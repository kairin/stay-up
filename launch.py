"""Build and start the stay-watch Rust application."""

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_HANDLE = 6
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_SYNCHRONIZE = 0x00100000
TH32CS_SNAPPROCESS = 0x00000002
STARTUP_TIMEOUT_SECONDS = 10.0
STARTUP_POLL_SECONDS = 0.1
LOCK_TIMEOUT_MS = 5000
U64_MAX = (1 << 64) - 1
SUPPORTED_CHECKOUT = Path("D:/Apps/stay-up")
SUPPORTED_TOOLCHAIN = "stable-x86_64-pc-windows-gnu"

REQUIRED_SOURCES = (
    Path("stay-watch") / "Cargo.toml",
    Path("stay-watch") / "src" / "lib.rs",
    Path("stay-watch") / "src" / "main.rs",
    Path("stay-watch") / "src" / "ui.rs",
    Path("keep-awake.py"),
    Path("monitor-helper.py"),
)


class LaunchError(RuntimeError):
    """A launch precondition or command failed."""


class LockTimeoutError(LaunchError):
    """Another launch owns the checkout lock."""


@dataclass(frozen=True)
class Paths:
    localappdata: Path
    cargo_home: Path
    rustup_home: Path
    cargo_target_root: Path
    stable_target: Path
    cargo: Path
    executable: Path
    rustc: Path
    rustup: Path


@dataclass(frozen=True)
class Instance:
    pid: int
    window_handle: int


@dataclass(frozen=True)
class StartupResult:
    status: str
    pid: int
    window_handle: int
    error: str = ""


def repo_root():
    """Return the directory that contains this file."""
    return Path(__file__).resolve().parent


def parse_arguments(argv=None):
    """Parse launcher arguments before any process starts."""
    parser = argparse.ArgumentParser(
        prog="python launch.py",
        description="Build and start the stay-watch Rust application.",
    )
    parser.add_argument(
        "--seconds",
        type=nonnegative_seconds,
        help="Stop the existing helper session after this many seconds.",
    )
    return parser.parse_args(argv)


def nonnegative_seconds(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise argparse.ArgumentTypeError("--seconds must contain decimal digits")
    seconds = int(value, 10)
    if seconds > U64_MAX:
        raise argparse.ArgumentTypeError("--seconds is outside the Rust u64 range")
    return seconds


def same_path(left, right):
    left_text = os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(left))))
    right_text = os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(right))))
    return left_text == right_text


def expected_paths(localappdata):
    localappdata = Path(localappdata)
    cargo_home = localappdata / "Programs" / "Rust" / "cargo"
    rustup_home = localappdata / "Programs" / "Rust" / "rustup"
    cargo_target_root = localappdata / "Rust" / "target"
    stable_target = cargo_target_root / "stay-up"
    cargo = cargo_home / "bin" / "cargo.exe"
    executable = stable_target / "debug" / "stay-watch.exe"
    rustc = cargo_home / "bin" / "rustc.exe"
    rustup = cargo_home / "bin" / "rustup.exe"
    return Paths(
        localappdata,
        cargo_home,
        rustup_home,
        cargo_target_root,
        stable_target,
        cargo,
        executable,
        rustc,
        rustup,
    )


def environment_errors(localappdata, values, is_windows=None):
    if is_windows is None:
        is_windows = sys.platform == "win32"
    errors = []
    if not is_windows:
        errors.append("This launcher requires Windows.")
    if not localappdata:
        return errors + ["LOCALAPPDATA is not set."]
    localappdata_path = Path(localappdata)
    if not localappdata_path.is_absolute():
        errors.append("LOCALAPPDATA must contain an absolute path.")
    paths = expected_paths(localappdata_path)
    for name, expected in (
        ("CARGO_HOME", paths.cargo_home),
        ("RUSTUP_HOME", paths.rustup_home),
        ("CARGO_TARGET_DIR", paths.cargo_target_root),
    ):
        actual = values.get(name)
        if not actual:
            errors.append(f"{name} is not set.")
        elif not same_path(actual, expected):
            errors.append(f"{name} does not match the documented path {expected}.")
    return errors


def path_is_under(path, root):
    path_text = os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(path))))
    root_text = os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(root))))
    return path_text == root_text or path_text.startswith(root_text + os.sep)


