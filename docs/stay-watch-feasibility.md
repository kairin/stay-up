# stay-watch feasibility gate

Checked: 2026-09-20 06:58:28 +0800.

## Results

| Check | Result | Evidence and limit |
|---|---|---|
| Rust toolchain | FAIL | `rustc` and `cargo` are not installed. Rust implementation cannot start on this machine until the toolchain is available. |
| Windows input APIs | PASS | `RegisterRawInputDevices`, `GetRawInputData`, and `GetLastInputInfo` are present. Registration and device coverage remain untested. |
| Windows state APIs | PASS | `RegisterPowerSettingNotification`, `GetConsoleWindow`, `PowerCreateRequest`, and `PowerSetRequest` are present. A Rust event loop remains untested. |
| Modern Standby | PASS | `powercfg /a` reports S0 low power idle with network connection and hibernate. Runtime behavior remains untested. |
| Raw Input device coverage | UNKNOWN | No observer exists to register devices. Keyboard, external mouse, and touchpad coverage needs a test application. |
| Capture target | FAIL | `GetConsoleWindow` returned handle `0`. The current session uses a pseudoconsole, so it has no visible console target. |
| Observer visibility | UNKNOWN | A visible Windows Terminal session is necessary. The current session cannot establish observer visibility. |
| Capture backend | UNKNOWN | No backend was tested. Test Windows Graphics Capture and a visible screen-region method in a visible terminal session. |
| Owned-child cleanup | UNKNOWN | No Rust observer or owned-child path exists. Test console signal routing and cleanup after the Rust foundation exists. |

## Decision

The feasibility gate is incomplete.

The next allowed milestone is blocked by the missing Rust toolchain. The capture checks also need a visible Windows Terminal session. Do not start Rust implementation or screenshot implementation until these two limits have an approved path.

After these limits are resolved, repeat the input, capture, visibility, touchpad, and child-cleanup checks. Then move the tracking-foundation task forward.
