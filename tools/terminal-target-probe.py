"""Read-only native enumeration of candidate terminal windows."""
import ctypes
import json
import os
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
try:
    dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
except OSError:
    dwmapi = None

HWND = wintypes.HWND
DWORD = wintypes.DWORD
BOOL = wintypes.BOOL
LPARAM = wintypes.LPARAM
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DWMWA_CLOAKED = 14

user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM), LPARAM]
user32.EnumWindows.restype = BOOL
user32.IsWindowVisible.argtypes = [HWND]
user32.IsWindowVisible.restype = BOOL
user32.IsIconic.argtypes = [HWND]
user32.IsIconic.restype = BOOL
user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(DWORD)]
user32.GetWindowThreadProcessId.restype = DWORD
user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = BOOL
kernel32.GetConsoleWindow.argtypes = []
kernel32.GetConsoleWindow.restype = HWND
kernel32.OpenProcess.argtypes = [DWORD, BOOL, DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = BOOL
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, DWORD, wintypes.LPWSTR, ctypes.POINTER(DWORD)]
kernel32.QueryFullProcessImageNameW.restype = BOOL
if dwmapi is not None:
    dwmapi.DwmGetWindowAttribute.argtypes = [HWND, DWORD, ctypes.c_void_p, DWORD]
    dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long


def process_basename(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return None
        return os.path.basename(buffer.value).lower()
    finally:
        kernel32.CloseHandle(handle)


def cloaked(hwnd):
    if dwmapi is None:
        return None
    value = wintypes.DWORD(0)
    result = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(value), ctypes.sizeof(value))
    return bool(value.value) if result == 0 else None


def main():
    context = kernel32.GetConsoleWindow()
    candidates = []
    target_names = {"windowsterminal.exe", "openconsole.exe"}
    callback_error = None

    @ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
    def visit(hwnd, _lparam):
        nonlocal callback_error
        try:
            pid = DWORD(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            basename = process_basename(pid.value)
            if basename not in target_names:
                return True
            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True
            visible = bool(user32.IsWindowVisible(hwnd))
            minimized = bool(user32.IsIconic(hwnd))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            cloak_state = cloaked(hwnd)
            candidates.append({
                "hwnd": int(getattr(hwnd, "value", hwnd) or 0),
                "pid": int(pid.value),
                "basename": basename,
                "visible": visible,
                "minimized": minimized,
                "rect": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
                "cloaked": cloak_state,
                "eligible_candidate": visible and not minimized and width > 0 and height > 0 and cloak_state is not True,
            })
            return True
        except Exception as exc:
            callback_error = f"{type(exc).__name__}: {exc}"
            return False

    enumerated = bool(user32.EnumWindows(visit, 0))
    context_value = int(getattr(context, "value", context) or 0)
    if not enumerated:
        result = {
            "context_console_hwnd": context_value,
            "candidates": candidates,
            "enumeration_succeeded": False,
            "error": callback_error or "EnumWindows returned false",
            "last_error": ctypes.get_last_error(),
        }
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps({"context_console_hwnd": context_value, "candidates": candidates, "enumeration_succeeded": True}, sort_keys=True))


if __name__ == "__main__":
    main()
