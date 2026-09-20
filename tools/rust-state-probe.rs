#![allow(non_snake_case)]

// Read-only Windows state probe. This program does not simulate input.
// It does not change power or lock settings.

#[repr(C)]
struct LastInputInfo {
    cb_size: u32,
    dw_time: u32,
}

#[repr(C)]
struct SystemPowerStatus {
    ac_line_status: u8,
    battery_flag: u8,
    battery_life_percent: u8,
    system_status_flag: u8,
    battery_life_time: u32,
    battery_full_life_time: u32,
}

#[repr(C)]
struct RawInputDeviceList {
    h_device: *mut core::ffi::c_void,
    dw_type: u32,
}

#[link(name = "user32")]
extern "system" {
    fn GetLastInputInfo(plii: *mut LastInputInfo) -> i32;
    fn GetRawInputDeviceList(
        pRawInputDeviceList: *mut RawInputDeviceList,
        puiNumDevices: *mut u32,
        cbSize: u32,
    ) -> u32;
    fn GetConsoleWindow() -> *mut core::ffi::c_void;
}

#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentProcessId() -> u32;
    fn GetTickCount() -> u32;
    fn GetSystemPowerStatus(lpSystemPowerStatus: *mut SystemPowerStatus) -> i32;
}

fn main() {
    let mut last_input = LastInputInfo {
        cb_size: core::mem::size_of::<LastInputInfo>() as u32,
        dw_time: 0,
    };
    let last_input_ok = unsafe { GetLastInputInfo(&mut last_input) } != 0;
    let tick = unsafe { GetTickCount() };
    let mut power = SystemPowerStatus {
        ac_line_status: 255,
        battery_flag: 0,
        battery_life_percent: 0,
        system_status_flag: 0,
        battery_life_time: 0,
        battery_full_life_time: 0,
    };
    let power_ok = unsafe { GetSystemPowerStatus(&mut power) } != 0;
    let mut count: u32 = 0;
    let size = core::mem::size_of::<RawInputDeviceList>() as u32;
    let listed = unsafe { GetRawInputDeviceList(core::ptr::null_mut(), &mut count, size) };
    let mut mouse = 0u32;
    let mut keyboard = 0u32;
    let mut hid = 0u32;
    let mut list_ok = listed != u32::MAX;
    if list_ok && count > 0 {
        let mut devices: Vec<RawInputDeviceList> = Vec::with_capacity(count as usize);
        let mut live_count = count;
        let filled = unsafe { GetRawInputDeviceList(devices.as_mut_ptr(), &mut live_count, size) };
        if filled == u32::MAX {
            list_ok = false;
        } else {
            unsafe { devices.set_len(filled as usize) };
            for device in &devices {
                match device.dw_type {
                    0 => mouse += 1,
                    1 => keyboard += 1,
                    2 => hid += 1,
                    _ => {}
                }
            }
        }
    }
    let pid = unsafe { GetCurrentProcessId() };
    let console = unsafe { GetConsoleWindow() } as usize;
    println!(
        "RUST_STATE_PROBE_OK pid={} console_hwnd={} last_input_ok={} dwTime={} tick={} power_ok={} ac={} batt%={} raw_ok={} mouse={} keyboard={} hid={}",
        pid,
        console,
        last_input_ok as u8,
        last_input.dw_time,
        tick,
        power_ok as u8,
        power.ac_line_status,
        power.battery_life_percent,
        list_ok as u8,
        mouse,
        keyboard,
        hid
    );
}
