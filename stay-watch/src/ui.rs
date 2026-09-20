//! Small visible status window. The launcher is not a console-only tool.

#![allow(non_snake_case)]

use std::ffi::c_void;
use std::mem;
use std::process::Child;
use std::ptr;
use std::time::Instant;

use stay_watch::{format_elapsed, should_reset_idle};

type HWND = *mut c_void;
type HDC = *mut c_void;
type HINSTANCE = *mut c_void;
type HBRUSH = *mut c_void;

const WM_DESTROY: u32 = 0x0002;
const WM_CLOSE: u32 = 0x0010;
const WM_COMMAND: u32 = 0x0111;
const WM_PAINT: u32 = 0x000F;
const WM_TIMER: u32 = 0x0113;
const WS_OVERLAPPEDWINDOW: u32 = 0x00CF_0000;
const WS_VISIBLE: u32 = 0x1000_0000;
const WS_CHILD: u32 = 0x4000_0000;
const CW_USEDEFAULT: i32 = -2147483648;
const SW_SHOWNORMAL: i32 = 1;
const SW_MINIMIZE: i32 = 6;
const ID_STOP: isize = 1;
const COLOR_WINDOW: i32 = 5;
const GWLP_USERDATA: i32 = -21;
const DT_LEFT: u32 = 0x0000;
const DT_TOP: u32 = 0x0000;
const TRANSPARENT: i32 = 1;

#[repr(C)]
struct POINT {
    x: i32,
    y: i32,
}

#[repr(C)]
struct RECT {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}

#[repr(C)]
struct MSG {
    hwnd: HWND,
    message: u32,
    wparam: usize,
    lparam: isize,
    time: u32,
    pt: POINT,
}

#[repr(C)]
struct PAINTSTRUCT {
    hdc: HDC,
    erase: i32,
    rc_paint: RECT,
    restore: i32,
    inc_update: i32,
    reserved: [u8; 32],
}

#[repr(C)]
struct LASTINPUTINFO {
    cbSize: u32,
    dwTime: u32,
}

#[repr(C)]
struct WNDCLASSW {
    style: u32,
    wnd_proc: Option<extern "system" fn(HWND, u32, usize, isize) -> isize>,
    cls_extra: i32,
    wnd_extra: i32,
    instance: HINSTANCE,
    icon: *mut c_void,
    cursor: *mut c_void,
    background: HBRUSH,
    menu_name: *const u16,
    class_name: *const u16,
}

struct AppState {
    keep: Child,
    monitor: Child,
    helper_pid: u32,
    monitor_pid: u32,
    started: Instant,
    last_input_tick: u32,
    have_input_sample: bool,
}

#[link(name = "user32")]
extern "system" {
    fn RegisterClassW(wndclass: *const WNDCLASSW) -> u16;
    fn CreateWindowExW(
        ex: u32,
        class: *const u16,
        name: *const u16,
        style: u32,
        x: i32,
        y: i32,
        width: i32,
        height: i32,
        parent: HWND,
        menu: *mut c_void,
        instance: HINSTANCE,
        param: *mut c_void,
    ) -> HWND;
    fn ShowWindow(hwnd: HWND, cmd: i32) -> i32;
    fn UpdateWindow(hwnd: HWND) -> i32;
    fn GetMessageW(msg: *mut MSG, hwnd: HWND, min: u32, max: u32) -> i32;
    fn TranslateMessage(msg: *const MSG) -> i32;
    fn DispatchMessageW(msg: *const MSG) -> isize;
    fn DefWindowProcW(hwnd: HWND, msg: u32, wparam: usize, lparam: isize) -> isize;
    fn DestroyWindow(hwnd: HWND) -> i32;
    fn PostQuitMessage(code: i32);
    fn BeginPaint(hwnd: HWND, paint: *mut PAINTSTRUCT) -> HDC;
    fn EndPaint(hwnd: HWND, paint: *const PAINTSTRUCT) -> i32;
    fn DrawTextW(hdc: HDC, text: *const u16, count: i32, rect: *mut RECT, format: u32) -> i32;
    fn SetTimer(hwnd: HWND, id: usize, elapse: u32, proc: *mut c_void) -> usize;
    fn KillTimer(hwnd: HWND, id: usize) -> i32;
    fn InvalidateRect(hwnd: HWND, rect: *const RECT, erase: i32) -> i32;
    fn SetWindowLongPtrW(hwnd: HWND, index: i32, value: isize) -> isize;
    fn GetWindowLongPtrW(hwnd: HWND, index: i32) -> isize;
    fn GetClientRect(hwnd: HWND, rect: *mut RECT) -> i32;
    fn GetLastInputInfo(info: *mut LASTINPUTINFO) -> i32;
}

#[link(name = "gdi32")]
extern "system" {
    fn SetBkMode(hdc: HDC, mode: i32) -> i32;
}

#[link(name = "kernel32")]
extern "system" {
    fn GetModuleHandleW(name: *const u16) -> HINSTANCE;
    fn OpenProcess(access: u32, inherit: i32, pid: u32) -> *mut c_void;
    fn WaitForSingleObject(handle: *mut c_void, ms: u32) -> u32;
    fn CloseHandle(handle: *mut c_void) -> i32;
}

fn wide(text: &str) -> Vec<u16> {
    text.encode_utf16().chain(std::iter::once(0)).collect()
}

