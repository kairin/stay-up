"""Verify feasibility probes from recorded evidence and silent commands.

These tests do not open Windows Terminal. They do not simulate input.
They do not change power or lock settings.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "local" / "stay-watch" / "feasibility-20260920-1345"
CAPTURE = Path(__file__).with_name("capture-feasibility-probe.py")
STATE = Path(__file__).with_name("windows-state-probe.py")
LOCALAPPDATA = Path(
    os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
)
RUST_EXE = LOCALAPPDATA / "Rust" / "target" / "feasibility-20260920-1336" / "rust-state-probe.exe"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count_rgb(path, rgb, tolerance):
    from PIL import Image

    image = Image.open(path).convert("RGB")
    matched = 0
    for pixel in image.getdata():
        if all(abs(pixel[index] - rgb[index]) <= tolerance for index in range(3)):
            matched += 1
    return matched, image.size[0] * image.size[1]


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.capture = load_module(CAPTURE, "capture_feasibility_probe")

    def test_synthetic_marker_is_accepted(self):
        width = 20
        height = 20
        red, green, blue = self.capture.COLOR_A
        pixels = bytes([blue, green, red] * (width * height))
        capture = {
            "ok": True,
            "pixels": pixels,
            "width": width,
            "height": height,
        }
        result = self.capture.analyze(capture, self.capture.COLOR_A)
        self.assertTrue(result["valid_observer_evidence"])
        self.assertEqual(result["reason"], "verified_marker")

    def test_synthetic_empty_marker_is_rejected(self):
        width = 20
        height = 20
        pixels = bytes([0, 0, 0] * (width * height))
        capture = {
            "ok": True,
            "pixels": pixels,
            "width": width,
            "height": height,
        }
        result = self.capture.analyze(capture, self.capture.COLOR_A)
        self.assertFalse(result["valid_observer_evidence"])


class EvidenceImageTests(unittest.TestCase):
    def setUp(self):
        self.capture = load_module(CAPTURE, "capture_feasibility_probe")
        self.assertTrue(EVIDENCE.is_dir(), "Evidence directory is missing: %s" % EVIDENCE)

    def _count(self, name, rgb):
        path = EVIDENCE / name
        self.assertTrue(path.is_file(), "Missing image: %s" % path)
        return count_rgb(path, rgb, self.capture.MATCH_TOLERANCE)

    def test_initial_image_has_no_marker(self):
        matched, total = self._count("01-initial-no-marker-printwindow.png", self.capture.COLOR_A)
        self.assertLess(matched, self.capture.REJECT_PIXELS)
        self.assertGreater(total, 1000)

    def test_draw_a_has_red_marker(self):
        matched, _total = self._count("02-draw-a-printwindow.png", self.capture.COLOR_A)
        other, _ignore = self._count("02-draw-a-printwindow.png", self.capture.COLOR_B)
        self.assertGreaterEqual(matched, self.capture.ACCEPT_PIXELS)
        self.assertLess(other, self.capture.ACCEPT_PIXELS)

    def test_draw_b_has_green_marker(self):
        matched, _total = self._count("03-draw-b-printwindow.png", self.capture.COLOR_B)
        other, _ignore = self._count("03-draw-b-printwindow.png", self.capture.COLOR_A)
        self.assertGreaterEqual(matched, self.capture.ACCEPT_PIXELS)
        self.assertLess(other, matched)

    def test_scroll_away_has_no_marker(self):
        red, _total = self._count("04-scroll-away-printwindow.png", self.capture.COLOR_A)
        green, _ignore = self._count("04-scroll-away-printwindow.png", self.capture.COLOR_B)
        self.assertLess(red, self.capture.ACCEPT_PIXELS)
        self.assertLess(green, self.capture.ACCEPT_PIXELS)

    def test_minimized_image_is_not_valid_observer_evidence(self):
        red, total = self._count("05-minimized-printwindow.png", self.capture.COLOR_A)
        green, _ignore = self._count("05-minimized-printwindow.png", self.capture.COLOR_B)
        self.assertLess(red, self.capture.ACCEPT_PIXELS)
        self.assertLess(green, self.capture.ACCEPT_PIXELS)
        self.assertLess(total, 20000)

    def test_tab_away_has_no_red_marker(self):
        matched, total = self._count("tab-away-printwindow.png", self.capture.COLOR_A)
        self.assertLess(matched, self.capture.REJECT_PIXELS)
        self.assertGreater(total, 1000)


class ReportTests(unittest.TestCase):
    def test_capture_report_pass_marks(self):
        path = EVIDENCE / "capture-report.json"
        self.assertTrue(path.is_file(), "Missing capture-report.json")
        report = json.loads(path.read_text(encoding="utf-8"))
        results = report["results"]
        for key in (
            "printwindow_backend",
            "screen_region_backend",
            "initial_image_rejection",
            "observer_visibility_draw_a",
            "freshness_draw_b",
            "scrollback_unverified",
            "minimization_unverified",
            "terminal_target_discovery",
        ):
            self.assertEqual(results[key], "pass", key)

    def test_tab_away_report_pass_mark(self):
        path = EVIDENCE / "tab-away-report.json"
        self.assertTrue(path.is_file(), "Missing tab-away-report.json")
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["tab_change"], "pass")
        self.assertFalse(any(
            item.get("analysis", {}).get("valid_observer_evidence")
            for item in report.get("captures", [])
        ))

    def test_windows_state_registrations_and_devices(self):
        path = EVIDENCE / "windows-state.json"
        self.assertTrue(path.is_file(), "Missing windows-state.json")
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["power_before"]["ac_line"], "ac")
        self.assertTrue(report["powercfg"]["s0_low_power_idle"])
        labels = {item["label"]: item["ok"] for item in report["registrations"]["raw_input"]}
        self.assertTrue(labels["keyboard"])
        self.assertTrue(labels["mouse"])
        self.assertTrue(labels["touchpad"])
        counts = report["device_category_counts"]
        self.assertGreaterEqual(counts.get("keyboard", 0), 1)
        self.assertGreaterEqual(counts.get("mouse", 0), 1)
        self.assertGreaterEqual(counts.get("touchpad", 0), 1)


class SilentCommandTests(unittest.TestCase):
    def test_terminal_target_probe_enumerates(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools" / "terminal-target-probe.py")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["enumeration_succeeded"])
        self.assertTrue(any(item.get("eligible_candidate") for item in payload.get("candidates", [])))

    def test_rust_state_probe_prints_ok(self):
        self.assertTrue(RUST_EXE.is_file(), "Missing rust-state-probe.exe: %s" % RUST_EXE)
        completed = subprocess.run(
            [str(RUST_EXE)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("RUST_STATE_PROBE_OK", completed.stdout)
        self.assertIn("last_input_ok=1", completed.stdout)
        self.assertIn("power_ok=1", completed.stdout)
        self.assertIn("raw_ok=1", completed.stdout)

    def test_classify_touchpad_from_elan_name(self):
        state = load_module(STATE, "windows_state_probe")
        category = state.classify_device(
            r"\\?\HID#TOUCHPAD-TEST&Col01#TEST&0&0000",
            0,
            None,
            None,
        )
        self.assertEqual(category, "touchpad")


if __name__ == "__main__":
    unittest.main()
