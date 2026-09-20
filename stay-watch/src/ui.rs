//! Native dashboard window for the stay-watch helper session.

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
type HGDIOBJ = *mut c_void;
type HFONT = *mut c_void;
type HPEN = *mut c_void;

const WM_DESTROY: u32 = 0x0002;
const WM_SIZE: u32 = 0x0005;
const WM_CLOSE: u32 = 0x0010;
const WM_ERASEBKGND: u32 = 0x0014;
const WM_GETMINMAXINFO: u32 = 0x0024;
const WM_DRAWITEM: u32 = 0x002B;
const WM_COMMAND: u32 = 0x0111;
const WM_PAINT: u32 = 0x000F;
const WM_TIMER: u32 = 0x0113;
const WS_OVERLAPPEDWINDOW: u32 = 0x00CF_0000;
const WS_VISIBLE: u32 = 0x1000_0000;
const WS_CHILD: u32 = 0x4000_0000;
const WS_TABSTOP: u32 = 0x0001_0000;
const BS_OWNERDRAW: u32 = 0x0000_000B;
const CW_USEDEFAULT: i32 = -2147483648;
const SW_SHOWNORMAL: i32 = 1;
const SW_MINIMIZE: i32 = 6;
const ID_STOP: isize = 1;
const COLOR_WINDOW: i32 = 5;
const GWLP_USERDATA: i32 = -21;
const DT_LEFT: u32 = 0x0000;
const DT_CENTER: u32 = 0x0001;
const DT_RIGHT: u32 = 0x0002;
const DT_VCENTER: u32 = 0x0004;
const DT_SINGLELINE: u32 = 0x0020;
const DT_NOPREFIX: u32 = 0x0800;
const TRANSPARENT: i32 = 1;
const PS_SOLID: i32 = 0;
const FW_NORMAL: i32 = 400;
const FW_SEMIBOLD: i32 = 600;
const FW_BOLD: i32 = 700;
const DEFAULT_CHARSET: u32 = 1;
const OUT_DEFAULT_PRECIS: u32 = 0;
const CLIP_DEFAULT_PRECIS: u32 = 0;
const CLEARTYPE_QUALITY: u32 = 5;
const DEFAULT_PITCH: u32 = 0;
const ODT_BUTTON: u32 = 4;
const ODS_SELECTED: u32 = 0x0001;
const ODS_FOCUS: u32 = 0x0010;
const COLORREF_WHITE: u32 = 0x00FF_FFFF;

#[repr(C)]
struct POINT {
    x: i32,
    y: i32,
}

#[repr(C)]
#[derive(Clone, Copy)]
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
struct MINMAXINFO {
    pt_reserved: POINT,
    pt_max_size: POINT,
    pt_max_position: POINT,
    pt_min_track_size: POINT,
    pt_max_track_size: POINT,
}