def compiler_override_errors(paths, values):
    errors = []
    rust_root = paths.localappdata / "Programs" / "Rust"
    for name in ("RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER"):
        value = values.get(name)
        if value and (
            not os.path.isabs(value)
            or not path_is_under(value, rust_root)
            or not Path(value).is_file()
        ):
            errors.append(f"{name} must name a file under {rust_root}.")
    rustc_override = values.get("RUSTC")
    if rustc_override and not same_path(rustc_override, paths.rustc):
        errors.append(f"RUSTC does not match the documented compiler path {paths.rustc}.")
    toolchain = values.get("RUSTUP_TOOLCHAIN")
    if toolchain and toolchain != SUPPORTED_TOOLCHAIN:
        errors.append(f"RUSTUP_TOOLCHAIN must be {SUPPORTED_TOOLCHAIN}.")
    return errors


def active_command_errors(paths, values):
    errors = []
    for name, expected in (
        ("cargo", paths.cargo),
        ("rustc", paths.rustc),
        ("rustup", paths.rustup),
    ):
        actual = shutil.which(name, path=values.get("PATH"))
        if not actual:
            errors.append(f"The active {name} command is not available in PATH.")
        elif not same_path(actual, expected):
            errors.append(f"The active {name} command does not match the documented path {expected}.")
    return errors


def source_errors(repo):
    errors = []
    for relative in REQUIRED_SOURCES:
        path = repo / relative
        if not path.is_file():
            errors.append(f"Required source file is missing: {path}")
    return errors


def build_command(cargo, repo, stable_target):
    return [
        str(cargo),
        "build",
        "--offline",
        "--locked",
        "--manifest-path",
        str(repo / "stay-watch" / "Cargo.toml"),
        "--target-dir",
        str(stable_target),
        "--bin",
        "stay-watch",
    ]


