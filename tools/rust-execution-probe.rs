#![allow(non_snake_case)]

#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentProcessId() -> u32;
    fn GetConsoleWindow() -> *mut core::ffi::c_void;
}

fn main() {
    let (pid, console_hwnd) = unsafe { (GetCurrentProcessId(), GetConsoleWindow()) };
    println!("RUST_EXECUTION_PROBE_OK pid={} console_hwnd={}", pid, console_hwnd as usize);
}