#[repr(C)]
struct DRAWITEMSTRUCT {
    ctl_type: u32,
    ctl_id: u32,
    item_id: u32,
    item_action: u32,
    item_state: u32,
    hwnd_item: HWND,
    hdc: HDC,
    rc_item: RECT,
    item_data: usize,
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

#[derive(Clone, Copy)]
struct DashboardLayout {
    helper_card: RECT,
    monitor_card: RECT,
    activity_card: RECT,
    controls_card: RECT,
    stop_button: RECT,
    idle_panel: RECT,
}

struct AppState {
    keep: Child,
    monitor: Child,
    helper_pid: u32,
    monitor_pid: u32,
    started: Instant,
    last_input_tick: u32,
    have_input_sample: bool,
    stop_button: HWND,
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
    fn SetWindowTextW(hwnd: HWND, text: *const u16) -> i32;
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
    fn MoveWindow(hwnd: HWND, x: i32, y: i32, width: i32, height: i32, repaint: i32) -> i32;
    fn GetLastInputInfo(info: *mut LASTINPUTINFO) -> i32;
}

#[link(name = "gdi32")]
extern "system" {
    fn SetBkMode(hdc: HDC, mode: i32) -> i32;
    fn SetTextColor(hdc: HDC, color: u32) -> u32;
    fn CreateSolidBrush(color: u32) -> HBRUSH;
    fn CreatePen(style: i32, width: i32, color: u32) -> HPEN;
    fn CreateFontW(
        height: i32,
        width: i32,
        escapement: i32,
        orientation: i32,
        weight: i32,
        italic: u32,
        underline: u32,
        strike_out: u32,
        charset: u32,
        output_precision: u32,
        clip_precision: u32,
        quality: u32,
        pitch_and_family: u32,
        face: *const u16,
    ) -> HFONT;
    fn SelectObject(hdc: HDC, object: HGDIOBJ) -> HGDIOBJ;
    fn DeleteObject(object: HGDIOBJ) -> i32;
    fn FillRect(hdc: HDC, rect: *const RECT, brush: HBRUSH) -> i32;
    fn RoundRect(hdc: HDC, left: i32, top: i32, right: i32, bottom: i32, width: i32, height: i32)
        -> i32;
    fn Ellipse(hdc: HDC, left: i32, top: i32, right: i32, bottom: i32) -> i32;
    fn MoveToEx(hdc: HDC, x: i32, y: i32, point: *mut POINT) -> i32;
    fn LineTo(hdc: HDC, x: i32, y: i32) -> i32;
    fn FrameRect(hdc: HDC, rect: *const RECT, brush: HBRUSH) -> i32;
}

#[link(name = "kernel32")]
extern "system" {
    fn GetModuleHandleW(name: *const u16) -> HINSTANCE;
    fn OpenProcess(access: u32, inherit: i32, pid: u32) -> *mut c_void;
    fn WaitForSingleObject(handle: *mut c_void, ms: u32) -> u32;
    fn CloseHandle(handle: *mut c_void) -> i32;
}

#[repr(C)]
struct LASTINPUTINFO {
    cbSize: u32,
    dwTime: u32,
}

fn wide(text: &str) -> Vec<u16> {
    text.encode_utf16().chain(std::iter::once(0)).collect()
}

fn rgb(red: u32, green: u32, blue: u32) -> u32 {
    red | (green << 8) | (blue << 16)
}

fn stop_child(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

fn rect(left: i32, top: i32, right: i32, bottom: i32) -> RECT {
    RECT {
        left,
        top,
        right,
        bottom,
    }
}

fn dashboard_layout(client: RECT) -> DashboardLayout {
    let margin = 28;
    let gap = 18;
    let header_height = 84;
    let content_top = header_height + 22;
    let content_bottom = client.bottom - margin;
    let content_width = client.right - margin * 2;
    let column_width = (content_width - gap) / 2;
    let available_height = content_bottom - content_top - gap;
    let top_height = (available_height - 210).max(280);
    let lower_top = content_top + top_height + gap;
    let left = margin;
    let right = margin + column_width;
    let second_left = right + gap;
    let second_right = client.right - margin;
    let lower_bottom = content_bottom;
    let helper_card = rect(left, content_top, right, content_top + top_height);
    let monitor_card = rect(second_left, content_top, second_right, content_top + top_height);
    let activity_card = rect(left, lower_top, right, lower_bottom);
    let controls_card = rect(second_left, lower_top, second_right, lower_bottom);
    let stop_button = rect(
        controls_card.left + 24,
        controls_card.top + 116,
        controls_card.right - 24,
        controls_card.bottom - 24,
    );
    let idle_panel = rect(
        controls_card.left + 24,
        controls_card.top + 24,
        controls_card.right - 24,
        controls_card.top + 90,
    );
    DashboardLayout {
        helper_card,
        monitor_card,
        activity_card,
        controls_card,
        stop_button,
        idle_panel,
    }
}

fn fill_rect(hdc: HDC, area: &RECT, color: u32) {
    unsafe {
        let brush = CreateSolidBrush(color);
        if !brush.is_null() {
            FillRect(hdc, area, brush);
            DeleteObject(brush as HGDIOBJ);
        }
    }
}

fn rounded_box(hdc: HDC, area: &RECT, fill: u32, border: u32, radius: i32) {
    unsafe {
        let brush = CreateSolidBrush(fill);
        let pen = CreatePen(PS_SOLID, 1, border);
        if brush.is_null() || pen.is_null() {
            if !brush.is_null() {
                DeleteObject(brush as HGDIOBJ);
            }
            if !pen.is_null() {
                DeleteObject(pen as HGDIOBJ);
            }
            return;
        }
        let old_brush = SelectObject(hdc, brush as HGDIOBJ);
        let old_pen = SelectObject(hdc, pen as HGDIOBJ);
        RoundRect(
            hdc,
            area.left,
            area.top,
            area.right,
            area.bottom,
            radius,
            radius,
        );
        SelectObject(hdc, old_brush);
        SelectObject(hdc, old_pen);
        DeleteObject(brush as HGDIOBJ);
        DeleteObject(pen as HGDIOBJ);
    }
}

fn draw_text(hdc: HDC, text: &str, area: &RECT, color: u32, size: i32, weight: i32, format: u32) {
    unsafe {
        let face = wide("Segoe UI");
        let font = CreateFontW(
            -size,
            0,
            0,
            0,
            weight,
            0,
            0,
            0,
            DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS,
            CLIP_DEFAULT_PRECIS,
            CLEARTYPE_QUALITY,
            DEFAULT_PITCH,
            face.as_ptr(),
        );
        let mut target = *area;
        let text_value = wide(text);
        let old_font = if font.is_null() {
            ptr::null_mut()
        } else {
            SelectObject(hdc, font as HGDIOBJ)
        };
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, color);
        DrawTextW(
            hdc,
            text_value.as_ptr(),
            -1,
            &mut target,
            format | DT_NOPREFIX,
        );
        if !font.is_null() {
            SelectObject(hdc, old_font);
            DeleteObject(font as HGDIOBJ);
        }
    }
}

fn draw_card_shell(hdc: HDC, area: &RECT) {
    rounded_box(hdc, area, rgb(255, 255, 255), rgb(194, 218, 242), 12);
    let header = rect(area.left + 1, area.top + 1, area.right - 1, area.top + 74);
    fill_rect(hdc, &header, rgb(237, 246, 253));
}

fn draw_process_card(hdc: HDC, area: &RECT, title: &str, pid: u32) {
    draw_card_shell(hdc, area);
    draw_text(
        hdc,
        title,
        &rect(area.left + 24, area.top + 15, area.right - 20, area.top + 60),
        rgb(14, 42, 91),
        27,
        FW_BOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );

    let output = rect(area.left + 22, area.top + 96, area.right - 22, area.bottom - 78);
    rounded_box(hdc, &output, rgb(244, 247, 250), rgb(218, 226, 235), 12);
    let icon = rect(
        (output.left + output.right) / 2 - 29,
        output.top + 72,
        (output.left + output.right) / 2 + 29,
        output.top + 140,
    );
    rounded_box(hdc, &icon, rgb(249, 251, 253), rgb(166, 179, 196), 7);
    unsafe {
        let pen = CreatePen(PS_SOLID, 3, rgb(166, 179, 196));
        if !pen.is_null() {
            let old = SelectObject(hdc, pen as HGDIOBJ);
            MoveToEx(hdc, icon.left + 14, icon.top + 20, ptr::null_mut());
            LineTo(hdc, icon.right - 14, icon.top + 20);
            MoveToEx(hdc, icon.left + 14, icon.top + 34, ptr::null_mut());
            LineTo(hdc, icon.right - 14, icon.top + 34);
            MoveToEx(hdc, icon.left + 14, icon.top + 48, ptr::null_mut());
            LineTo(hdc, icon.right - 24, icon.top + 48);
            SelectObject(hdc, old);
            DeleteObject(pen as HGDIOBJ);
        }
    }
    draw_text(
        hdc,
        "Process output is not displayed",
        &rect(output.left + 16, output.top + 160, output.right - 16, output.top + 202),
        rgb(104, 123, 149),
        18,
        FW_NORMAL,
        DT_CENTER | DT_SINGLELINE | DT_VCENTER,
    );
    draw_text(
        hdc,
        "PID:",
        &rect(area.left + 24, area.bottom - 62, area.left + 86, area.bottom - 28),
        rgb(106, 123, 147),
        21,
        FW_SEMIBOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
    draw_text(
        hdc,
        &pid.to_string(),
        &rect(area.left + 88, area.bottom - 62, area.right - 20, area.bottom - 28),
        rgb(14, 35, 74),
        21,
        FW_SEMIBOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
}

fn draw_activity_card(hdc: HDC, area: &RECT) {
    draw_card_shell(hdc, area);
    draw_text(
        hdc,
        "Activity sources",
        &rect(area.left + 24, area.top + 12, area.right - 20, area.top + 54),
        rgb(14, 42, 91),
        23,
        FW_BOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
    for (index, label) in ["keyboard", "mouse", "touchpad"].iter().enumerate() {
        let top = area.top + 90 + index as i32 * 48;
        unsafe {
            let brush = CreateSolidBrush(rgb(42, 139, 232));
            if !brush.is_null() {
                let old = SelectObject(hdc, brush as HGDIOBJ);
                Ellipse(hdc, area.left + 30, top + 9, area.left + 48, top + 27);
                SelectObject(hdc, old);
                DeleteObject(brush as HGDIOBJ);
            }
        }
        draw_text(
            hdc,
            label,
            &rect(area.left + 70, top, area.right - 20, top + 42),
            rgb(14, 35, 74),
            21,
            FW_NORMAL,
            DT_LEFT | DT_SINGLELINE | DT_VCENTER,
        );
    }
}

fn draw_controls_card(hdc: HDC, area: &RECT, idle_panel: &RECT, idle: &str) {
    rounded_box(hdc, area, rgb(255, 255, 255), rgb(194, 218, 242), 12);
    rounded_box(
        hdc,
        &idle_panel,
        rgb(239, 247, 255),
        rgb(207, 229, 250),
        12,
    );
    draw_text(
        hdc,
        "IDLE:",
        &rect(
            idle_panel.left + 18,
            idle_panel.top + 10,
            idle_panel.left + 126,
            idle_panel.bottom - 10,
        ),
        rgb(77, 94, 118),
        22,
        FW_SEMIBOLD,
        DT_RIGHT | DT_SINGLELINE | DT_VCENTER,
    );
    draw_text(
        hdc,
        idle,
        &rect(
            idle_panel.left + 140,
            idle_panel.top + 5,
            idle_panel.right - 14,
            idle_panel.bottom - 5,
        ),
        rgb(20, 95, 190),
        34,
        FW_BOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
}

fn draw_header(hdc: HDC, client: RECT) {
    fill_rect(hdc, &rect(0, 0, client.right, 84), rgb(246, 250, 254));
    fill_rect(
        hdc,
        &rect(0, 83, client.right, 85),
        rgb(220, 232, 244),
    );
    rounded_box(
        hdc,
        &rect(28, 24, 64, 60),
        rgb(14, 181, 137),
        rgb(14, 181, 137),
        6,
    );
    draw_text(
        hdc,
        "stay-watch - RUNNING",
        &rect(84, 17, client.right - 24, 67),
        rgb(14, 35, 74),
        27,
        FW_BOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
}

fn paint_dashboard(hwnd: HWND, hdc: HDC, client: RECT) {
    fill_rect(hdc, &client, rgb(250, 252, 255));
    draw_header(hdc, client);
    let layout = dashboard_layout(client);
    let (helper_pid, monitor_pid, elapsed) = unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            (0, 0, "00:00:00".to_string())
        } else {
            let state = &*(raw as *const AppState);
            (
                state.helper_pid,
                state.monitor_pid,
                format_elapsed(state.started.elapsed().as_secs()),
            )
        }
    };
    draw_process_card(hdc, &layout.helper_card, "keep-awake.py", helper_pid);
    draw_process_card(hdc, &layout.monitor_card, "monitor-helper.py", monitor_pid);
    draw_activity_card(hdc, &layout.activity_card);
    draw_controls_card(hdc, &layout.controls_card, &layout.idle_panel, &elapsed);
}

fn layout_controls(hwnd: HWND) {
    unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            return;
        }
        let state = &*(raw as *const AppState);
        let mut client: RECT = mem::zeroed();
        GetClientRect(hwnd, &mut client);
        let layout = dashboard_layout(client);
        let area = layout.stop_button;
        MoveWindow(
            state.stop_button,
            area.left,
            area.top,
            area.right - area.left,
            area.bottom - area.top,
            1,
        );
    }
}

fn draw_stop_button(item: &DRAWITEMSTRUCT) {
    let selected = item.item_state & ODS_SELECTED != 0;
    let fill = if selected {
        rgb(24, 105, 190)
    } else {
        rgb(42, 133, 222)
    };
    rounded_box(item.hdc, &item.rc_item, fill, fill, 12);
    let center_y = (item.rc_item.top + item.rc_item.bottom) / 2;
    let icon_left = (item.rc_item.left + item.rc_item.right) / 2 - 58;
    let icon_top = center_y - 10;
    unsafe {
        let brush = CreateSolidBrush(COLORREF_WHITE);
        if !brush.is_null() {
            FillRect(
                item.hdc,
                &rect(icon_left, icon_top, icon_left + 20, icon_top + 20),
                brush,
            );
            DeleteObject(brush as HGDIOBJ);
        }
    }
    draw_text(
        item.hdc,
        "Stop",
        &rect(
            icon_left + 34,
            item.rc_item.top,
            item.rc_item.right - 26,
            item.rc_item.bottom,
        ),
        COLORREF_WHITE,
        25,
        FW_SEMIBOLD,
        DT_LEFT | DT_SINGLELINE | DT_VCENTER,
    );
    if item.item_state & ODS_FOCUS != 0 {
        unsafe {
            let brush = CreateSolidBrush(COLORREF_WHITE);
            if !brush.is_null() {
                FrameRect(
                    item.hdc,
                    &rect(
                        item.rc_item.left + 4,
                        item.rc_item.top + 4,
                        item.rc_item.right - 4,
                        item.rc_item.bottom - 4,
                    ),
                    brush,
                );
                DeleteObject(brush as HGDIOBJ);
            }
        }
    }
}

extern "system" fn wnd_proc(hwnd: HWND, msg: u32, wparam: usize, lparam: isize) -> isize {
    unsafe {
        match msg {
            WM_GETMINMAXINFO => {
                let info = &mut *(lparam as *mut MINMAXINFO);
                info.pt_min_track_size.x = 800;
                info.pt_min_track_size.y = 640;
                0
            }
            WM_PAINT => {
                let mut paint: PAINTSTRUCT = mem::zeroed();
                let hdc = BeginPaint(hwnd, &mut paint);
                let mut client: RECT = mem::zeroed();
                GetClientRect(hwnd, &mut client);
                paint_dashboard(hwnd, hdc, client);
                EndPaint(hwnd, &paint);
                0
            }
            WM_ERASEBKGND => 1,
            WM_SIZE => {
                layout_controls(hwnd);
                InvalidateRect(hwnd, ptr::null(), 0);
                0
            }
            WM_TIMER => {
                let quit = update_or_quit(hwnd);
                InvalidateRect(hwnd, ptr::null(), 0);
                if quit {
                    DestroyWindow(hwnd);
                }
                0
            }
            WM_DRAWITEM => {
                if wparam as isize == ID_STOP && lparam != 0 {
                    let item = &*(lparam as *const DRAWITEMSTRUCT);
                    if item.ctl_type == ODT_BUTTON {
                        draw_stop_button(item);
                        return 1;
                    }
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

/// Show the dashboard and preserve the existing helper lifecycle.
pub fn run(keep: Child, monitor: Child, helper_pid: u32) -> Result<(), String> {
    let monitor_pid = monitor.id();
    let class = wide("StayWatchStatusWindow");
    let title = wide("stay-watch - RUNNING");
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
            960,
            720,
            ptr::null_mut(),
            ptr::null_mut(),
            instance,
            ptr::null_mut(),
        );
        if hwnd.is_null() {
            return Err("Cannot create the stay-watch window.".to_string());
        }
        SetWindowTextW(hwnd, title.as_ptr());
        let btn_class = wide("BUTTON");
        let btn_text = wide("");
        let stop_button = CreateWindowExW(
            0,
            btn_class.as_ptr(),
            btn_text.as_ptr(),
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_OWNERDRAW,
            0,
            0,
            10,
            10,
            hwnd,
            ID_STOP as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        if stop_button.is_null() {
            DestroyWindow(hwnd);
            return Err("Cannot create the Stop button.".to_string());
        }
        let state = Box::new(AppState {
            keep,
            monitor,
            helper_pid,
            monitor_pid,
            started: Instant::now(),
            last_input_tick: 0,
            have_input_sample: false,
            stop_button,
        });
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, Box::into_raw(state) as isize);
        layout_controls(hwnd);
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