def validate_setup(repo):
    """Check the documented setup and the installed Cargo command."""
    if not same_path(repo, SUPPORTED_CHECKOUT):
        raise LaunchError(
            f"The checkout {Path(repo).resolve()} is not the supported checkout {SUPPORTED_CHECKOUT}."
        )
    localappdata = os.environ.get("LOCALAPPDATA")
    errors = source_errors(repo)
    errors.extend(environment_errors(localappdata, os.environ))
    if errors:
        raise LaunchError(" ".join(errors))
    paths = expected_paths(Path(localappdata))
    for label, path in (
        ("CARGO_HOME", paths.cargo_home),
        ("RUSTUP_HOME", paths.rustup_home),
        ("CARGO_TARGET_DIR", paths.cargo_target_root),
    ):
        if not path.is_dir():
            raise LaunchError(f"The documented {label} directory is missing: {path}")
    for label, path in (
        ("Cargo", paths.cargo),
        ("rustc", paths.rustc),
        ("rustup", paths.rustup),
    ):
        if not path.is_file():
            raise LaunchError(f"The documented {label} command is missing: {path}")
    errors = compiler_override_errors(paths, os.environ)
    errors.extend(active_command_errors(paths, os.environ))
    if errors:
        raise LaunchError(" ".join(errors))
    try:
        completed = subprocess.run(
            [str(paths.cargo), "--version"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise LaunchError(f"The documented Cargo command could not start: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise LaunchError(
            f"The documented Cargo command failed with exit status "
            f"{completed.returncode}: {detail}"
        )
    toolchain = subprocess.run(
        [str(paths.rustup), "show", "active-toolchain"],
        cwd=str(repo), capture_output=True, text=True, check=False,
    )
    selected = toolchain.stdout.split()
    if toolchain.returncode != 0 or not selected or selected[0] != SUPPORTED_TOOLCHAIN:
        raise LaunchError(
            f"The active toolchain must be {SUPPORTED_TOOLCHAIN}. "
            f"Rustup returned exit status {toolchain.returncode}: "
            f"{(toolchain.stderr or toolchain.stdout).strip()}"
        )
    return paths


def command_text(command):
    return subprocess.list2cmdline([str(item) for item in command])


def build_app(command, repo, runner=subprocess.run):
    try:
        completed = runner(
            command,
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise LaunchError(
            f"Cargo command {command_text(command)} could not start: {error}"
        ) from error
    if completed.returncode == 0:
        return completed
    output = (completed.stderr or completed.stdout or "").strip()
    lowered = output.lower()
    if "access is denied" in lowered or "permission denied" in lowered or "os error 5" in lowered:
        explanation = "Cargo could not write to the target path. Check terminal authorization and path permissions."
    else:
        explanation = "Cargo reported a build error."
    detail = f" Output: {output[-1200:]}" if output else ""
    raise LaunchError(
        f"Cargo command {command_text(command)} failed with exit status "
        f"{completed.returncode}. {explanation}{detail}"
    )


def spawn_app(executable, repo, arguments):
    """Start only the built Rust executable with detached standard handles."""
    return subprocess.Popen(
        [str(executable), *arguments],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    )


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class ProcessInspector:
    """Read live process paths and owned status windows."""

    def __init__(self):
        if sys.platform != "win32":
            raise LaunchError("The process inspector requires Windows.")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32FirstW.restype = wintypes.BOOL
        self.kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32NextW.restype = wintypes.BOOL
        self.kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user32.GetClassNameW.restype = ctypes.c_int
        self.window_callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        self.user32.EnumWindows.argtypes = [self.window_callback_type, wintypes.LPARAM]
        self.user32.EnumWindows.restype = wintypes.BOOL

    def _process_ids(self):
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot in (None, INVALID_HANDLE_VALUE):
            raise LaunchError(f"Windows could not enumerate processes: {ctypes.WinError()}")
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        process_ids = []
        try:
            if self.kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                while True:
                    process_ids.append(int(entry.th32ProcessID))
                    if not self.kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                        break
        finally:
            self.kernel32.CloseHandle(snapshot)
        return process_ids

    def _path_for_pid(self, pid):
        handle = self.open_process(pid)
        if not handle:
            return None
        try:
            return self._path_for_handle(handle)
        finally:
            self.close_handle(handle)

    def open_process(self, pid):
        return self.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_SYNCHRONIZE,
            False,
            pid,
        )

    def close_handle(self, handle):
        self.kernel32.CloseHandle(handle)

    def _path_for_handle(self, handle):
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not self.kernel32.QueryFullProcessImageNameW(
            handle, 0, buffer, ctypes.byref(size)
        ):
            return None
        return buffer.value

    def handle_is_alive(self, handle):
        wait_result = self.kernel32.WaitForSingleObject(handle, 0)
        if wait_result == WAIT_TIMEOUT:
            return True
        if wait_result == 0xFFFFFFFF:
            raise LaunchError(f"Windows could not check a process handle: {ctypes.WinError()}")
        return False

    def process_handle_is_alive(self, process):
        handle = getattr(process, "_handle", None)
        if handle in (None, INVALID_HANDLE_VALUE):
            raise LaunchError("The new Rust process has no usable process handle.")
        return self.handle_is_alive(handle)

    def image_matches_handle(self, handle, executable):
        path = self._path_for_handle(handle)
        wanted = os.path.normcase(os.path.normpath(str(executable)))
        return bool(path) and os.path.normcase(os.path.normpath(path)) == wanted

    def process_matches(self, pid, executable):
        wanted = os.path.normcase(os.path.normpath(str(executable)))
        if pid not in self._process_ids():
            return False
        path = self._path_for_pid(pid)
        return bool(path) and os.path.normcase(os.path.normpath(path)) == wanted

    def matching_pids(self, executable):
        wanted = os.path.normcase(os.path.normpath(str(executable)))
        matches = []
        for pid in self._process_ids():
            path = self._path_for_pid(pid)
            if path and os.path.normcase(os.path.normpath(path)) == wanted:
                matches.append(pid)
        return matches

    def window_for_pid(self, pid):
        found = [0]

        def visit(hwnd, _lparam):
            window_pid = wintypes.DWORD()
            if self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid)) == 0:
                return True
            if int(window_pid.value) != pid:
                return True
            class_name = ctypes.create_unicode_buffer(256)
            length = self.user32.GetClassNameW(hwnd, class_name, len(class_name))
            if length and class_name.value == "StayWatchStatusWindow":
                found[0] = int(hwnd)
                return False
            return True

        callback = self.window_callback_type(visit)
        self.user32.EnumWindows(callback, 0)
        return found[0]


def find_existing_instance(executable, inspector):
    for pid in inspector.matching_pids(executable):
        handle = inspector.open_process(pid)
        if not handle:
            continue
        try:
            if not inspector.handle_is_alive(handle):
                continue
            if not inspector.image_matches_handle(handle, executable):
                continue
            window_handle = inspector.window_for_pid(pid)
            if not inspector.handle_is_alive(handle):
                continue
            if not inspector.image_matches_handle(handle, executable):
                continue
            return Instance(pid, window_handle)
        finally:
            inspector.close_handle(handle)
    return None


