//! Native dashboard window for the stay-watch helper session.

#![allow(non_snake_case)]

use std::ffi::c_void;
use std::mem;
use std::process::Child;
use std::ptr;
use std::time::Instant;

use crate::output::{Views, LIMIT};
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
const WM_HSCROLL: u32 = 0x0114;
const WM_VSCROLL: u32 = 0x0115;
const WM_SETFONT: u32 = 0x0030;
const EM_GETSEL: u32 = 0x00B0;
const EM_SETSEL: u32 = 0x00B1;
const EM_SETLIMITTEXT: u32 = 0x00C5;
const EM_LINESCROLL: u32 = 0x00B6;
const EM_SCROLLCARET: u32 = 0x00B7;
const EM_GETFIRSTVISIBLELINE: u32 = 0x00CE;
const TBM_GETPOS: u32 = 0x0400;
const TBM_SETPOS: u32 = 0x0405;
const TBM_SETRANGE: u32 = 0x0406;
const WS_OVERLAPPEDWINDOW: u32 = 0x00CF_0000;
const WS_CLIPCHILDREN: u32 = 0x0200_0000;
const WS_VISIBLE: u32 = 0x1000_0000;
const WS_CHILD: u32 = 0x4000_0000;
const WS_TABSTOP: u32 = 0x0001_0000;
const WS_VSCROLL: u32 = 0x0020_0000;
const WS_HSCROLL: u32 = 0x0010_0000;
const WS_EX_CLIENTEDGE: u32 = 0x0000_0200;
const ES_MULTILINE: u32 = 0x0004;
const ES_AUTOHSCROLL: u32 = 0x0080;
const ES_AUTOVSCROLL: u32 = 0x0040;
const ES_NOHIDESEL: u32 = 0x0100;
const ES_READONLY: u32 = 0x0800;
const ES_WANTRETURN: u32 = 0x1000;
const TBS_VERT: u32 = 0x0002;
const TBS_NOTICKS: u32 = 0x0010;
const SS_CENTER: u32 = 0x0001;
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
const ICC_BAR_CLASSES: u32 = 0x0000_0004;

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
struct INITCOMMONCONTROLSEX {
    size: u32,
    classes: u32,
}

#[repr(C)]
struct SCROLLINFO {
    cbSize: u32,
    fMask: u32,
    nMin: i32,
    nMax: i32,
    nPage: u32,
    nPos: i32,
    nTrackPos: i32,
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
    helper_output: RECT,
    monitor_output: RECT,
    splitter: RECT,
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
    helper_output: HWND,
    monitor_output: HWND,
    splitter: HWND,
    splitter_label: HWND,
    split_percent: i32,
    views: Views,
    helper_text: String,
    monitor_text: String,
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
    fn SendMessageW(hwnd: HWND, msg: u32, wparam: usize, lparam: isize) -> isize;
    fn ShowWindow(hwnd: HWND, cmd: i32) -> i32;
    fn UpdateWindow(hwnd: HWND) -> i32;
    fn GetMessageW(msg: *mut MSG, hwnd: HWND, min: u32, max: u32) -> i32;
    fn TranslateMessage(msg: *const MSG) -> i32;
    fn IsDialogMessageW(hwnd: HWND, msg: *mut MSG) -> i32;
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
    fn GetScrollInfo(hwnd: HWND, bar: i32, info: *mut SCROLLINFO) -> i32;
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
    fn FrameRect(hdc: HDC, rect: *const RECT, brush: HBRUSH) -> i32;
    fn GetStockObject(index: i32) -> HGDIOBJ;
}

