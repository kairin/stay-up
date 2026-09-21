"""Read-only Windows input, session, display, and power observations.

This probe does not simulate input. It does not change power or lock settings.
It does not create a keep-awake request.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
wtsapi = ctypes.WinDLL("wtsapi32", use_last_error=True)

HWND_MESSAGE = wintypes.HWND(-3)
WM_DESTROY = 0x0002
WM_INPUT = 0x00FF
WM_POWERBROADCAST = 0x0218
WM_WTSSESSION_CHANGE = 0x02B1
PBT_POWERSETTINGCHANGE = 0x8013
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000B
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2
NOTIFY_FOR_THIS_SESSION = 0
WTS_CURRENT_SERVER_HANDLE = wintypes.HANDLE(0)
WTS_CURRENT_SESSION = 0xFFFFFFFF
WTSSessionInfoEx = 24
DEVICE_NOTIFY_WINDOW_HANDLE = 0
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
WS_OVERLAPPED = 0x00000000
PM_REMOVE = 0x0001

GUID_ACDC_POWER_SOURCE = "{5D3E9A59-E9D5-4B00-A6BD-FF34FF516548}"
GUID_CONSOLE_DISPLAY_STATE = "{6FE69556-704A-47A0-8F24-C28D936FDA47}"
GUID_MONITOR_POWER_ON = "{02731015-4510-4526-99E6-E5A17EBD1AEA}"


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [("hDevice", wintypes.HANDLE), ("dwType", wintypes.DWORD)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RID_DEVICE_INFO_MOUSE(ctypes.Structure):
    _fields_ = [
        ("dwId", wintypes.DWORD),
        ("dwNumberOfButtons", wintypes.DWORD),
        ("dwSampleRate", wintypes.DWORD),
        ("fHasHorizontalWheel", wintypes.BOOL),
    ]


class RID_DEVICE_INFO_KEYBOARD(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSubType", wintypes.DWORD),
        ("dwKeyboardMode", wintypes.DWORD),
        ("dwNumberOfFunctionKeys", wintypes.DWORD),
        ("dwNumberOfIndicators", wintypes.DWORD),
        ("dwNumberOfKeysTotal", wintypes.DWORD),
    ]


class RID_DEVICE_INFO_HID(ctypes.Structure):
    _fields_ = [
        ("dwVendorId", wintypes.DWORD),
        ("dwProductId", wintypes.DWORD),
        ("dwVersionNumber", wintypes.DWORD),
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
    ]


class RID_DEVICE_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("mouse", RID_DEVICE_INFO_MOUSE),
        ("keyboard", RID_DEVICE_INFO_KEYBOARD),
        ("hid", RID_DEVICE_INFO_HID),
    ]


class RID_DEVICE_INFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("u", RID_DEVICE_INFO_UNION),
    ]


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

    @classmethod
    def from_string(cls, value):
        hex_value = value.strip("{}")
        data1 = int(hex_value[0:8], 16)
        data2 = int(hex_value[9:13], 16)
        data3 = int(hex_value[14:18], 16)
        rest = hex_value[19:].replace("-", "")
        data4 = (wintypes.BYTE * 8)(*[int(rest[i:i + 2], 16) for i in range(0, 16, 2)])
        return cls(data1, data2, data3, data4)


class POWERBROADCAST_SETTING(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", GUID),
        ("DataLength", wintypes.DWORD),
        ("Data", wintypes.BYTE * 1),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HANDLE),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class WTSINFOEX_LEVEL1_W(ctypes.Structure):
    _fields_ = [
        ("SessionId", wintypes.DWORD),
        ("SessionState", wintypes.INT),
        ("SessionFlags", wintypes.LONG),
        ("WinStationName", wintypes.WCHAR * 33),
        ("UserName", wintypes.WCHAR * 21),
        ("DomainName", wintypes.WCHAR * 18),
        ("LogonTime", ctypes.c_longlong),
        ("ConnectTime", ctypes.c_longlong),
        ("DisconnectTime", ctypes.c_longlong),
        ("LastInputTime", ctypes.c_longlong),
        ("CurrentTime", ctypes.c_longlong),
        ("IncomingBytes", wintypes.DWORD),
        ("OutgoingBytes", wintypes.DWORD),
        ("IncomingFrames", wintypes.DWORD),
        ("OutgoingFrames", wintypes.DWORD),
    ]


class WTSINFOEX_W(ctypes.Structure):
    _fields_ = [
        ("Level", wintypes.DWORD),
        ("Data", WTSINFOEX_LEVEL1_W),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetLastInputInfo.restype = wintypes.BOOL
user32.GetRawInputDeviceList.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICELIST),
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
]
user32.GetRawInputDeviceList.restype = wintypes.UINT
user32.GetRawInputDeviceInfoW.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT),
]
user32.GetRawInputDeviceInfoW.restype = wintypes.UINT
user32.RegisterRawInputDevices.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICE),
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterRawInputDevices.restype = wintypes.BOOL
user32.GetRawInputData.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
]
user32.GetRawInputData.restype = wintypes.UINT
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_longlong
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
    wintypes.UINT,
]
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = ctypes.c_longlong
user32.RegisterPowerSettingNotification.argtypes = [wintypes.HANDLE, ctypes.POINTER(GUID), wintypes.DWORD]
user32.RegisterPowerSettingNotification.restype = wintypes.HANDLE
user32.UnregisterPowerSettingNotification.argtypes = [wintypes.HANDLE]
user32.UnregisterPowerSettingNotification.restype = wintypes.BOOL
kernel32.GetSystemPowerStatus.argtypes = [ctypes.POINTER(SYSTEM_POWER_STATUS)]
kernel32.GetSystemPowerStatus.restype = wintypes.BOOL
kernel32.GetTickCount.argtypes = []
kernel32.GetTickCount.restype = wintypes.DWORD
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
wtsapi.WTSRegisterSessionNotification.argtypes = [wintypes.HWND, wintypes.DWORD]
wtsapi.WTSRegisterSessionNotification.restype = wintypes.BOOL
wtsapi.WTSUnRegisterSessionNotification.argtypes = [wintypes.HWND]
wtsapi.WTSUnRegisterSessionNotification.restype = wintypes.BOOL
wtsapi.WTSQuerySessionInformationW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(wintypes.DWORD),
]
wtsapi.WTSQuerySessionInformationW.restype = wintypes.BOOL
wtsapi.WTSFreeMemory.argtypes = [ctypes.c_void_p]
wtsapi.WTSFreeMemory.restype = None


def handle_int(value):
    return int(getattr(value, "value", value) or 0)


def last_input_snapshot():
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ok = bool(user32.GetLastInputInfo(ctypes.byref(info)))
    tick = int(kernel32.GetTickCount())
    idle_ms = None
    if ok:
        idle_ms = int(tick - info.dwTime) if tick >= info.dwTime else None
    return {
        "ok": ok,
        "dwTime": int(info.dwTime) if ok else None,
        "tick_count": tick,
        "idle_ms_unwrapped": idle_ms,
        "last_error": ctypes.get_last_error() if not ok else 0,
    }


def power_status_snapshot():
    status = SYSTEM_POWER_STATUS()
    ok = bool(kernel32.GetSystemPowerStatus(ctypes.byref(status)))
    ac_map = {0: "battery", 1: "ac", 255: "unknown"}
    return {
        "ok": ok,
        "ac_line": ac_map.get(int(status.ACLineStatus), "unknown"),
        "ac_line_raw": int(status.ACLineStatus),
        "battery_flag": int(status.BatteryFlag),
        "battery_percent": int(status.BatteryLifePercent),
        "system_status_flag": int(status.SystemStatusFlag),
        "last_error": ctypes.get_last_error() if not ok else 0,
    }


def classify_device(name, dw_type, hid_usage_page, hid_usage):
    lowered = (name or "").lower()
    if dw_type == RIM_TYPEKEYBOARD:
        return "keyboard"
    if hid_usage_page == 0x0D and hid_usage in (0x04, 0x05):
        return "touchpad"
    if "touchpad" in lowered or "touch pad" in lowered or "synaptics" in lowered or "elan" in lowered:
        return "touchpad"
    if dw_type == RIM_TYPEMOUSE:
        return "mouse"
    return "hid"


def raw_device_snapshot():
    count = wintypes.UINT(0)
    listed = user32.GetRawInputDeviceList(None, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if listed == 0xFFFFFFFF:
        return {"ok": False, "last_error": ctypes.get_last_error(), "devices": []}
    if count.value == 0:
        return {"ok": True, "devices": []}
    array_type = RAWINPUTDEVICELIST * count.value
    devices = array_type()
    listed = user32.GetRawInputDeviceList(devices, ctypes.byref(count), ctypes.sizeof(RAWINPUTDEVICELIST))
    if listed == 0xFFFFFFFF:
        return {"ok": False, "last_error": ctypes.get_last_error(), "devices": []}
    result = []
    for item in devices[:listed]:
        size = wintypes.UINT(0)
        user32.GetRawInputDeviceInfoW(item.hDevice, RIDI_DEVICENAME, None, ctypes.byref(size))
        name = None
        if size.value:
            buf = ctypes.create_unicode_buffer(size.value)
            if user32.GetRawInputDeviceInfoW(item.hDevice, RIDI_DEVICENAME, buf, ctypes.byref(size)) != 0xFFFFFFFF:
                name = buf.value
        info = RID_DEVICE_INFO()
        info.cbSize = ctypes.sizeof(RID_DEVICE_INFO)
        info_size = wintypes.UINT(ctypes.sizeof(RID_DEVICE_INFO))
        hid_usage_page = None
        hid_usage = None
        if user32.GetRawInputDeviceInfoW(
            item.hDevice, RIDI_DEVICEINFO, ctypes.byref(info), ctypes.byref(info_size)
        ) != 0xFFFFFFFF and info.dwType == RIM_TYPEHID:
            hid_usage_page = int(info.u.hid.usUsagePage)
            hid_usage = int(info.u.hid.usUsage)
        category = classify_device(name, int(item.dwType), hid_usage_page, hid_usage)
        result.append({
            "hDevice": handle_int(item.hDevice),
            "dwType": int(item.dwType),
            "name": name,
            "category": category,
            "hid_usage_page": hid_usage_page,
            "hid_usage": hid_usage,
        })
    return {"ok": True, "devices": result}


def session_lock_snapshot():
    buf = ctypes.c_void_p()
    nbytes = wintypes.DWORD(0)
    ok = bool(
        wtsapi.WTSQuerySessionInformationW(
            WTS_CURRENT_SERVER_HANDLE,
            WTS_CURRENT_SESSION,
            WTSSessionInfoEx,
            ctypes.byref(buf),
            ctypes.byref(nbytes),
        )
    )
    if not ok or not buf:
        return {"ok": False, "last_error": ctypes.get_last_error()}
    try:
        raw = ctypes.string_at(buf, nbytes.value)
        if len(raw) < 16:
            return {"ok": False, "error": "short_buffer", "byte_length": int(nbytes.value)}
        # WTSINFOEX: DWORD Level, then WTSINFOEX_LEVEL1 with no extra padding on this host.
        level = int.from_bytes(raw[0:4], "little")
        session_id = int.from_bytes(raw[4:8], "little")
        session_state = int.from_bytes(raw[8:12], "little", signed=True)
        session_flags = int.from_bytes(raw[12:16], "little", signed=True)
        lock_label = {0: "locked", 1: "unlocked"}.get(session_flags, "unknown")
        return {
            "ok": True,
            "level": level,
            "session_id": session_id,
            "session_state": session_state,
            "session_flags": session_flags,
            "lock_label": lock_label,
            "byte_length": int(nbytes.value),
        }
    finally:
        wtsapi.WTSFreeMemory(buf)


def powercfg_available_states():
    completed = subprocess.run(
        ["powercfg.exe", "/a"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    text = (completed.stdout or "") + (completed.stderr or "")
    available, _sep, _rest = text.partition("The following sleep states are not available")
    return {
        "exit_code": int(completed.returncode),
        "s0_low_power_idle": "Standby (S0 Low Power Idle)" in available,
        "output": text.strip(),
    }


def pump(hwnd, seconds, events):
    deadline = time.monotonic() + seconds
    msg = MSG()
    while time.monotonic() < deadline:
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.05)
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen-seconds", type=float, default=20.0)
    parser.add_argument("--output", help="Write JSON to this path as well as stdout.")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This probe requires Windows")

    events = {
        "raw_input": [],
        "power_setting": [],
        "session_change": [],
        "counts_by_type": {"mouse": 0, "keyboard": 0, "hid": 0},
        "counts_by_device": {},
    }
    devices_by_handle = {}

    def record_raw_input(lparam):
        size = wintypes.UINT(0)
        header_size = ctypes.sizeof(RAWINPUTHEADER)
        user32.GetRawInputData(wintypes.HANDLE(lparam), RID_INPUT, None, ctypes.byref(size), header_size)
        if not size.value:
            return
        buf = ctypes.create_string_buffer(size.value)
        copied = user32.GetRawInputData(
            wintypes.HANDLE(lparam), RID_INPUT, buf, ctypes.byref(size), header_size
        )
        if copied == 0xFFFFFFFF:
            return
        header = RAWINPUTHEADER.from_buffer_copy(buf.raw[:header_size])
        dw_type = int(header.dwType)
        handle = handle_int(header.hDevice)
        type_name = {0: "mouse", 1: "keyboard", 2: "hid"}.get(dw_type, "unknown")
        events["counts_by_type"][type_name] = events["counts_by_type"].get(type_name, 0) + 1
        key = str(handle)
        events["counts_by_device"][key] = events["counts_by_device"].get(key, 0) + 1
        if len(events["raw_input"]) < 32:
            events["raw_input"].append({
                "dwType": dw_type,
                "type_name": type_name,
                "hDevice": handle,
                "category": devices_by_handle.get(handle, {}).get("category"),
            })

    def record_power(lparam):
        if not lparam:
            return
        setting = ctypes.cast(lparam, ctypes.POINTER(POWERBROADCAST_SETTING)).contents
        data_len = int(setting.DataLength)
        raw = ctypes.string_at(ctypes.addressof(setting.Data), max(0, min(data_len, 8)))
        value = int.from_bytes(raw, "little") if raw else None
        guid = "{%08X-%04X-%04X-%02X%02X-%02X%02X%02X%02X%02X%02X}" % (
            setting.PowerSetting.Data1,
            setting.PowerSetting.Data2,
            setting.PowerSetting.Data3,
            *list(setting.PowerSetting.Data4),
        )
        label = {
            GUID_ACDC_POWER_SOURCE.upper(): "acdc_power_source",
            GUID_CONSOLE_DISPLAY_STATE.upper(): "console_display_state",
            GUID_MONITOR_POWER_ON.upper(): "monitor_power_on",
        }.get(guid.upper(), guid)
        events["power_setting"].append({"label": label, "guid": guid, "value": value})

    @WNDPROC
    def wndproc(hwnd, message, wparam, lparam):
        if message == WM_INPUT:
            record_raw_input(lparam)
            return 0
        if message == WM_POWERBROADCAST and wparam == PBT_POWERSETTINGCHANGE:
            record_power(lparam)
            return 1
        if message == WM_WTSSESSION_CHANGE:
            events["session_change"].append({"wparam": int(wparam)})
            return 0
        if message == WM_DESTROY:
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    class_name = "StayUpWindowsStateProbe"
    window_class = WNDCLASSEXW()
    window_class.cbSize = ctypes.sizeof(WNDCLASSEXW)
    window_class.style = CS_HREDRAW | CS_VREDRAW
    window_class.lpfnWndProc = ctypes.cast(wndproc, ctypes.c_void_p)
    window_class.hInstance = kernel32.GetModuleHandleW(None)
    window_class.lpszClassName = class_name
    atom = user32.RegisterClassExW(ctypes.byref(window_class))
    if not atom:
        raise ctypes.WinError(ctypes.get_last_error())
    hwnd = user32.CreateWindowExW(
        0,
        class_name,
        "stay-up-windows-state-probe",
        WS_OVERLAPPED,
        0,
        0,
        0,
        0,
        HWND_MESSAGE,
        None,
        window_class.hInstance,
        None,
    )
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    registrations = {"raw_input": [], "power": [], "session": False}
    usages = [
        (0x01, 0x06, "keyboard"),
        (0x01, 0x02, "mouse"),
        (0x0D, 0x05, "touchpad"),
    ]
    for page, usage, label in usages:
        device = RAWINPUTDEVICE(page, usage, RIDEV_INPUTSINK, hwnd)
        ok = bool(user32.RegisterRawInputDevices(ctypes.byref(device), 1, ctypes.sizeof(RAWINPUTDEVICE)))
        registrations["raw_input"].append({
            "label": label,
            "usage_page": page,
            "usage": usage,
            "ok": ok,
            "last_error": 0 if ok else ctypes.get_last_error(),
        })

    power_handles = []
    for guid_text, label in (
        (GUID_ACDC_POWER_SOURCE, "acdc_power_source"),
        (GUID_CONSOLE_DISPLAY_STATE, "console_display_state"),
        (GUID_MONITOR_POWER_ON, "monitor_power_on"),
    ):
        guid = GUID.from_string(guid_text)
        handle = user32.RegisterPowerSettingNotification(hwnd, ctypes.byref(guid), DEVICE_NOTIFY_WINDOW_HANDLE)
        ok = bool(handle)
        registrations["power"].append({"label": label, "ok": ok, "last_error": 0 if ok else ctypes.get_last_error()})
        if ok:
            power_handles.append(handle)

    registrations["session"] = bool(wtsapi.WTSRegisterSessionNotification(hwnd, NOTIFY_FOR_THIS_SESSION))
    if not registrations["session"]:
        registrations["session_last_error"] = ctypes.get_last_error()

    devices = raw_device_snapshot()
    if devices.get("ok"):
        for item in devices["devices"]:
            devices_by_handle[item["hDevice"]] = item

    before_input = last_input_snapshot()
    before_power = power_status_snapshot()
    before_lock = session_lock_snapshot()
    listen_seconds = max(0.0, float(args.listen_seconds))
    try:
        pump(hwnd, listen_seconds, events)
    finally:
        if registrations["session"]:
            wtsapi.WTSUnRegisterSessionNotification(hwnd)
        for handle in power_handles:
            user32.UnregisterPowerSettingNotification(handle)
        user32.DestroyWindow(hwnd)

    after_input = last_input_snapshot()
    after_power = power_status_snapshot()
    after_lock = session_lock_snapshot()
    categories = {}
    for item in devices.get("devices", []):
        categories[item["category"]] = categories.get(item["category"], 0) + 1

    report = {
        "probe": "windows-state-probe",
        "pid": os.getpid(),
        "listen_seconds": listen_seconds,
        "last_input_before": before_input,
        "last_input_after": after_input,
        "last_input_changed": before_input.get("dwTime") != after_input.get("dwTime"),
        "power_before": before_power,
        "power_after": after_power,
        "session_before": before_lock,
        "session_after": after_lock,
        "session_changed": before_lock.get("session_flags") != after_lock.get("session_flags"),
        "raw_devices": devices,
        "device_category_counts": categories,
        "registrations": registrations,
        "observed_events": {
            "raw_input_sample": events["raw_input"],
            "counts_by_type": events["counts_by_type"],
            "counts_by_device": events["counts_by_device"],
            "power_setting": events["power_setting"],
            "session_change": events["session_change"],
        },
        "powercfg": powercfg_available_states(),
        "limits": [
            "No input was simulated.",
            "No lock, sleep, or power-source change was requested.",
            "Missing live events stay unknown; they are not a fail of API presence.",
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        parent = os.path.dirname(os.path.abspath(args.output))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")


if __name__ == "__main__":
    main()
