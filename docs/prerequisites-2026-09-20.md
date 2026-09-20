# stay-watch prerequisite packet

Checked: 2026-09-20 (Asia/Singapore). This packet records prerequisite preparation and the subsequent Rust installation checks. The initial preflight below is historical: the corrected installation now passes the Rust prerequisite. See the [current feasibility status](stay-watch-feasibility.md) for the remaining checks. The proposed acceptance vectors have not been executed, and the full feasibility gate has not passed.

## Initial capability preflight

| Check | Result | Evidence and next action |
|---|---|---|
| Rust on PATH | NOT FOUND | `Get-Command rustc` and `Get-Command cargo` returned absent. |
| Checked standard Rust paths | NOT FOUND | No executable was found at `C:\Users\test-user\.cargo\bin\rustc.exe`, `C:\Users\test-user\.cargo\bin\cargo.exe`, `C:\Program Files\Rust stable MSVC\bin\rustc.exe`, `C:\Program Files\Rust stable MSVC\bin\cargo.exe`, `C:\Program Files\Rust stable GNU\bin\rustc.exe`, or `C:\Program Files\Rust stable GNU\bin\cargo.exe`. This is not a machine-wide search. |
| Visual Studio locator | UNVERIFIED | `C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe` is absent. This does not establish that the SDK or MSVC is absent. |
| Python | AVAILABLE | `Get-Command python` resolves to Python 3.12.9. This supports existing helper tooling only; it does not provide the Rust toolchain. |
| Windows Terminal candidate | UNVERIFIED | A `WindowsTerminal` process was found with PID 15928 and `MainWindowHandle=0`. No title, command line, tab, or observer ownership was inspected. `EnumWindows` was skipped, so this does not establish that no top-level terminal HWND exists. A visible interactive Windows Terminal probe remains required. |

Commands used: `Get-Command rustc,cargo`; `Test-Path` on the six exact Rust paths above; `Test-Path` on the documented `vswhere.exe` path; `Get-Command python` and `python --version`; and `Get-Process -Name WindowsTerminal,wt` with only process name, PID, handle, and handle-derived visibility emitted.

At the initial preflight, Rust was not found on PATH or at the six checked standard paths; API presence and `powercfg /a` are static evidence only; Raw Input device coverage, Modern Standby runtime behavior, capture backend, observer visibility, and owned-child cleanup remain unverified (`docs/stay-watch-feasibility.md`, lines 9-25). The zero handle is evidence about this launch context, not proof that Windows Graphics Capture or a real visible terminal target is unsupported.

## Acceptance vectors

These are proposed fixtures, not executed tests. Unless a row says otherwise, time starts at `t=0`, the test target is 10 minutes, initial required states are known, and no input event occurs. Power and input adapters can be tested with deterministic simulation; separate real-device integration checks remain needed. The vectors encode the requirements in `docs/stay-watch-plan.md` (source lines 308-333, 450-480, and 502-526) and `docs/validation.md` (lines 44-48).

| ID / task | Timeline and expected result | Fixture |
|---|---|---|
| V1 / `t_c466d6a8` | At `t=0`, raw idle onset is `-120s`; start the test at `t=30s` with a 600s target. Without a start-input event: at `t=30s` raw idle=150s and test coverage=0s; at `t=600s` raw idle=720s and test coverage=570s, so the target is not reached; at `t=630s` raw idle=750s and test coverage=600s, so the target is reached. In the observed Start-input branch, input at `t=30s` resets raw idle to 0s; at `t=630s` raw idle and test coverage are both 600s. Do not hide the start input. | Deterministic clock/input fixture; real input integration separate |
| V2 / `t_e620a0cf`, `t_28377916` | Target=30m. `t=0` AC, `t=29m` battery, `t=30m` AC, inspect at `t=59m`: segments are AC `0..29m` (29m), battery `29..30m` (1m), AC `30..59m` (29m); neither reaches 30m and no durations sum. At `t=60m`, the current AC segment reaches 30m and may report the first AC success. | Deterministic power adapter; real AC/battery integration separate |
| V3 / `t_e620a0cf`, `t_c466d6a8` | `t=0` known AC, `t=4m` unknown, `t=7m` known AC, inspect at `t=13m`: confirmed segments are `0..4m` (4m) and `7..13m` (6m); unknown coverage is 3m; no 10m success and no summing. | Deterministic power/event adapter; real device integration separate |
| V4 / `t_e620a0cf` | Attach process A at `t=0` with handle identity A, record exit at `t=40s`, then present process B with reused PID at `t=50s`. Helper-required coverage ends at 40s; B is never attached by PID alone. | Deterministic process-event fixture |
| V5 / `t_1f0a1839` | Last trustworthy observation at `t=10s`; required event is lost at `t=12s`, so latch `RECORDING INCOMPLETE` immediately; sink recovers at `t=20s`; required states re-establish at `t=25s`; inspect at `t=35s`. Confirmed intervals are `0..10s` and `25..35s`; no summing; sink recovery alone is insufficient. | Deterministic queue/state fixture |
| V6 / `t_1f0a1839`, `t_fcc30590` | Branch A: image queue overflows at `t=40s`; record a screenshot gap while live sensor state continues. Branch B: durable event-log write fails at `t=45s`; latch sticky `RECORDING INCOMPLETE`, expose the durable evidence gap, and keep live state separate. Do not invent repair or claim lost records were persisted. | Deterministic queue and sink-failure fixtures |
| V7 / `t_fcc30590` | Tracking at `t=0` creates no capture resources. An explicitly invoked test at `t=10s` may attempt its initial image; if visibility/freshness is unverified, reject setup and return to tracking. In a valid setup, a later hidden, stale, or uncertain image at `t=30s` is retained as invalid/unverified and excluded from valid screenshots; independently observed objective state is unaffected. | Initial setup and image-status simulation; visible-terminal integration separate |
| V8 / `t_fcc30590` | End an active test explicitly at `t=60s`; deliver a delayed event at `t=61s`. Finish pending writes as specified, start no new capture from the late event, and continue tracking with saved evidence retained. | Deterministic event fixture |
| V9 / `t_fcc30590`, `t_28377916` | At `t=600s`, record `target reached` as a milestone and keep the test active. Send an explicit End test control at `t=650s`; end the test then and retain the earlier milestone. Exit/interruption are separate end-path variants; target attainment alone never ends the test. | Deterministic timer/terminal-event fixture |
| V10 / `t_1f0a1839`, `t_fcc30590` | Write complete JSONL through `t=30s`, truncate only the tail at `t=31s`, then manually relaunch at `t=60s`. Mark the prior test interrupted, retain complete records, and do not resume the test or restart its helper. | Deterministic file fixture |

