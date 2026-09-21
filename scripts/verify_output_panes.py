"""Explicit live regression for the native panes; no screenshots or input injection.

Starts two bounded test sessions through launch.py, only when no app is running.
Uses window messages for resize/minimize/Stop and holds owned process handles.
The unchanged helper makes its normal power requests during these sessions.
"""

import argparse
import ctypes
from ctypes import wintypes
import json
import re
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launch


class Desktop:
    def __init__(self):
        self.inspector = launch.ProcessInspector()
        self.user = self.inspector.user32
        self.kernel = self.inspector.kernel32
        self.user.EnumChildWindows.argtypes = [wintypes.HWND, self.inspector.window_callback_type, wintypes.LPARAM]
        self.user.EnumChildWindows.restype = wintypes.BOOL
        self.user.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t, wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
        self.user.SendMessageTimeoutW.restype = ctypes.c_ssize_t
        self.user.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user.GetWindowLongW.restype = wintypes.LONG
        self.user.IsWindowVisible.argtypes = [wintypes.HWND]
        self.user.IsWindowVisible.restype = wintypes.BOOL
        self.user.IsIconic.argtypes = [wintypes.HWND]
        self.user.IsIconic.restype = wintypes.BOOL
        self.user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user.ShowWindow.restype = wintypes.BOOL
        self.user.MoveWindow.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.BOOL]
        self.user.MoveWindow.restype = wintypes.BOOL
        self.user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.GetWindowRect.restype = wintypes.BOOL
        self.user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.GetClientRect.restype = wintypes.BOOL
        self.user.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        self.user.ClientToScreen.restype = wintypes.BOOL
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.kernel.GetProcessTimes.restype = wintypes.BOOL

    def send(self, hwnd, msg, wp=0, lp=0):
        result = ctypes.c_size_t()
        if not self.user.SendMessageTimeoutW(hwnd, msg, wp, lp, 2, 2000, ctypes.byref(result)):
            raise RuntimeError(f"Window message failed: {ctypes.WinError()}")
        return result.value

    def windows(self, parent=None):
        found = []
        def visit(hwnd, _):
            name = ctypes.create_unicode_buffer(256)
            pid = wintypes.DWORD()
            self.user.GetClassNameW(hwnd, name, len(name))
            self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            found.append((int(hwnd), name.value, pid.value))
            return True
        callback = self.inspector.window_callback_type(visit)
        if parent:
            self.user.EnumChildWindows(parent, callback, 0)
        else:
            self.user.EnumWindows(callback, 0)
        return found

    def text(self, hwnd):
        buffer = ctypes.create_unicode_buffer(150000)
        self.send(hwnd, 0x000D, len(buffer), ctypes.addressof(buffer))
        return buffer.value

    def created(self, handle):
        values = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(v) for v in values)):
            raise ctypes.WinError()
        return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime

    def check_bounds(self, parent, controls):
        client, origin = wintypes.RECT(), wintypes.POINT()
        require(self.user.GetClientRect(parent, ctypes.byref(client)), 'Cannot read client bounds')
        require(self.user.ClientToScreen(parent, ctypes.byref(origin)), 'Cannot locate client area')
        for control in controls:
            bounds = wintypes.RECT()
            require(self.user.GetWindowRect(control, ctypes.byref(bounds)), 'Cannot read control bounds')
            require(bounds.right > bounds.left and bounds.bottom > bounds.top, 'Control must have positive area')
            require(bounds.left >= origin.x and bounds.top >= origin.y and bounds.right <= origin.x + client.right and bounds.bottom <= origin.y + client.bottom, 'Pane or Stop extends outside client area')

    def descendants(self, root):
        handles = {root: self.inspector.open_process(root)}
        if not handles[root]:
            raise RuntimeError("Cannot hold the new app process")
        births = {root: self.created(handles[root])}
        snapshot = self.kernel.CreateToolhelp32Snapshot(launch.TH32CS_SNAPPROCESS, 0)
        if snapshot in (None, launch.INVALID_HANDLE_VALUE):
            raise ctypes.WinError()
        entries = []
        item = launch.PROCESSENTRY32W()
        item.dwSize = ctypes.sizeof(item)
        try:
            ok = self.kernel.Process32FirstW(snapshot, ctypes.byref(item))
            while ok:
                entries.append((item.th32ProcessID, item.th32ParentProcessID))
                ok = self.kernel.Process32NextW(snapshot, ctypes.byref(item))
        finally:
            self.kernel.CloseHandle(snapshot)
        changed = True
        while changed:
            changed = False
            for pid, parent in entries:
                if pid in handles or parent not in handles:
                    continue
                handle = self.inspector.open_process(pid)
                if not handle:
                    continue
                birth = self.created(handle)
                if birth < births[parent]:
                    self.inspector.close_handle(handle)
                    continue
                handles[pid], births[pid] = handle, birth
                changed = True
        return handles


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_session(desktop, mode, seconds):
    executable = launch.expected_paths(launch.os.environ['LOCALAPPDATA']).executable
    require(not desktop.inspector.matching_pids(executable), "Existing app: leave it untouched and close it before running this test")
    log = ROOT / 'logs' / 'keep-awake.monitor.log'
    before = log.read_bytes() if log.exists() else b''
    command = [sys.executable, '-B', str(ROOT / 'launch.py'), '--seconds', str(seconds)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, result.stdout + result.stderr)
    started = json.loads(result.stdout)
    require(started['status'] == 'started', str(started))
    hwnd, pid = started['window_handle'], started['pid']
    handles = {}
    try:
        time.sleep(2)
        handles = desktop.descendants(pid)
        require(len(handles) >= 3, 'Expected Rust and both owned Python processes')
        children = desktop.windows(hwnd)
        edits = [w for w, cls, _ in children if cls.lower() == 'edit']
        require(len(edits) >= 2, 'Two native output edit controls must exist')
        texts = [desktop.text(w) for w in edits]
        require(all(desktop.user.GetWindowLongW(w, -16) & 0x0800 for w in edits), 'Panes must be read-only')
        helper = next((t for t in texts if 'request accepted by Windows' in t), '')
        require('SYSTEM request accepted' in helper and 'DISPLAY request accepted' in helper and 'PID ' in helper, 'Startup output including PID handshake must be retained')
        helper_pid = int(re.search(r'PID (\d+):', helper).group(1))
        require(helper_pid in handles, 'Displayed helper PID must belong to this session')
        monitor_edit = next((w for w, t in zip(edits, texts) if f'OK helper PID={helper_pid} ' in t), None)
        require(monitor_edit is not None, 'Current session heartbeat records must be visible')
        visible = [(w, cls, p) for w, cls, p in desktop.windows() if p in handles and desktop.user.IsWindowVisible(w)]
        require(len(visible) == 1 and visible[0][0] == hwnd, f'Unexpected owned visible windows: {visible}')
        buttons = [w for w, cls, _ in children if cls.lower() == 'button' and desktop.text(w) == 'Stop']
        require(buttons, 'Stop must have an accessible native caption')
        if mode == 'stop':
            splitters = [w for w, cls, _ in children if cls.lower() == 'msctls_trackbar32']
            require(splitters, 'Expected a native keyboard-accessible split control')
            original = wintypes.RECT()
            desktop.user.GetWindowRect(edits[0], ctypes.byref(original))
            desktop.send(splitters[0], 0x0405, 1, 35)
            # The split control may be horizontal or vertical.
            message = 0x0115 if desktop.user.GetWindowLongW(splitters[0], -16) & 2 else 0x0114
            desktop.send(hwnd, message, 5, splitters[0])
            adjusted = wintypes.RECT()
            desktop.user.GetWindowRect(edits[0], ctypes.byref(adjusted))
            require(original.right - original.left != adjusted.right - adjusted.left, 'Split adjustment did not resize panes')
            desktop.send(hwnd, 0x0010)  # WM_CLOSE: preserve minimize semantics.
            require(desktop.user.IsIconic(hwnd), 'X must minimize')
            require(all(desktop.inspector.handle_is_alive(h) for h in handles.values()), 'Minimize must not end children')
            desktop.user.ShowWindow(hwnd, 9)
            desktop.user.MoveWindow(hwnd, 100, 100, 1000, 760, True)
            desktop.check_bounds(hwnd, edits + buttons)
            time.sleep(1)
            desktop.send(hwnd, 0x0111, 1)  # Existing Stop command.
        refresh_branch = 'not-applicable'
        if mode == 'timed' and seconds >= 65:
            desktop.send(monitor_edit, 0x00B1, 0, 6)  # Select existing text before the next heartbeat.
            initial_pane = desktop.text(monitor_edit)
            baseline_count = initial_pane.count(f'OK helper PID={helper_pid} ')
            heartbeat_deadline = time.monotonic() + 61
            while True:
                current = log.read_bytes()
                require(current.startswith(before), 'Heartbeat log changed before its saved prefix')
                added_text = current[len(before):].decode('utf-8', errors='replace')
                if added_text.count(f'OK helper PID={helper_pid} ') >= 2:
                    break
                require(time.monotonic() < heartbeat_deadline, 'Next heartbeat did not reach the log')
                time.sleep(0.25)
            time.sleep(2)
            selected_pane = desktop.text(monitor_edit)
            require(
                selected_pane == initial_pane or selected_pane.startswith(initial_pane),
                'Output refresh changed the selected text or its prefix',
            )
            selected = desktop.send(monitor_edit, 0x00B0)
            require(selected & 0xffff == 0 and selected >> 16 == 6, 'Output refresh changed the user selection')
            if selected_pane.count(f'OK helper PID={helper_pid} ') > baseline_count:
                refresh_branch = 'append-while-selected'
            else:
                refresh_branch = 'deferred-while-selected'
                desktop.send(monitor_edit, 0x00B1, 0, 0)
                pane_deadline = time.monotonic() + 15
                while desktop.text(monitor_edit).count(f'OK helper PID={helper_pid} ') <= baseline_count:
                    require(time.monotonic() < pane_deadline, 'Next heartbeat did not reach the pane after selection cleared')
                    time.sleep(0.25)
        deadline = time.monotonic() + seconds + 10
        while any(desktop.inspector.handle_is_alive(h) for h in handles.values()) and time.monotonic() < deadline:
            time.sleep(0.2)
        require(all(not desktop.inspector.handle_is_alive(h) for h in handles.values()), 'Owned processes did not all exit')
        after = log.read_bytes()
        require(after.startswith(before), 'Existing heartbeat bytes must remain intact')
        added = after[len(before):].decode('utf-8')
        require(f'helper PID={helper_pid}; interval=60s' in added and f'OK helper PID={helper_pid} ' in added, 'Heartbeat format/interval changed')
        if mode == 'timed' and seconds >= 65:
            require(added.count(f'OK helper PID={helper_pid} ') >= 2, 'Expected initial and subsequent heartbeat')
        print(json.dumps({'mode': mode, 'status': 'passed', 'pid': pid, 'owned_pids': list(handles), 'native_panes': len(edits), 'visible_owned_windows': len(visible), 'heartbeat_records_added': len(added.splitlines()), 'refresh_branch': refresh_branch}), flush=True)
    finally:
        # Only this harness's new instance may receive Stop on test failure.
        if handles and desktop.inspector.handle_is_alive(handles[pid]):
            if desktop.inspector.window_for_pid(pid) == hwnd:
                desktop.send(hwnd, 0x0111, 1)
        for handle in handles.values():
            desktop.inspector.close_handle(handle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Start the bounded live sessions')
    args = parser.parse_args()
    if not args.run:
        parser.error('Pass --run to explicitly start live regression sessions')
    desktop = Desktop()
    run_session(desktop, 'timed', 75)
    run_session(desktop, 'stop', 20)
