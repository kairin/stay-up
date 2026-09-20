"""Explicit capture feasibility test for a dedicated Windows Terminal window.

This probe does not capture another foreground application automatically.
It does not simulate input. It does not change power or lock settings.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
import uuid
from ctypes import wintypes


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020
SM_CXSCREEN = 0
SM_CYSCREEN = 1
SW_MINIMIZE = 6
DIB_RGB_COLORS = 0
BI_RGB = 0

COLOR_A = (196, 23, 46)
COLOR_B = (12, 140, 88)
MATCH_TOLERANCE = 30
ACCEPT_PIXELS = 400
REJECT_PIXELS = 50


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.GetWindowDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.BitBlt.argtypes = [
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.DWORD,
]
gdi32.BitBlt.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.GetDIBits.argtypes = [
    wintypes.HDC,
    wintypes.HBITMAP,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(BITMAPINFO),
    wintypes.UINT,
]
gdi32.GetDIBits.restype = ctypes.c_int
kernel32.GetConsoleWindow.argtypes = []
kernel32.GetConsoleWindow.restype = wintypes.HWND
kernel32.SetConsoleTitleW.argtypes = [wintypes.LPCWSTR]
kernel32.SetConsoleTitleW.restype = wintypes.BOOL


def handle_int(value):
    return int(getattr(value, "value", value) or 0)


def write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_text(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read().strip()
    except FileNotFoundError:
        return ""


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def fill_color(rgb):
    try:
        size = os.get_terminal_size()
        cols, rows = size.columns, size.lines
    except OSError:
        cols, rows = 80, 24
    line = "\x1b[48;2;{};{};{}m".format(*rgb) + (" " * max(1, cols)) + "\x1b[0m"
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.write("\n".join([line] * max(1, rows)))
    sys.stdout.write("\nSTAYUP_CAPTURE_MARKER rgb={}x{}\n".format(rgb, (cols, rows)))
    sys.stdout.flush()


def scroll_away():
    sys.stdout.write("\x1b[0m\x1b[2J\x1b[H")
    for index in range(120):
        sys.stdout.write("stay-up scroll-away line {:03d}\n".format(index))
    sys.stdout.flush()


def child_loop(args):
    kernel32.SetConsoleTitleW(args.title)
    command_path = os.path.join(args.control_dir, "command.txt")
    state_path = os.path.join(args.control_dir, "child_state.json")
    write_json(state_path, {"ready": True, "pid": os.getpid(), "stage": "waiting"})
    last_command = ""
    while True:
        command = read_text(command_path)
        if command and command != last_command:
            last_command = command
            if command == "draw_a":
                fill_color(COLOR_A)
                write_json(state_path, {"ready": True, "pid": os.getpid(), "stage": "draw_a"})
            elif command == "draw_b":
                fill_color(COLOR_B)
                write_json(state_path, {"ready": True, "pid": os.getpid(), "stage": "draw_b"})
            elif command == "scroll_away":
                scroll_away()
                write_json(state_path, {"ready": True, "pid": os.getpid(), "stage": "scroll_away"})
            elif command == "exit":
                write_json(state_path, {"ready": True, "pid": os.getpid(), "stage": "exit"})
                return
        time.sleep(0.1)


def find_window_by_title(title):
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _lparam):
        length = 512
        buf = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buf, length)
        text = buf.value
        if title in text:
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            found.append({
                "hwnd": handle_int(hwnd),
                "title": text,
                "visible": bool(user32.IsWindowVisible(hwnd)),
                "minimized": bool(user32.IsIconic(hwnd)),
                "rect": {
                    "left": int(rect.left),
                    "top": int(rect.top),
                    "right": int(rect.right),
                    "bottom": int(rect.bottom),
                },
            })
        return True

    user32.EnumWindows(visit, 0)
    return found


def wait_for_window(title, timeout_s):
    deadline = time.monotonic() + timeout_s
    last = []
    while time.monotonic() < deadline:
        last = find_window_by_title(title)
        visible = [item for item in last if item["visible"] and not item["minimized"]]
        if visible:
            return visible[0], last
        time.sleep(0.2)
    return None, last


def bitmap_to_png(pixels, width, height, path):
    try:
        from PIL import Image
    except ImportError:
        with open(path.replace(".png", ".raw.json"), "w", encoding="utf-8") as handle:
            json.dump({"width": width, "height": height, "bytes": len(pixels)}, handle)
        return False, "pil_missing"
    image = Image.frombytes("RGB", (width, height), pixels, "raw", "BGR", 0, 1)
    image.save(path)
    return True, "ok"


def count_color(pixels, width, height, rgb, tolerance):
    matched = 0
    # pixels are BGR, bottom-up rows already flipped by PIL path; here raw BGR top-down after copy
    step = 3
    length = min(len(pixels), width * height * step)
    r_t, g_t, b_t = rgb
    for index in range(0, length, step):
        blue = pixels[index]
        green = pixels[index + 1]
        red = pixels[index + 2]
        if abs(red - r_t) <= tolerance and abs(green - g_t) <= tolerance and abs(blue - b_t) <= tolerance:
            matched += 1
    return matched


def capture_window(hwnd, method):
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return {"ok": False, "error": "GetWindowRect failed", "last_error": ctypes.get_last_error()}
    width = int(rect.right - rect.left)
    height = int(rect.bottom - rect.top)
    if width <= 0 or height <= 0:
        return {"ok": False, "error": "empty_rect", "rect": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}}

    screen_dc = user32.GetDC(None)
    if not screen_dc:
        return {"ok": False, "error": "GetDC failed", "last_error": ctypes.get_last_error()}
    mem_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bitmap)
    ok = False
    last_error = 0
    try:
        if method == "printwindow":
            ok = bool(user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT))
            last_error = ctypes.get_last_error()
        elif method == "screen_region":
            ok = bool(gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, rect.left, rect.top, SRCCOPY))
            last_error = ctypes.get_last_error()
        else:
            return {"ok": False, "error": "unknown_method"}
        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 24
        info.bmiHeader.biCompression = BI_RGB
        stride = (width * 3 + 3) & ~3
        buf = ctypes.create_string_buffer(stride * height)
        copied = gdi32.GetDIBits(mem_dc, bitmap, 0, height, buf, ctypes.byref(info), DIB_RGB_COLORS)
        if copied == 0:
            return {
                "ok": False,
                "error": "GetDIBits failed",
                "method": method,
                "print_or_blt_ok": ok,
                "last_error": ctypes.get_last_error(),
            }
        packed = bytearray()
        for row in range(height):
            start = row * stride
            packed.extend(buf.raw[start:start + width * 3])
        return {
            "ok": True,
            "method": method,
            "print_or_blt_ok": ok,
            "last_error": last_error,
            "width": width,
            "height": height,
            "rect": {"left": int(rect.left), "top": int(rect.top), "right": int(rect.right), "bottom": int(rect.bottom)},
            "pixels": bytes(packed),
        }
    finally:
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, screen_dc)


def analyze(capture, expected_rgb):
    if not capture.get("ok"):
        return {
            "valid_observer_evidence": False,
            "reason": capture.get("error", "capture_failed"),
            "expected_rgb": expected_rgb,
        }
    pixels = capture["pixels"]
    width = capture["width"]
    height = capture["height"]
    matched = count_color(pixels, width, height, expected_rgb, MATCH_TOLERANCE) if expected_rgb else 0
    other = None
    if expected_rgb == COLOR_A:
        other = count_color(pixels, width, height, COLOR_B, MATCH_TOLERANCE)
    elif expected_rgb == COLOR_B:
        other = count_color(pixels, width, height, COLOR_A, MATCH_TOLERANCE)
    black = count_color(pixels, width, height, (0, 0, 0), 8)
    total = width * height
    valid = bool(expected_rgb) and matched >= ACCEPT_PIXELS
    reason = "verified_marker" if valid else "marker_not_established"
    if black > total * 0.98:
        reason = "image_nearly_black"
        valid = False
    return {
        "valid_observer_evidence": valid,
        "reason": reason,
        "expected_rgb": expected_rgb,
        "matched_pixels": matched,
        "other_marker_pixels": other,
        "black_pixels": black,
        "total_pixels": total,
        "accept_threshold": ACCEPT_PIXELS,
    }


def save_capture(capture, analysis, path):
    record = {k: v for k, v in capture.items() if k != "pixels"}
    record["analysis"] = analysis
    record["path"] = path
    saved = False
    save_status = "skipped"
    if capture.get("ok"):
        saved, save_status = bitmap_to_png(capture["pixels"], capture["width"], capture["height"], path)
    record["file_write_ok"] = saved
    record["file_write_status"] = save_status
    return record


def launch_child(title, control_dir):
    script = os.path.abspath(__file__)
    python_exe = sys.executable
    env = os.environ.copy()
    child_args = [
        "--window",
        "new",
        "--title",
        title,
        python_exe,
        "-B",
        script,
        "--role",
        "child",
        "--title",
        title,
        "--control-dir",
        control_dir,
    ]
    commands = [
        ["wt.exe"] + child_args,
        [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "wt.exe")] + child_args,
    ]
    errors = []
    for command in commands:
        try:
            process = subprocess.Popen(command, env=env)
            return {"ok": True, "pid": process.pid, "command": command, "method": command[0], "errors": errors}
        except OSError as exc:
            errors.append({"method": command[0], "error": str(exc)})
    quoted = subprocess.list2cmdline(child_args)
    ps_command = [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        "Start-Process -FilePath 'wt.exe' -ArgumentList {}".format(json.dumps(quoted)),
    ]
    try:
        process = subprocess.Popen(ps_command, env=env)
        return {"ok": True, "pid": process.pid, "command": ps_command, "method": "Start-Process", "errors": errors}
    except OSError as exc:
        errors.append({"method": "Start-Process", "error": str(exc)})
        return {"ok": False, "errors": errors}


def wait_child_stage(control_dir, stage, timeout_s):
    path = os.path.join(control_dir, "child_state.json")
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            if data.get("stage") == stage:
                return data
        except (OSError, json.JSONDecodeError):
            pass
        time.sleep(0.1)
    return None


def run_parent(args):
    token = uuid.uuid4().hex[:8]
    title = "STAYUP-CAP-" + token
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = args.output_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "local",
        "stay-watch",
        "feasibility-" + stamp,
    )
    control_dir = os.path.join(out_dir, "control")
    os.makedirs(control_dir, exist_ok=True)
    write_text(os.path.join(control_dir, "command.txt"), "waiting")
    launch = launch_child(title, control_dir)
    context_hwnd = handle_int(kernel32.GetConsoleWindow())
    window, enumerated = wait_for_window(title, 20)
    ready = wait_child_stage(control_dir, "waiting", 20)
    stages = []

    def run_stage(name, command, expected_rgb, extra=None):
        if command:
            write_text(os.path.join(control_dir, "command.txt"), command)
            if command != "exit":
                wait_child_stage(control_dir, command, 8)
                time.sleep(0.4)
        current, _all_windows = wait_for_window(title, 5)
        target = current or window
        stage_record = {
            "name": name,
            "command": command,
            "window": target,
            "foreground_hwnd": handle_int(user32.GetForegroundWindow()),
            "extra": extra or {},
        }
        if target is None:
            stage_record["captures"] = []
            stage_record["error"] = "window_not_found"
            stages.append(stage_record)
            return stage_record
        hwnd = wintypes.HWND(target["hwnd"])
        captures = []
        for method in ("printwindow", "screen_region"):
            captured = capture_window(hwnd, method)
            analysis = analyze(captured, expected_rgb)
            filename = "{}-{}.png".format(name, method)
            path = os.path.join(out_dir, filename)
            saved = save_capture(captured, analysis, path)
            captures.append(saved)
        stage_record["captures"] = captures
        stages.append(stage_record)
        return stage_record

    initial = run_stage("01-initial-no-marker", None, COLOR_A)
    drawn_a = run_stage("02-draw-a", "draw_a", COLOR_A)
    drawn_b = run_stage("03-draw-b", "draw_b", COLOR_B)
    scrolled = run_stage("04-scroll-away", "scroll_away", COLOR_B)
    minimized_extra = {}
    if window:
        minimized_extra["showwindow"] = bool(user32.ShowWindow(wintypes.HWND(window["hwnd"]), SW_MINIMIZE))
        time.sleep(0.4)
    minimized = run_stage("05-minimized", None, COLOR_B, extra=minimized_extra)
    write_text(os.path.join(control_dir, "command.txt"), "exit")

    def verdict(stage_name, predicate, status_if_true, status_if_false):
        stage = next((item for item in stages if item["name"] == stage_name), None)
        if stage is None:
            return "unknown"
        return status_if_true if predicate(stage) else status_if_false

    def any_valid(stage):
        return any(item.get("analysis", {}).get("valid_observer_evidence") for item in stage.get("captures", []))

    def none_valid(stage):
        captures = stage.get("captures", [])
        return bool(captures) and not any_valid(stage)

    def method_valid(stage, method):
        for item in stage.get("captures", []):
            if item.get("method") == method and item.get("analysis", {}).get("valid_observer_evidence"):
                return True
        return False

    report = {
        "probe": "capture-feasibility-probe",
        "title": title,
        "output_dir": out_dir,
        "context_console_hwnd": context_hwnd,
        "launch": {k: v for k, v in launch.items() if k != "command"} | {"command": launch.get("command")},
        "ready_child": ready,
        "enumerated_on_wait": enumerated,
        "stages": stages,
        "results": {
            "terminal_target_discovery": "pass" if window else "fail",
            "getconsolewindow_nonzero": context_hwnd != 0,
            "initial_image_rejection": verdict("01-initial-no-marker", none_valid, "pass", "fail" if initial.get("captures") else "unknown"),
            "observer_visibility_draw_a": verdict("02-draw-a", any_valid, "pass", "fail" if drawn_a.get("captures") else "unknown"),
            "freshness_draw_b": "unknown",
            "scrollback_unverified": verdict("04-scroll-away", none_valid, "pass", "fail" if scrolled.get("captures") else "unknown"),
            "minimization_unverified": verdict("05-minimized", none_valid, "pass", "fail" if minimized.get("captures") else "unknown"),
            "printwindow_backend": "pass" if method_valid(drawn_a, "printwindow") or method_valid(drawn_b, "printwindow") else "fail",
            "screen_region_backend": "pass" if method_valid(drawn_a, "screen_region") or method_valid(drawn_b, "screen_region") else "fail",
            "windows_graphics_capture": "unknown",
            "tab_change": "unknown",
        },
        "limits": [
            "Windows Graphics Capture was not invoked; no WinRT binding was available in this probe.",
            "Tab change was not invoked. The probe does not switch Windows Terminal tabs.",
            "GetConsoleWindow was not used as the capture target.",
            "No other foreground application was selected automatically.",
        ],
    }
    if drawn_b.get("captures") and any_valid(drawn_b):
        b_ok = True
        leaked_a = False
        for item in drawn_b.get("captures", []):
            other = item.get("analysis", {}).get("other_marker_pixels") or 0
            matched = item.get("analysis", {}).get("matched_pixels") or 0
            if other >= ACCEPT_PIXELS and other > matched:
                leaked_a = True
        report["results"]["freshness_draw_b"] = "fail" if leaked_a or not b_ok else "pass"

    report_path = os.path.join(out_dir, "capture-report.json")
    # Drop bulky nested pixels if any remain
    write_json(report_path, report)
    print(json.dumps({"report_path": report_path, "results": report["results"], "title": title}, indent=2, sort_keys=True))
    return 0 if window else 2


def run_tab_away(args):
    token = uuid.uuid4().hex[:8]
    title = "STAYUP-TAB-" + token
    other = "STAYUP-OTHER-" + token
    out_dir = args.output_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "local",
        "stay-watch",
        "feasibility-tab-" + token,
    )
    control_dir = os.path.join(out_dir, "control")
    os.makedirs(control_dir, exist_ok=True)
    write_text(os.path.join(control_dir, "command.txt"), "draw_a")
    script = os.path.abspath(__file__)
    python_exe = sys.executable
    command = [
        "wt.exe",
        "--window",
        "new",
        "new-tab",
        "--title",
        title,
        python_exe,
        "-B",
        script,
        "--role",
        "child",
        "--title",
        title,
        "--control-dir",
        control_dir,
        ";",
        "new-tab",
        "--title",
        other,
        "cmd.exe",
        "/d",
        "/c",
        "echo STAYUP-OTHER-TAB && ping -n 25 127.0.0.1 >NUL",
    ]
    launched = subprocess.Popen(command)
    time.sleep(2.5)
    wait_child_stage(control_dir, "draw_a", 12)
    marker_window, marker_enum = wait_for_window(title, 8)
    other_window, other_enum = wait_for_window(other, 8)
    target = other_window or marker_window
    captures = []
    if target:
        hwnd = wintypes.HWND(target["hwnd"])
        for method in ("printwindow", "screen_region"):
            captured = capture_window(hwnd, method)
            analysis = analyze(captured, COLOR_A)
            path = os.path.join(out_dir, "tab-away-{}.png".format(method))
            captures.append(save_capture(captured, analysis, path))
    write_text(os.path.join(control_dir, "command.txt"), "exit")
    if target:
        user32.PostMessageW(wintypes.HWND(target["hwnd"]), 0x0010, 0, 0)
    marker_visible = any(item.get("analysis", {}).get("valid_observer_evidence") for item in captures)
    result = "unknown"
    if captures and other_window and not marker_visible:
        result = "pass"
    elif captures and marker_visible:
        result = "fail"
    report = {
        "probe": "capture-tab-away",
        "launch_pid": launched.pid,
        "command": command,
        "marker_window": marker_window,
        "other_window": other_window,
        "marker_enum": marker_enum,
        "other_enum": other_enum,
        "captures": captures,
        "tab_change": result,
        "limits": [
            "The probe used Windows Terminal command-line tab creation, not simulated input.",
            "A pass means the visible other tab did not contain the observer marker.",
        ],
    }
    path = os.path.join(out_dir, "tab-away-report.json")
    write_json(path, report)
    print(json.dumps({"report_path": path, "tab_change": result, "other_window": other_window, "marker_visible": marker_visible}, indent=2, sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=["parent", "child"], default="parent")
    parser.add_argument("--title")
    parser.add_argument("--control-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--tab-away", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This probe requires Windows")
    if args.role == "child":
        if not args.title or not args.control_dir:
            parser.error("child role requires --title and --control-dir")
        child_loop(args)
        return 0
    if args.tab_away:
        return run_tab_away(args)
    return run_parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