For V7, a rejected initial-image attempt is distinct from ordinary tracking: tracking must make no capture resources, while an explicitly invoked test may attempt its initial image before rejecting setup. Hidden, stale, invalid, or uncertain content cannot count as verified evidence. This follows `docs/stay-watch-plan.md` line 521 and `docs/validation.md` lines 47-48.

## Checks and decisions after the initial preflight

The corrected installation completed item 1. Items 2-5 remain unverified:

1. Supply an approved Rust toolchain path and verify compilation and execution. Completed; see the corrected installation record below.
2. In a real visible Windows Terminal session, establish candidate target, observer visibility, freshness, tab switch/return, scrollback, and minimize behavior; test a capture backend without sampling during tracking.
3. Exercise keyboard, external mouse, and touchpad Raw Input coverage.
4. Exercise Modern Standby, lock, suspend/resume, and AC/battery transitions.
5. Run baseline and manually attached-helper validation under matching known power conditions.

The minimum start decision is an approved Rust toolchain plus a viable visible-terminal capture route. The full feasibility gate remains incomplete until runtime checks are performed. In particular, static API presence does not pass device coverage, Modern Standby behavior, or capture validity.

The board task `t_cc724421` broadly mentions owned-child cleanup, but the plan explicitly defers owned-child launching and cleanup to the later milestone. Clarify that task scope before marking the gate complete: owned-child cleanup must not block baseline or manual-helper attachment work, while its own later feasibility check remains required before `t_a765f749`.

## Readiness and inferred order

The board has no explicit dependency rows in the listing. The following order is inferred from acceptance criteria and the plan: resolve the `t_cc724421` toolchain and visible-terminal capture decisions; implement `t_740bd591`; share its event/state contract with `t_c466d6a8`, `t_e620a0cf`, and `t_1f0a1839`; add `t_fcc30590`; then run `t_28377916` baseline/manual-helper validation. Defer `t_a765f749` until core measurements pass and the separate child-cleanup feasibility check is complete.

## Initial review scope and provenance

Given: the live eight-task snapshot, the five supplied project documents, and bounded local capability commands. Examined: task titles/acceptance criteria, feasibility lines 9-25, validation lines 39-55, plan lines 308-333, 450-480, 502-526, and adversarial-review lines 59-74. Skipped: research tree, source implementation, helper execution, capture creation, machine settings, board mutation, network, credentials, and broad filesystem search.

Provenance: this packet records a sequential prerequisite review. No parallel worker run is claimed.

Sources: [stay-watch-plan.md](stay-watch-plan.md), [stay-watch-feasibility.md](stay-watch-feasibility.md), and [validation.md](validation.md).

## First resolution attempt (2026-09-20)

Canonical feasibility status is recorded in [docs/stay-watch-feasibility.md](stay-watch-feasibility.md).
In the first attempt, Rustup installation completed, but compiler launch was blocked by application control; no compile/run proof passed at that stage.
Native terminal discovery found an ephemeral eligible candidate; capture, tab ownership, and freshness remain untested.

## Corrected installation (2026-09-20)

The previous Rust folders were removed and Rust was reinstalled under `AppData\Local\Programs\Rust`. User environment settings put Cargo build outputs under `AppData\Local\Rust\target`. Rust and Cargo 1.98.1 ran successfully; an offline Cargo build executed its build script, compiled the Win32 probe, and ran the resulting executable. The Rust prerequisite now passes. See the [current feasibility notes](stay-watch-feasibility.md) for exact paths and the remaining capture/runtime checks.
