import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launch


class FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeProcess:
    def __init__(self, pid=2468, handle=8642):
        self.pid = pid
        self._handle = handle


class FakeInspector:
    def __init__(self, matches=True, window_handle=0, alive=None):
        self.matches = matches
        self.window_handle = window_handle
        self.alive = alive

    def process_matches(self, pid, executable):
        return self.matches

    def process_handle_is_alive(self, process):
        if isinstance(self.alive, list):
            return self.alive.pop(0)
        return True if self.alive is None else self.alive

    def window_for_pid(self, pid):
        return self.window_handle

    def open_process(self, pid):
        return 97531

    def handle_is_alive(self, handle):
        return True

    def image_matches_handle(self, handle, executable):
        return True

    def close_handle(self, handle):
        return None


class LaunchTests(unittest.TestCase):
    def test_repo_root_ignores_caller_cwd(self):
        with mock.patch("launch.os.getcwd", return_value="C:/caller"):
            self.assertEqual(launch.repo_root(), Path(launch.__file__).resolve().parent)

    def test_parse_arguments_accepts_seconds_and_u64_boundaries(self):
        self.assertEqual(launch.parse_arguments(["--seconds", "3"]).seconds, 3)
        self.assertEqual(launch.parse_arguments(["--seconds", "0"]).seconds, 0)
        self.assertEqual(
            launch.parse_arguments(["--seconds", str(launch.U64_MAX)]).seconds,
            launch.U64_MAX,
        )

    def test_parse_arguments_rejects_invalid_seconds_before_start(self):
        for value in ("-1", "+1", "1.0", " 1", str(launch.U64_MAX + 1)):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                launch.parse_arguments(["--seconds", value])

    def test_parse_arguments_rejects_unknown_argument(self):
        with self.assertRaises(SystemExit) as raised:
            launch.parse_arguments(["--unknown"])
        self.assertEqual(raised.exception.code, 2)

    def test_build_command_uses_stable_target_and_locked_offline_build(self):
        repo = Path("D:/Apps/stay-up")
        cargo = Path("C:/Users/Test/AppData/Local/Programs/Rust/cargo/bin/cargo.exe")
        target = Path("C:/Users/Test/AppData/Local/Rust/target/stay-up")
        self.assertEqual(
            launch.build_command(cargo, repo, target),
            [str(cargo), "build", "--offline", "--locked", "--manifest-path",
             str(repo / "Cargo.toml"), "--target-dir", str(target),
             "--bin", "stay-watch"],
        )

    def test_environment_errors_report_stale_settings(self):
        localappdata = Path("C:/Users/Test/AppData/Local")
        values = {"CARGO_HOME": str(localappdata / "old"),
                  "RUSTUP_HOME": str(localappdata / "Programs" / "Rust" / "rustup"),
                  "CARGO_TARGET_DIR": str(localappdata / "Rust" / "target")}
        errors = launch.environment_errors(localappdata, values, is_windows=True)
        self.assertTrue(any("CARGO_HOME" in error for error in errors))

    def test_unsupported_compiler_overrides_are_rejected(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local"))
        values = {"RUSTC": "C:/other/rustc.exe", "RUSTC_WRAPPER": "C:/other/wrapper.exe",
                  "RUSTC_WORKSPACE_WRAPPER": "wrapper.exe", "RUSTUP_TOOLCHAIN": "nightly"}
        self.assertEqual(len(launch.compiler_override_errors(paths, values)), 4)

    def test_missing_source_is_reported(self):
        self.assertTrue(any("Cargo.toml" in error for error in launch.source_errors(Path("C:/missing"))))

    def test_validate_setup_rejects_an_unsupported_active_toolchain(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local"))
        values = {
            "LOCALAPPDATA": str(paths.localappdata),
            "CARGO_HOME": str(paths.cargo_home),
            "RUSTUP_HOME": str(paths.rustup_home),
            "CARGO_TARGET_DIR": str(paths.cargo_target_root),
        }
        with (
            mock.patch.dict(launch.os.environ, values, clear=True),
            mock.patch.object(launch, "source_errors", return_value=[]),
            mock.patch.object(launch, "active_command_errors", return_value=[]),
            mock.patch.object(launch.Path, "is_dir", return_value=True),
            mock.patch.object(launch.Path, "is_file", return_value=True),
            mock.patch.object(launch.subprocess, "run", side_effect=[
                FakeCompleted(stdout="cargo 1.98.1"),
                FakeCompleted(stdout="nightly-x86_64-pc-windows-gnu (default)"),
            ]),
            self.assertRaisesRegex(launch.LaunchError, "active toolchain"),
        ):
            launch.validate_setup(Path("D:/Apps/stay-up"))

    def test_denied_build_has_command_status_and_permission_explanation(self):
        with self.assertRaises(launch.LaunchError) as raised:
            launch.build_app(["cargo.exe", "build", "--offline"], Path("D:/Apps/stay-up"),
                             runner=lambda *args, **kwargs: FakeCompleted(5, stderr="Access is denied. (os error 5)"))
        message = str(raised.exception)
        self.assertIn("cargo.exe build --offline", message)
        self.assertIn("exit status 5", message)
        self.assertIn("could not write", message)

    def _main_patches(self, paths, lock):
        return (mock.patch.object(launch, "repo_root", return_value=Path("D:/Apps/stay-up")),
                mock.patch.object(launch, "validate_setup", return_value=paths),
                mock.patch.object(launch, "ProcessInspector", return_value=FakeInspector()),
                mock.patch.object(launch, "LaunchLock", return_value=lock))

    def test_main_reports_failed_build_without_start(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local")); lock = mock.MagicMock(); lock.__enter__.return_value = lock
        with self._main_patches(paths, lock)[0], self._main_patches(paths, lock)[1], self._main_patches(paths, lock)[2], self._main_patches(paths, lock)[3], mock.patch.object(launch, "find_existing_instance", return_value=None), mock.patch.object(launch, "build_app", side_effect=launch.LaunchError("build failed")), mock.patch.object(launch, "spawn_app") as start, mock.patch.object(launch, "emit") as emit:
            self.assertEqual(launch.main([]), 1)
        self.assertEqual(emit.call_args.args[0]["status"], "failed"); start.assert_not_called()

    def test_main_reports_missing_output_without_start(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local")); lock = mock.MagicMock(); lock.__enter__.return_value = lock
        with self._main_patches(paths, lock)[0], self._main_patches(paths, lock)[1], self._main_patches(paths, lock)[2], self._main_patches(paths, lock)[3], mock.patch.object(launch, "find_existing_instance", return_value=None), mock.patch.object(launch, "build_app"), mock.patch.object(launch.Path, "is_file", return_value=False), mock.patch.object(launch, "spawn_app") as start, mock.patch.object(launch, "emit") as emit:
            self.assertEqual(launch.main([]), 1)
        self.assertIn("executable is missing", emit.call_args.args[0]["error"]); start.assert_not_called()

    def test_main_reports_process_start_failure(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local")); lock = mock.MagicMock(); lock.__enter__.return_value = lock
        with self._main_patches(paths, lock)[0], self._main_patches(paths, lock)[1], self._main_patches(paths, lock)[2], self._main_patches(paths, lock)[3], mock.patch.object(launch, "find_existing_instance", return_value=None), mock.patch.object(launch, "build_app"), mock.patch.object(launch.Path, "is_file", return_value=True), mock.patch.object(launch, "spawn_app", side_effect=OSError("access denied")), mock.patch.object(launch, "emit") as emit:
            self.assertEqual(launch.main([]), 1)
        self.assertEqual(emit.call_args.args[0]["status"], "failed")
        self.assertIn("access denied", emit.call_args.args[0]["error"])

    def test_main_reports_process_inspector_setup_failure(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local"))
        with (
            mock.patch.object(launch, "validate_setup", return_value=paths),
            mock.patch.object(launch, "ProcessInspector", side_effect=OSError("DLL setup failed")),
            mock.patch.object(launch, "spawn_app") as start,
            mock.patch.object(launch, "emit") as emit,
        ):
            self.assertEqual(launch.main([]), 1)
        self.assertEqual(emit.call_args.args[0]["status"], "failed")
        start.assert_not_called()

    def test_other_checkout_is_rejected_before_commands(self):
        with mock.patch.object(launch.subprocess, "run") as run:
            with self.assertRaisesRegex(launch.LaunchError, "not the supported checkout"):
                launch.validate_setup(Path("D:/Apps/other-stay-up"))
        run.assert_not_called()

    def test_existing_instance_rejects_exit_during_window_check(self):
        inspector = mock.Mock(spec=launch.ProcessInspector)
        inspector.matching_pids.return_value = [2468]
        inspector.open_process.return_value = 97531
        inspector.handle_is_alive.side_effect = [True, False]
        inspector.image_matches_handle.return_value = True
        inspector.window_for_pid.return_value = 1357
        self.assertIsNone(launch.find_existing_instance(Path("D:/stay-watch.exe"), inspector))
        inspector.close_handle.assert_called_once_with(97531)

    def test_main_reports_duplicate_instance_without_build_or_start(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local")); lock = mock.MagicMock(); lock.__enter__.return_value = lock
        with self._main_patches(paths, lock)[0], self._main_patches(paths, lock)[1], self._main_patches(paths, lock)[2], self._main_patches(paths, lock)[3], mock.patch.object(launch, "find_existing_instance", return_value=launch.Instance(2468, 1357)), mock.patch.object(launch, "build_app") as build, mock.patch.object(launch, "spawn_app") as start, mock.patch.object(launch, "emit") as emit:
            self.assertEqual(launch.main([]), 0)
        value = emit.call_args.args[0]; self.assertEqual(value["status"], "already_running"); self.assertEqual(value["pid"], 2468); build.assert_not_called(); start.assert_not_called()

    def test_main_retains_pid_when_startup_check_fails(self):
        paths = launch.expected_paths(Path("C:/Users/Test/AppData/Local")); process = FakeProcess(); lock = mock.MagicMock(); lock.__enter__.return_value = lock
        with self._main_patches(paths, lock)[0], self._main_patches(paths, lock)[1], self._main_patches(paths, lock)[2], self._main_patches(paths, lock)[3], mock.patch.object(launch, "find_existing_instance", return_value=None), mock.patch.object(launch, "build_app"), mock.patch.object(launch.Path, "is_file", return_value=True), mock.patch.object(launch, "spawn_app", return_value=process), mock.patch.object(launch, "wait_for_startup", side_effect=OSError("window check failed")), mock.patch.object(launch, "emit") as emit:
            self.assertEqual(launch.main([]), 1)
        value = emit.call_args.args[0]; self.assertEqual(value["status"], "startup_failed"); self.assertEqual(value["pid"], 2468)

    def test_startup_timeout_reports_pid(self):
        clock = iter([0.0, 2.0, 4.0])
        startup = launch.wait_for_startup(FakeProcess(), Path("D:/stay-watch.exe"), FakeInspector(matches=True), timeout=3.0, monotonic=lambda: next(clock), sleeper=lambda seconds: None)
        self.assertEqual(startup.status, "startup_timeout"); self.assertEqual(startup.pid, 2468)

    def test_startup_requires_owned_status_window(self):
        startup = launch.wait_for_startup(FakeProcess(), Path("D:/stay-watch.exe"), FakeInspector(matches=True, window_handle=9753), timeout=3.0, monotonic=lambda: 0.0, sleeper=lambda seconds: None)
        self.assertEqual(startup.status, "started"); self.assertEqual(startup.window_handle, 9753)

    def test_startup_rejects_replacement_process_after_window_check(self):
        startup = launch.wait_for_startup(FakeProcess(), Path("D:/stay-watch.exe"), FakeInspector(matches=True, window_handle=9753, alive=[True, False]), timeout=3.0, monotonic=lambda: 0.0, sleeper=lambda seconds: None)
        self.assertEqual(startup.status, "startup_failed"); self.assertEqual(startup.pid, 2468)

    def test_spawn_detaches_standard_handles_and_preserves_gui_process(self):
        calls = {}
        def fake_popen(*args, **kwargs):
            calls["kwargs"] = kwargs; return FakeProcess()
        with mock.patch.object(launch.subprocess, "Popen", side_effect=fake_popen):
            process = launch.spawn_app(Path("D:/stay-watch.exe"), Path("D:/Apps/stay-up"), ["--seconds", "3"])
        self.assertEqual(process.pid, 2468); self.assertEqual(calls["kwargs"]["stdin"], subprocess.DEVNULL); self.assertTrue(calls["kwargs"]["close_fds"]); self.assertTrue(calls["kwargs"]["creationflags"] & launch.DETACHED_PROCESS); self.assertFalse(calls["kwargs"]["creationflags"] & launch.CREATE_NO_WINDOW)

    def test_result_is_machine_readable(self):
        self.assertEqual(json.loads(json.dumps(launch.result("started", 2468, Path("D:/stay-watch.exe"), 9753)))["status"], "started")


@unittest.skipUnless(sys.platform == "win32", "The mutex is a Windows boundary.")
class LaunchLockTests(unittest.TestCase):
    def test_second_lock_waits_and_times_out(self):
        outcome = []; ready = threading.Event()
        def acquire_in_other_thread():
            try:
                with launch.LaunchLock(Path("D:/Apps/stay-up"), timeout_ms=20): outcome.append("acquired")
            except launch.LockTimeoutError: outcome.append("timed_out")
            finally: ready.set()
        with launch.LaunchLock(Path("D:/Apps/stay-up"), timeout_ms=20):
            worker = threading.Thread(target=acquire_in_other_thread); worker.start(); self.assertTrue(ready.wait(1)); worker.join()
        self.assertEqual(outcome, ["timed_out"])


if __name__ == "__main__":
    unittest.main()
