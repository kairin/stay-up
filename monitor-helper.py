"""Write a heartbeat while a Windows process remains alive."""

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
import time


def write_line(path, message):
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write(f"{timestamp} {message}\n")
        stream.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    if args.pid <= 0 or args.interval <= 0:
        parser.error("PID and interval must be positive")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    synchronize = 0x00100000
    handle = kernel32.OpenProcess(synchronize, False, args.pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        write_line(args.log, f"monitor started; helper PID={args.pid}; interval={args.interval}s")
        while True:
            wait_result = kernel32.WaitForSingleObject(handle, 0)
            if wait_result == 0:
                write_line(args.log, f"STOPPED helper PID={args.pid}")
                return
            if wait_result != 0x00000102:
                write_line(args.log, f"ERROR wait result=0x{wait_result:08X}; helper PID={args.pid}")
                return
            write_line(args.log, f"OK helper PID={args.pid} is running")
            time.sleep(args.interval)
    finally:
        kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
