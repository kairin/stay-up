# stay-watch feasibility gate

Checked: 2026-09-20 (Asia/Singapore). Current results below separate verified changes from prior static observations.

## Results

| Check | Result | Evidence and limit |
|---|---|---|
| Rustup installation | PASS | Removed the previous `.cargo` and `.rustup` directories and reinstalled Rustup 1.29.1 under `C:\Users\W106036\AppData\Local\Programs\Rust`. The active toolchain is `stable-x86_64-pc-windows-gnu`. User environment settings and PATH are configured as listed below. |
| Rust compilation/execution | PASS | `rustc 1.98.1` and `cargo 1.98.1` run. An offline Cargo build executed its build script and compiled the [Win32 probe](../tools/rust-execution-probe.rs). The executable printed `RUST_EXECUTION_PROBE_OK`. Each verification run must use a fresh output directory under `CARGO_TARGET_DIR`. See the [required procedure](rust-environment-verification.md). |
| Terminal target discovery | CANDIDATE FOUND | A normal-user `EnumWindows` probe found visible, non-minimized, uncloaked `WindowsTerminal.exe`: HWND 591284, PID 15928, rect `[148,0,1236,678]`. These are ephemeral observations, never fixed settings. See [tools/terminal-target-probe.py](../tools/terminal-target-probe.py). |
| Capture target / observer visibility | UNKNOWN | Discovery is viable, but active-tab ownership, observer visibility, freshness, and capture support remain untested. Earlier `GetConsoleWindow`/`MainWindowHandle` failures were launch-context evidence, not proof that no visible target existed. See [GetConsoleWindow documentation](https://learn.microsoft.com/en-us/windows/console/getconsolewindow). |
| Capture backend | UNKNOWN | No screenshot or capture session was run. Test [Windows Graphics Capture CreateForWindow](https://learn.microsoft.com/en-us/windows/win32/api/windows.graphics.capture.interop/nf-windows-graphics-capture-interop-igraphicscaptureiteminterop-createforwindow) with a verified marker, freshness check, and initial-image rejection. |
| Windows input/state APIs | PRIOR STATIC OBSERVATION | Earlier API-presence checks recorded `RegisterRawInputDevices`, `GetRawInputData`, `GetLastInputInfo`, `RegisterPowerSettingNotification`, `PowerCreateRequest`, and `PowerSetRequest`; registration, device coverage, and a Rust event loop were not retested today. |
| Modern Standby | PRIOR STATIC OBSERVATION | Earlier `powercfg /a` output reported S0 low power idle with network connection and hibernate; runtime behavior was not retested today. |
| Raw Input device coverage | UNKNOWN | Keyboard, external mouse, and touchpad coverage still require an observer and real-device validation. |
| Owned-child cleanup | UNKNOWN / LATER | No Rust observer or owned-child path exists. Keep this later than baseline/manual-helper validation. See [tools/rust-execution-probe.rs](../tools/rust-execution-probe.rs) for the separate compile proof source. |

## Decision

The Rust installation, compilation, build-script execution, and native executable checks pass. The broader feasibility gate is still incomplete: capture, observer visibility, and runtime observations remain untested. This installation check alone does not complete `t_cc724421`. Owned-child cleanup is not part of this gate. It belongs to the later helper-launch milestone.

## Rust paths and verification

The earlier AppLocker check identified an allow rule named `%OSDRIVE%\Users\*\AppData\Local\*`. The old Rust installation was outside that location. The corrected installation and its generated executables run without a policy change.

| User setting | Value |
|---|---|
| `CARGO_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `C:\Users\W106036\AppData\Local\Rust\target` |
| User PATH entry | `C:\Users\W106036\AppData\Local\Programs\Rust\cargo\bin` |

These [Cargo settings](https://doc.rust-lang.org/cargo/reference/environment-variables.html) and [Rustup setting](https://rust-lang.github.io/rustup/environment-variables.html) are saved in the user environment. Cargo's output directory is a user-wide default. Restart existing terminals to load the new settings.

The first installation check used an ignored local fixture. The reusable [repository fixture](../tools/rust-install-check/Cargo.toml) now uses the same [Win32 source](../tools/rust-execution-probe.rs). Follow the [required verification procedure](rust-environment-verification.md) for a fresh output directory and complete pass criteria:

```powershell
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml
```

It printed `RUST_BUILD_SCRIPT_EXECUTION_OK` during the build and `RUST_EXECUTION_PROBE_OK` when the program ran. The default Cargo output executable is `C:\Users\W106036\AppData\Local\Rust\target\debug\stay-up-rust-install-check.exe`. A verification run must still use a fresh directory as specified in the procedure. The dated repository check is in the [observation log](observations.md).

Final checks confirmed that the previous `C:\Users\W106036\.cargo` and `C:\Users\W106036\.rustup` directories are absent, the saved environment values match the new locations, and the new Cargo bin directory occurs once in user PATH.

## Next actions

1. Use small native observer probes to validate input, lock, suspend, and power observations.
2. Run `python -B tools\terminal-target-probe.py` in a normal visible Windows Terminal, then a separately invoked capture feasibility test against the live target. Verify observer content and freshness, including initial-image rejection. No screenshot test has run here.
3. Keep owned-child launching and cleanup for the later milestone after baseline/manual-helper validation.
