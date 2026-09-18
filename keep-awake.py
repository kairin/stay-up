"""Hold Windows display/system power requests until Ctrl+C or a time limit.

Uses only Python's standard library. No installation or persistent settings.
Reference: https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-powersetrequest
"""

import argparse
import ctypes
from ctypes import wintypes
import os
import sys
import time


class DetailedReason(ctypes.Structure):
    _fields_ = [
        ("module", wintypes.HMODULE),
        ("reason_id", wintypes.ULONG),
        ("count", wintypes.ULONG),
        ("strings", ctypes.POINTER(wintypes.LPWSTR)),
    ]


class ReasonUnion(ctypes.Union):
    _fields_ = [("detailed", DetailedReason), ("simple", wintypes.LPWSTR)]


class ReasonContext(ctypes.Structure):
    _fields_ = [
        ("version", wintypes.ULONG),
        ("flags", wintypes.DWORD),
        ("reason", ReasonUnion),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=0,
                        help="Duration; 0 means until Ctrl+C (default).")
    args = parser.parse_args()
    if args.seconds < 0:
        parser.error("--seconds must be zero or positive")
    if sys.platform != "win32":
        parser.error("This helper requires Windows")

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.PowerCreateRequest.argtypes = [ctypes.POINTER(ReasonContext)]
    api.PowerCreateRequest.restype = wintypes.HANDLE
    for name in ("PowerSetRequest", "PowerClearRequest"):
        function = getattr(api, name)
        function.argtypes = [wintypes.HANDLE, ctypes.c_int]
        function.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL

    context = ReasonContext()
    context.version = 0  # POWER_REQUEST_CONTEXT_VERSION
    context.flags = 1  # POWER_REQUEST_CONTEXT_SIMPLE_STRING
    context.reason.simple = "User requested display and system stay awake"
    handle = api.PowerCreateRequest(ctypes.byref(context))
    if handle in (None, ctypes.c_void_p(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())

    held = []
    cleanup_errors = []
    try:
        # SYSTEM first, then DISPLAY. No away-mode or input simulation.
        for request, label in ((1, "SYSTEM"), (0, "DISPLAY")):
            if not api.PowerSetRequest(handle, request):
                raise ctypes.WinError(ctypes.get_last_error())
            held.append(request)
            print(f"{label} request accepted by Windows.", flush=True)
        print(f"PID {os.getpid()}: keep-awake active. Ctrl+C stops it.", flush=True)
        deadline = time.monotonic() + args.seconds if args.seconds else None
        try:
            while deadline is None or time.monotonic() < deadline:
                time.sleep(1 if deadline is None else min(1, max(0, deadline - time.monotonic())))
        except KeyboardInterrupt:
            pass
    finally:
        for request in reversed(held):
            if not api.PowerClearRequest(handle, request):
                cleanup_errors.append(ctypes.get_last_error())
        if not api.CloseHandle(handle):
            cleanup_errors.append(ctypes.get_last_error())
        if cleanup_errors:
            raise RuntimeError(f"Request cleanup errors: {cleanup_errors}")
        print("Power requests released; normal power behavior restored.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"Keep-awake failed: {error}", file=sys.stderr)
        sys.exit(1)