#[link(name = "comctl32")]
extern "system" {
    fn InitCommonControlsEx(init: *const INITCOMMONCONTROLSEX) -> i32;
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

fn dashboard_layout(client: RECT, split_percent: i32) -> DashboardLayout {
    let margin = 24;
    let gap = 12;
    let content_top = 106;
    let content_bottom = (client.bottom - margin).max(content_top + 180);
    let content_width = (client.right - margin * 2).max(2);
    let lower_height = 190;
    let lower_top = (content_bottom - lower_height - gap).max(content_top + 170);
    let pane_bottom = (lower_top - gap).max(content_top + 120);
    let splitter_width = 28;
    let pane_width = (content_width - splitter_width).max(2);
    let split = split_percent.clamp(25, 75);
    let left_width = (pane_width * split / 100).max(1);
    let left = margin;
    let right = left + left_width;
    let splitter_left = right;
    let second_left = splitter_left + splitter_width;
    let second_right = client.right - margin;
    let helper_card = rect(left, content_top, right, pane_bottom);
    let monitor_card = rect(second_left, content_top, second_right, pane_bottom);
    let lower_column_width = (content_width - gap) / 2;
    let lower_left = margin;
    let lower_right = lower_left + lower_column_width;
    let lower_second_left = lower_right + gap;
    let activity_card = rect(lower_left, lower_top, lower_right, content_bottom);
    let controls_card = rect(lower_second_left, lower_top, second_right, content_bottom);
    let stop_button = rect(
        controls_card.left + 24,
        controls_card.top + 104,
        controls_card.right - 24,
        controls_card.bottom - 24,
    );
    let idle_panel = rect(
        controls_card.left + 24,
        controls_card.top + 24,
        controls_card.right - 24,
        controls_card.top + 82,
    );
    let helper_output = rect(helper_card.left + 18, helper_card.top + 78, helper_card.right - 18, helper_card.bottom - 78);
    let monitor_output = rect(monitor_card.left + 18, monitor_card.top + 78, monitor_card.right - 18, monitor_card.bottom - 78);
    let splitter = rect(splitter_left, content_top, second_left, pane_bottom);
    DashboardLayout {
        helper_card,
        monitor_card,
        activity_card,
        controls_card,
        stop_button,
        idle_panel,
        helper_output,
        monitor_output,
        splitter,
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
        let top = area.top + 66 + index as i32 * 34;
        unsafe {
            let brush = CreateSolidBrush(rgb(42, 139, 232));
            if !brush.is_null() {
                let old = SelectObject(hdc, brush as HGDIOBJ);
                Ellipse(hdc, area.left + 30, top + 6, area.left + 46, top + 22);
                SelectObject(hdc, old);
                DeleteObject(brush as HGDIOBJ);
            }
        }
        draw_text(
            hdc,
            label,
            &rect(area.left + 64, top, area.right - 20, top + 30),
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
    let (helper_pid, monitor_pid, elapsed, split_percent) = unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            (0, 0, "00:00:00".to_string(), 50)
        } else {
            let state = &*(raw as *const AppState);
            (
                state.helper_pid,
                state.monitor_pid,
                format_elapsed(state.started.elapsed().as_secs()),
                state.split_percent,
            )
        }
    };
    let layout = dashboard_layout(client, split_percent);
    draw_process_card(hdc, &layout.helper_card, "keep-awake.py", helper_pid);
    draw_process_card(hdc, &layout.monitor_card, "monitor-helper.py", monitor_pid);
    fill_rect(hdc, &layout.splitter, rgb(234, 241, 248));
    draw_text(
        hdc,
        "Split",
        &rect(layout.splitter.left, layout.splitter.top, layout.splitter.right, layout.splitter.top + 22),
        rgb(77, 94, 118),
        11,
        FW_SEMIBOLD,
        DT_CENTER | DT_SINGLELINE | DT_VCENTER,
    );
    draw_activity_card(hdc, &layout.activity_card);
    draw_controls_card(hdc, &layout.controls_card, &layout.idle_panel, &elapsed);
}

fn scroll_at_bottom(hwnd: HWND) -> bool {
    unsafe {
        let mut info = SCROLLINFO {
            cbSize: mem::size_of::<SCROLLINFO>() as u32,
            fMask: 0x0017,
            nMin: 0,
            nMax: 0,
            nPage: 0,
            nPos: 0,
            nTrackPos: 0,
        };
        if GetScrollInfo(hwnd, 1, &mut info) == 0 {
            return true;
        }
        info.nPos.saturating_add(info.nPage as i32) >= info.nMax.saturating_sub(1)
    }
}

fn update_edit(hwnd: HWND, next: &str, previous: &mut String) {
    unsafe {
        if *previous == next {
            return;
        }
        let mut selection_start = 0u32;
        let mut selection_end = 0u32;
        SendMessageW(
            hwnd,
            EM_GETSEL,
            &mut selection_start as *mut u32 as usize,
            &mut selection_end as *mut u32 as isize,
        );
        let has_selection = selection_start != selection_end;
        if has_selection && !next.starts_with(previous.as_str()) {
            // A bounded tail may have discarded the selected prefix. Keep the
            // user's selected text stable until the selection is cleared.
            return;
        }
        let first_line = SendMessageW(hwnd, EM_GETFIRSTVISIBLELINE, 0, 0) as i32;
        let follow_tail = !has_selection && (previous.is_empty() || scroll_at_bottom(hwnd));
        let next_wide = wide(next);
        let next_len = next_wide.len().saturating_sub(1) as u32;
        SetWindowTextW(hwnd, next_wide.as_ptr());
        let caret = if follow_tail {
            next_len
        } else {
            selection_start.min(next_len)
        };
        let end = if has_selection {
            selection_end.min(next_len)
        } else {
            caret
        };
        SendMessageW(hwnd, EM_SETSEL, caret as usize, end as isize);
        if follow_tail {
            SendMessageW(hwnd, EM_SCROLLCARET, 0, 0);
        } else if first_line > 0 {
            SendMessageW(hwnd, EM_LINESCROLL, 0, first_line as isize);
        }
        *previous = next.to_string();
    }
}

fn refresh_outputs(hwnd: HWND) {
    unsafe {
        let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
        if raw == 0 {
            return;
        }
        let state = &mut *(raw as *mut AppState);
        let helper = state.views.helper_text();
        let monitor = format!(
            "Shared log / history (includes other runs)\r\nPath: {}\r\n\r\n{}",
            state.views.log_path.display(),
            state.views.monitor_text()
        );
        update_edit(state.helper_output, &helper, &mut state.helper_text);
        update_edit(state.monitor_output, &monitor, &mut state.monitor_text);
    }
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
        let layout = dashboard_layout(client, state.split_percent);
        let area = layout.stop_button;
        MoveWindow(
            state.stop_button,
            area.left,
            area.top,
            area.right - area.left,
            area.bottom - area.top,
            1,
        );
        MoveWindow(
            state.helper_output,
            layout.helper_output.left,
            layout.helper_output.top,
            layout.helper_output.right - layout.helper_output.left,
            layout.helper_output.bottom - layout.helper_output.top,
            1,
        );
        MoveWindow(
            state.monitor_output,
            layout.monitor_output.left,
            layout.monitor_output.top,
            layout.monitor_output.right - layout.monitor_output.left,
            layout.monitor_output.bottom - layout.monitor_output.top,
            1,
        );
        MoveWindow(
            state.splitter_label,
            layout.splitter.left,
            layout.splitter.top,
            layout.splitter.right - layout.splitter.left,
            22,
            1,
        );
        MoveWindow(
            state.splitter,
            layout.splitter.left,
            layout.splitter.top + 20,
            layout.splitter.right - layout.splitter.left,
            (layout.splitter.bottom - layout.splitter.top - 20).max(1),
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
                refresh_outputs(hwnd);
                InvalidateRect(hwnd, ptr::null(), 0);
                if quit {
                    DestroyWindow(hwnd);
                }
                0
            }
            WM_VSCROLL | WM_HSCROLL => {
                let raw = GetWindowLongPtrW(hwnd, GWLP_USERDATA);
                if raw != 0 && lparam as HWND == (*(raw as *mut AppState)).splitter {
                    let state = &mut *(raw as *mut AppState);
                    state.split_percent = SendMessageW(state.splitter, TBM_GETPOS, 0, 0) as i32;
                    state.split_percent = state.split_percent.clamp(25, 75);
                    layout_controls(hwnd);
                    InvalidateRect(hwnd, ptr::null(), 0);
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
pub fn run(mut keep: Child, mut monitor: Child, helper_pid: u32, views: Views) -> Result<(), String> {
    let monitor_pid = monitor.id();
    let class = wide("StayWatchStatusWindow");
    let title = wide("stay-watch - RUNNING");
    unsafe {
        let common_controls = INITCOMMONCONTROLSEX {
            size: mem::size_of::<INITCOMMONCONTROLSEX>() as u32,
            classes: ICC_BAR_CLASSES,
        };
        InitCommonControlsEx(&common_controls);
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
            WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN | WS_VISIBLE,
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
            stop_child(&mut monitor);
            stop_child(&mut keep);
            return Err("Cannot create the stay-watch window.".to_string());
        }
        SetWindowTextW(hwnd, title.as_ptr());
        let btn_class = wide("BUTTON");
        let btn_text = wide("Stop");
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
            stop_child(&mut monitor);
            stop_child(&mut keep);
            return Err("Cannot create the Stop button.".to_string());
        }
        let edit_class = wide("EDIT");
        let edit_style = WS_CHILD
            | WS_VISIBLE
            | WS_TABSTOP
            | WS_VSCROLL
            | WS_HSCROLL
            | ES_MULTILINE
            | ES_AUTOHSCROLL
            | ES_AUTOVSCROLL
            | ES_NOHIDESEL
            | ES_READONLY
            | ES_WANTRETURN;
        let helper_output = CreateWindowExW(
            WS_EX_CLIENTEDGE,
            edit_class.as_ptr(),
            wide("").as_ptr(),
            edit_style,
            0,
            0,
            10,
            10,
            hwnd,
            2usize as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        let monitor_output = CreateWindowExW(
            WS_EX_CLIENTEDGE,
            edit_class.as_ptr(),
            wide("").as_ptr(),
            edit_style,
            0,
            0,
            10,
            10,
            hwnd,
            3usize as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        let static_class = wide("STATIC");
        let splitter_label = CreateWindowExW(
            0,
            static_class.as_ptr(),
            wide("Split").as_ptr(),
            WS_CHILD | WS_VISIBLE | SS_CENTER,
            0,
            0,
            10,
            10,
            hwnd,
            5usize as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        let track_class = wide("msctls_trackbar32");
        let splitter = CreateWindowExW(
            0,
            track_class.as_ptr(),
            wide("Pane split").as_ptr(),
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | TBS_VERT | TBS_NOTICKS,
            0,
            0,
            10,
            10,
            hwnd,
            4usize as *mut c_void,
            instance,
            ptr::null_mut(),
        );
        if helper_output.is_null()
            || monitor_output.is_null()
            || splitter_label.is_null()
            || splitter.is_null()
        {
            DestroyWindow(hwnd);
            stop_child(&mut monitor);
            stop_child(&mut keep);
            return Err("Cannot create the native output controls.".to_string());
        }
        let gui_font = GetStockObject(17) as usize;
        SendMessageW(helper_output, WM_SETFONT, gui_font, 1);
        SendMessageW(monitor_output, WM_SETFONT, gui_font, 1);
        let edit_limit = (LIMIT * 3 + 4096) as usize;
        SendMessageW(helper_output, EM_SETLIMITTEXT, edit_limit, 0);
        SendMessageW(monitor_output, EM_SETLIMITTEXT, edit_limit, 0);
        SendMessageW(splitter_label, WM_SETFONT, gui_font, 1);
        SendMessageW(splitter, TBM_SETRANGE, 1, ((75u32 << 16) | 25) as isize);
        SendMessageW(splitter, TBM_SETPOS, 1, 50);
        let state = Box::new(AppState {
            keep,
            monitor,
            helper_pid,
            monitor_pid,
            started: Instant::now(),
            last_input_tick: 0,
            have_input_sample: false,
            stop_button,
            helper_output,
            monitor_output,
            splitter,
            splitter_label,
            split_percent: 50,
            views,
            helper_text: String::new(),
            monitor_text: String::new(),
        });
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, Box::into_raw(state) as isize);
        layout_controls(hwnd);
        refresh_outputs(hwnd);
        SetTimer(hwnd, 1, 1000, ptr::null_mut());
        ShowWindow(hwnd, SW_SHOWNORMAL);
        UpdateWindow(hwnd);
        let mut msg: MSG = mem::zeroed();
        while GetMessageW(&mut msg, ptr::null_mut(), 0, 0) > 0 {
            if IsDialogMessageW(hwnd, &mut msg) == 0 {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn inside(area: RECT, client: RECT) -> bool {
        area.left >= client.left
            && area.top >= client.top
            && area.right <= client.right
            && area.bottom <= client.bottom
            && area.right >= area.left
            && area.bottom >= area.top
    }

    #[test]
    fn dashboard_cards_and_controls_stay_inside_client_at_split_limits() {
        let client = rect(0, 0, 960, 720);
        for split in [25, 50, 75] {
            let layout = dashboard_layout(client, split);
            assert!(inside(layout.helper_card, client));
            assert!(inside(layout.monitor_card, client));
            assert!(inside(layout.activity_card, client));
            assert!(inside(layout.controls_card, client));
            assert!(inside(layout.stop_button, client));
            assert!(inside(layout.helper_output, layout.helper_card));
            assert!(inside(layout.monitor_output, layout.monitor_card));
        }
    }

    #[test]
    fn dashboard_split_is_clamped_to_readable_columns() {
        let client = rect(0, 0, 800, 640);
        let narrow = dashboard_layout(client, -100);
        let wide = dashboard_layout(client, 1000);
        assert!(narrow.helper_card.right - narrow.helper_card.left >= 180);
        assert!(narrow.monitor_card.right - narrow.monitor_card.left >= 180);
        assert!(wide.helper_card.right - wide.helper_card.left >= 180);
        assert!(wide.monitor_card.right - wide.monitor_card.left >= 180);
    }
}
