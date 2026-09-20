# stay-watch feasibility gate

Checked: 2026-09-20 (Asia/Singapore). Results below separate verified changes from prior static observations.

## Current scope update

The [visual-refresh plan](visual-refresh-plan.md) controls current work.
Screenshot logging is removed from scope. Windows Graphics Capture and observer-tab return are no longer required deliverables.
Their earlier unknown results remain unknown, not passed.
The capture gates below describe the older observer proposal, not prerequisites for a visual refresh.
Other observer runtime checks remain separate from the working launcher.
The board was not updated during this planning task. Historical gate statements below are not a fresh board-status check.
The launcher now has an owned-child path. Its broader cleanup guarantees remain unverified by these historical probes.

The later [agent build check](observations.md#20-september-2026-cargo-build-access-from-an-agent) separates working Rust builds from Codex sandbox file access.
Repeated builds in a stable approved directory passed outside the sandbox. The same directory did not pass sandbox access checks.
This result does not change the historical observer results below.

The later [root-launch checks](observations.md#20-september-2026-root-launch-command-and-owned-process-checks) passed for the current application.
They cover startup, concurrent commands, timed exit, and the existing Stop action with owned-process cleanup.
They do not complete the historical observer, input-device, lock, or sleep checks.

## Historical probe record

## Completed

- Rust installation and a fresh Win32 execution probe.
- Terminal window discovery.
- Explicit `PrintWindow` and screen-region capture of a dedicated Windows Terminal window.
- Marker visibility, freshness, initial-image rejection, scroll-away, minimization, and tab-away.
- Raw Input registration and device lists, including `ELAN07FF` touchpad collections.
- Current AC power source and S0 Low Power Idle capability.

## Outstanding

- Live `WM_INPUT` events.
- Lock cycle and sleep or Modern Standby runtime.
- Windows Graphics Capture `CreateForWindow`.
- Return to the observer tab.
- The stay-watch application.
- Owned-child cleanup, after baseline and manual-helper validation.

Gate `t_cc724421` stays blocked while required outstanding checks remain unknown.

## Verify

From PowerShell in `D:\Apps\stay-up`:

```powershell
python -B -m unittest tools.test_feasibility_probes -v
```

The suite checks recorded PNG files, JSON reports, terminal enumeration, and `rust-state-probe.exe`.
It does not open a capture window.
Pass when the command prints `OK` and exit status is zero.
Last silent re-check: 20 September 2026, 14:21 Singapore time, 14 tests passed.

## Results

| Check | Result | Evidence and limit |
|---|---|---|
| Rustup installation | PASS | Removed the previous `.cargo` and `.rustup` directories and reinstalled Rustup 1.29.1 under `C:\Users\W106036\AppData\Local\Programs\Rust`. The active toolchain is `stable-x86_64-pc-windows-gnu`. User environment settings and PATH are configured as listed below. |
| Rust compilation/execution | PASS | `rustc 1.98.1` and `cargo 1.98.1` run. An offline Cargo build executed its build script and compiled the [Win32 probe](../tools/rust-execution-probe.rs). The executable printed `RUST_EXECUTION_PROBE_OK`. On 20 September 2026 the [state probe](../tools/rust-state-probe.rs) compiled under `CARGO_TARGET_DIR` in directory `feasibility-20260920-1336` as `rust-state-probe.exe` and printed `RUST_STATE_PROBE_OK`. Each verification run must use a fresh output directory under `CARGO_TARGET_DIR`. See the [required procedure](rust-environment-verification.md). |
| Terminal target discovery | PASS | `python -B tools\terminal-target-probe.py` found a visible, non-minimized, uncloaked `WindowsTerminal.exe`. A dedicated probe window titled `STAYUP-CAP-3e918444` was also created and captured. HWND and PID values are ephemeral. See [tools/terminal-target-probe.py](../tools/terminal-target-probe.py). |
| Capture target / observer visibility | PARTIAL | An explicit capture test saved images of a dedicated Windows Terminal window, including the title bar and tab strip. A unique color marker was present after draw, absent before draw, replaced on the second draw, absent after scroll-away, and absent when minimized. A second tab without the marker was captured while the observer tab remained in the same window. Return to the observer tab was not tested. See `local/stay-watch/feasibility-20260920-1345/`. |
| Capture backend | PARTIAL | `PrintWindow` with `PW_RENDERFULLCONTENT` and screen-region `BitBlt` both saved verified marker images. Windows Graphics Capture `CreateForWindow` was not invoked. |
| Windows input/state APIs | PARTIAL | Python and Rust probes called `GetLastInputInfo`, `GetSystemPowerStatus`, and `GetRawInputDeviceList`. Raw Input registration succeeded for keyboard, mouse, and touchpad usage pages. Power and session notification registration succeeded. Current AC line was `ac`. Display notification data was `1` (on) after registration. No lock, session return, suspend, or power-source change occurred during the probe. `WTSSessionInfoEx` flags are not treated as a lock result. |
| Modern Standby | PARTIAL | `powercfg /a` reports `Standby (S0 Low Power Idle) Network Connected` as available. No sleep or resume was requested or observed. |
| Raw Input device coverage | PARTIAL | Device lists included keyboard collections, mouse collections, and `ELAN07FF` touchpad collections. No live `WM_INPUT` events arrived in a 25-second listen. Event coverage remains unknown. Input was not simulated. |
| Owned-child cleanup | UNKNOWN / LATER | No Rust observer or owned-child path exists. Keep this later than baseline/manual-helper validation. See [tools/rust-execution-probe.rs](../tools/rust-execution-probe.rs) for the separate compile proof source. |

## Decision

The Rust installation, compilation, build-script execution, and native executable checks pass.
PrintWindow and screen-region capture passed an explicit marker test on a dedicated Windows Terminal window.
The feasibility gate is still incomplete.
Live Raw Input events, lock and sleep transitions, Modern Standby runtime, Windows Graphics Capture, and return to the observer tab remain untested.
This work does not complete `t_cc724421`.
Owned-child cleanup is not part of this gate.

## Rust paths and verification

The earlier AppLocker check identified an allow rule named `%OSDRIVE%\Users\*\AppData\Local\*`. The old Rust installation was outside that location. The corrected installation and its generated executables run without a policy change.

| User setting | Value |
|---|---|
| `CARGO_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `C:\Users\W106036\AppData\Local\Rust\target` |
| User PATH entry | `C:\Users\W106036\AppData\Local\Programs\Rust\cargo\bin` |

These [Cargo settings](https://doc.rust-lang.org/cargo/reference/environment-variables.html) and [Rustup setting](https://rust-lang.github.io/rustup/environment-variables.html) are saved in the user environment. Cargo's output directory is a user-wide default. Restart existing terminals to load the new settings.

The first installation check used an ignored local fixture. The reusable [repository fixture](../tools/rust-install-check/Cargo.toml) uses the same [Win32 source](../tools/rust-execution-probe.rs).
For a new installation check, follow the [required verification procedure](rust-environment-verification.md).
That procedure requires a fresh output directory and the listed pass criteria.
Do not treat a cached build as a new check.

The dated repository check from 20 September 2026 is in the [observation log](observations.md).

Final checks confirmed that the previous `C:\Users\W106036\.cargo` and `C:\Users\W106036\.rustup` directories are absent, the saved environment values match the new locations, and the new Cargo bin directory occurs once in user PATH.

## Next actions

1. Repeat the state probe while the user types, moves a mouse, and uses the touchpad. Do not simulate input.
2. With user approval, observe one lock cycle and one sleep or Modern Standby cycle. Do not change power or lock policy.
3. If needed, test Windows Graphics Capture `CreateForWindow` on the same marker window.
4. Test return to the observer tab after a tab change.
5. Keep owned-child launching and cleanup for the later milestone after baseline/manual-helper validation.
