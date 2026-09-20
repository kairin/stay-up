# stay-watch feasibility gate

Checked: 2026-09-20 (local time). This record separates current application
results from historical probes.

## Current scope

The [visual plan](visual-refresh-plan.md) controls current work. Screenshot
logging and capture resources are removed from scope. Historical capture
results remain evidence only. They do not pass current application checks and
are not visual-refresh blockers.

The current application has an owned-child path. Startup, concurrent commands,
timed exit, Stop, and cleanup passed. These checks do not establish input,
lock, sleep, power, or idle behavior.

## Historical probe record

Completed work included Rust and Win32 execution, terminal discovery, Raw Input
registration, device enumeration, AC status, and S0 Low Power Idle reporting.
Historical `PrintWindow` and screen-region tests also completed before capture
left the project scope.

These results remain unknown:

- live `WM_INPUT` coverage.
- lock and return behavior.
- sleep or Modern Standby runtime.
- power-source transitions.
- broader observer behavior beyond the current launcher.

## Verify recorded evidence

```powershell
python -B -m unittest tools.test_feasibility_probes -v
```

The last re-check ran 14 tests and returned `OK` with exit code zero. It
checked recorded files and did not open a capture window.

## Results

| Check | Result | Evidence and limit |
|---|---|---|
| Rust installation | PASS | Rustup 1.29.1 runs under `%LOCALAPPDATA%\Programs\Rust`. The toolchain is `stable-x86_64-pc-windows-gnu`. |
| Rust build and execution | PASS | rustc and Cargo 1.98.1 ran. The installation binary emitted `RUST_EXECUTION_PROBE_OK`. The state binary emitted `RUST_STATE_PROBE_OK`. Both used fresh output directories. |
| Terminal discovery | PASS | The probe found a visible, non-minimized, uncloaked `WindowsTerminal.exe`. Handles and process IDs are temporary. |
| Historical capture | PARTIAL | `PrintWindow` and screen-region `BitBlt` saved marker images. Other capture paths were not tested before capture left scope. |
| Input and state APIs | PARTIAL | Input, power, and device-list APIs ran. Registration succeeded. No lock, return, suspend, or power-source change occurred. |
| Modern Standby | PARTIAL | `powercfg /a` reported S0 Low Power Idle. No sleep or resume occurred. |
| Raw Input | PARTIAL | Lists included keyboard, mouse, and touchpad collections. No live event arrived during 25 seconds. |
| Current launcher cleanup | PASS | Root-launch checks confirmed owned-process cleanup. This does not prove the historical observer design. |

## Rust paths

| Setting | Value |
|---|---|
| `CARGO_HOME` | `%LOCALAPPDATA%\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `%LOCALAPPDATA%\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `%LOCALAPPDATA%\Rust\target` |
| User PATH entry | `%LOCALAPPDATA%\Programs\Rust\cargo\bin` |

Earlier AppLocker evidence showed an allow rule for
`%OSDRIVE%\Users\*\AppData\Local\*`. The corrected installation runs
without a policy change. The previous `%USERPROFILE%\.cargo` and
`%USERPROFILE%\.rustup` directories are absent.

Use the [required procedure](rust-environment-verification.md) for a new
installation check. A cached build is not new evidence.

## Decision

Rust installation, compilation, build-script execution, linking, native
execution, launcher startup, and owned-child cleanup passed. Input, lock, sleep,
power-transition, and broader observer checks remain separate and incomplete.