fn stop_child(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

extern "system" fn wnd_proc(hwnd: HWND, msg: u32, wparam: usize, lparam: isize) -> isize {
    unsafe {
        match msg {
            WM_PAINT => {
                let mut paint: PAINTSTRUCT = mem::zeroed();
                let hdc = BeginPaint(hwnd, &mut paint);
                SetBkMode(hdc, TRANSPARENT);
                let mut rect = RECT {
                    left: 16,
                    top: 16,
                    right: 460,
                    bottom: 200,
                };
                GetClientRect(hwnd, &mut rect);
                rect.left = 16;
                rect.top = 16;
                let text = status_text(hwnd);
                let wide_text = wide(&text);
                DrawTextW(
                    hdc,
                    wide_text.as_ptr(),
                    -1,
                    &mut rect,
                    DT_LEFT | DT_TOP,
                );
                EndPaint(hwnd, &paint);
                0
            }
            WM_TIMER => {
                let quit = update_or_quit(hwnd);
                InvalidateRect(hwnd, ptr::null(), 1);
                if quit {
                    DestroyWindow(hwnd);
                }
                0
            }
            WM_COMMAND => {
                if (wparam as u32) & 0xFFFF == ID_STOP as u32 {
                    DestroyWindow(hwnd);
                }
                0
            }
            WM_CLOSE => {
                ShowWindow(hwnd, SW_MINIMIZE);
                0
            }
            WM_DESTROY => {
                KillTimer(hwnd, 1);
                drop_state(hwnd);
                PostQuitMessage(0);
                0
            }
            _ => DefWindowProcW(hwnd, msg, wparam, lparam),
        }
    }
}

fn status_text(hwnd: HWND) -> String {
    unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            return "stay-watch".to_string();
        }
        let state = &*(raw as *const AppState);
        let elapsed = format_elapsed(state.started.elapsed().as_secs());
        format!(
            "stay-watch is running\r\n\r\nkeep-awake.py PID={}\r\nmonitor-helper.py PID={}\r\nidle {}\r\n\r\nKeyboard, mouse, or trackpad input resets idle to 00:00:00.\r\nX minimizes. Use Stop to end the scripts.",
            state.helper_pid, state.monitor_pid, elapsed
        )
    }
}

fn helper_still_running(pid: u32) -> bool {
    unsafe {
        let handle = OpenProcess(0x0010_0000, 0, pid);
        if handle.is_null() {
            return false;
        }
        let wait = WaitForSingleObject(handle, 0);
        CloseHandle(handle);
        wait == 0x0000_0102
    }
}

fn update_or_quit(hwnd: HWND) -> bool {
    unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            return true;
        }
        let state = &mut *(raw as *mut AppState);
        let mut info = LASTINPUTINFO {
            cbSize: mem::size_of::<LASTINPUTINFO>() as u32,
            dwTime: 0,
        };
        if GetLastInputInfo(&mut info) != 0 {
            if should_reset_idle(state.have_input_sample, state.last_input_tick, info.dwTime) {
                state.started = Instant::now();
            }
            state.last_input_tick = info.dwTime;
            state.have_input_sample = true;
        }
        let _ = state.keep.try_wait();
        let _ = state.monitor.try_wait();
        !helper_still_running(state.helper_pid)
    }
}

fn drop_state(hwnd: HWND) {
    unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            return;
        }
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, 0);
        let mut state = Box::from_raw(raw as *mut AppState);
        stop_child(&mut state.monitor);
        stop_child(&mut state.keep);
    }
}

/// Show a small window with PIDs and elapsed time. Close the window to stop.
pub fn run(keep: Child, monitor: Child, helper_pid: u32) -> Result<(), String> {
    let monitor_pid = monitor.id();
    let class = wide("StayWatchStatusWindow");
    let title = wide("stay-watch");
    unsafe {
        let instance = GetModuleHandleW(ptr::null());
        let wndclass = WNDCLASSW {
            style: 3,
            wnd_proc: Some(wnd_proc),
            cls_extra: 0,
            wnd_extra: 0,
            instance,
            icon: ptr::null_mut(),
            cursor: ptr::null_mut(),
            background: (COLOR_WINDOW + 1) as HBRUSH,
            menu_name: ptr::null(),
            class_name: class.as_ptr(),
        };
        RegisterClassW(&wndclass);
        let hwnd = CreateWindowExW(
            0,
            class.as_ptr(),
            title.as_ptr(),
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            480,
            280,
            ptr::null_mut(),
            ptr::null_mut(),
            instance,
            ptr::null_mut(),
        );
        if hwnd.is_null() {
            return Err("Cannot create the stay-watch window.".to_string());
        }
        let btn_class = wide("BUTTON");
        let btn_text = wide("Stop");
        CreateWindowExW(
            0,
            btn_class.as_ptr(),
            btn_text.as_ptr(),
            WS_CHILD | WS_VISIBLE,
            16,
            200,
            88,
            28,
            hwnd,
            ID_STOP as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        let state = Box::new(AppState {
            keep,
            monitor,
            helper_pid,
            monitor_pid,
            started: Instant::now(),
            last_input_tick: 0,
            have_input_sample: false,
        });
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, Box::into_raw(state) as isize);
        SetTimer(hwnd, 1, 1000, ptr::null_mut());
        ShowWindow(hwnd, SW_SHOWNORMAL);
        UpdateWindow(hwnd);
        let mut msg: MSG = mem::zeroed();
        while GetMessageW(&mut msg, ptr::null_mut(), 0, 0) > 0 {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }
    Ok(())
}