def wait_for_startup(
    process,
    executable,
    inspector,
    timeout=STARTUP_TIMEOUT_SECONDS,
    monotonic=time.monotonic,
    sleeper=time.sleep,
):
    pid = process.pid
    deadline = monotonic() + timeout
    while True:
        if not inspector.process_handle_is_alive(process):
            return StartupResult(
                "startup_failed",
                pid,
                0,
                "The Rust process did not stay live during startup.",
            )
        if not inspector.process_matches(pid, executable):
            return StartupResult(
                "startup_failed",
                pid,
                0,
                "The Rust process image did not match the expected executable.",
            )
        window_handle = inspector.window_for_pid(pid)
        if not inspector.process_handle_is_alive(process):
            return StartupResult(
                "startup_failed",
                pid,
                0,
                "The original Rust process ended during the window check.",
            )
        if window_handle:
            return StartupResult("started", pid, int(window_handle))
        if monotonic() >= deadline:
            return StartupResult(
                "startup_timeout",
                pid,
                0,
                "The process stayed live, but no owned StayWatchStatusWindow appeared within the startup limit.",
            )
        sleeper(STARTUP_POLL_SECONDS)


def result(status, pid, executable, window_handle, error=""):
    value = {
        "status": status,
        "pid": pid,
        "executable_path": str(executable),
        "window_handle": int(window_handle or 0),
    }
    if error:
        value["error"] = error
    return value


class LaunchLock:
    """Serialize launch work for one checkout with a bounded named mutex."""

    def __init__(self, repo, timeout_ms=LOCK_TIMEOUT_MS):
        self.repo = repo
        self.timeout_ms = timeout_ms
        self.handle = None
        self.acquired = False
        self.kernel32 = None

    def __enter__(self):
        if sys.platform != "win32":
            raise LaunchError("The launch lock requires Windows.")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel32.CreateMutexW.restype = wintypes.HANDLE
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self.kernel32.ReleaseMutex.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        name = self._mutex_name()
        self.handle = self.kernel32.CreateMutexW(None, False, name)
        if not self.handle:
            raise LaunchError(f"Windows could not create the launch lock: {ctypes.WinError()}")
        wait_result = self.kernel32.WaitForSingleObject(self.handle, self.timeout_ms)
        if wait_result in (WAIT_OBJECT_0, WAIT_ABANDONED):
            self.acquired = True
            return self
        self.kernel32.CloseHandle(self.handle)
        self.handle = None
        if wait_result == WAIT_TIMEOUT:
            raise LockTimeoutError("Another launch is active for this checkout.")
        raise LaunchError(f"Windows could not acquire the launch lock: 0x{wait_result:08X}")

    def _mutex_name(self):
        identity = str(self.repo.resolve()).casefold().encode("utf-8")
        digest = hashlib.sha256(identity).hexdigest()[:24]
        return f"Local\\stay-up-launch-{digest}"

    def __exit__(self, _exception_type, _exception_value, _traceback):
        if self.acquired:
            self.kernel32.ReleaseMutex(self.handle)
            self.acquired = False
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


def emit(value, stream=None):
    if stream is None:
        stream = sys.stdout
    json.dump(value, stream, sort_keys=True)
    stream.write("\n")


def reported_executable(repo):
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        return expected_paths(localappdata).executable
    return repo / "stay-watch.exe"


def main(argv=None):
    args = parse_arguments(argv)
    repo = repo_root()
    try:
        paths = validate_setup(repo)
        inspector = ProcessInspector()
        with LaunchLock(repo):
            existing = find_existing_instance(paths.executable, inspector)
            if existing:
                emit(
                    result(
                        "already_running",
                        existing.pid,
                        paths.executable,
                        existing.window_handle,
                        "The exact stable executable path is already running. The requested arguments did not start a new session.",
                    )
                )
                return 0
            command = build_command(paths.cargo, repo, paths.stable_target)
            build_app(command, repo)
            if not paths.executable.is_file():
                raise LaunchError(
                    f"Cargo finished successfully, but the expected executable is missing: {paths.executable}"
                )
            arguments = [] if args.seconds is None else ["--seconds", str(args.seconds)]
            process = spawn_app(paths.executable, repo, arguments)
            try:
                startup = wait_for_startup(process, paths.executable, inspector)
            except (LaunchError, OSError, ctypes.ArgumentError) as error:
                emit(result("startup_failed", process.pid, paths.executable, 0, str(error)))
                return 1
            emit(result(startup.status, startup.pid, paths.executable, startup.window_handle, startup.error))
            return 0 if startup.status == "started" else 1
    except LockTimeoutError as error:
        emit(result("busy", None, reported_executable(repo), 0, str(error)))
        return 1
    except LaunchError as error:
        emit(result("failed", None, reported_executable(repo), 0, str(error)))
        return 1
    except (OSError, ctypes.ArgumentError) as error:
        emit(
            result(
                "failed",
                None,
                reported_executable(repo),
                0,
                f"Windows or process setup failed: {error}",
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
