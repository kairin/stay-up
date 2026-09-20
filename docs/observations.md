# Observation log

The [required Rust environment procedure](rust-environment-verification.md) defines commands and pass criteria.
It covers installation, relocation, environment changes, and native execution failures.
The records below describe observed results.
Historical observations do not pass later application checks.

Stay-watch design rules are in the [stay-watch plan](stay-watch-plan.md). Unexecuted fixtures are in [stay-watch-acceptance.md](stay-watch-acceptance.md). Current machine results are in [stay-watch-feasibility.md](stay-watch-feasibility.md).

## 19 September 2026: observation before planned reboot

Recorded at approximately 09:55 Singapore time (local time).

The user reports that, as far as they recall, they have not needed to log
in again during this session. Their assessment is that the stay-awake app
appears to be working. This is an initial observation; the duration of
uninterrupted idle time, Teams status, and power source were not recorded.

Runtime evidence from the check at approximately 09:52:

- Latest commit: `28d03c14edaefd286a3741f670b95ce806677660`,
  "Add keep-awake heartbeat monitor", committed at 07:57:39 that morning.
- The helper process, PID `TEST-PID`, started at 07:54:52 and was still running
  when checked, about 1 hour 57 minutes later.
- The latest heartbeat read from `keep-awake.monitor.log` was
  `<local-timestamp> OK helper PID=TEST-PID is running`.
  This confirms process activity at that time; it does not measure screen
  or login behavior.

The user plans to reboot the computer and review the behavior again.
The reboot and subsequent review are pending at the time of this note.
Rebooting stops the helper and monitor. Neither has automatic startup
configured by this project.

After reboot, restart the helper and monitor, record the new process ID
and start time, and review whether another login is required during use.
The separate idle test with Teams closed for longer than the ten-minute
screen-saver timeout remains pending.

These two helper checks are not stay-watch design gaps.

## 19 September 2026: documentation review

A documentation review checked the helper scripts, inventory, and selected source references.
It did not repeat the runtime, reboot, sleep, or idle tests.
The observations above remain historical evidence.

That review found two specification gaps and one capture risk:

- Qualifying intervals must close at a power-source change.
- Required-observation loss must be visible. It must not be silent.
- A stable window handle does not prove observer content.

Those rules now live in the [stay-watch plan](stay-watch-plan.md).
This 19 September 2026 review did not run capture or stay-watch tests.
Later 20 September 2026 records in this log replace this pending statement for current status.

## 20 September 2026: corrected Rust installation and repository check

The former `%USERPROFILE%\.cargo` and `%USERPROFILE%\.rustup` installation was removed after checking the paths and confirming they contained only the prior installation. Rustup was reinstalled under `%LOCALAPPDATA%\Programs\Rust`. User settings and PATH were saved as specified in the [required procedure](rust-environment-verification.md).

| Check | Observed result |
|---|---|
| Old installation removed | Both old directories absent; old Cargo bin entry absent from user PATH. |
| Saved configuration | `CARGO_HOME`, `RUSTUP_HOME`, and `CARGO_TARGET_DIR` matched the documented paths. New Cargo bin entry occurred once in user PATH. |
| Compiler and package manager | `rustc 1.98.1 (48a229cea 2026-09-01)` and `cargo 1.98.1 (797e8a9bc 2026-08-05)` ran successfully. |
| Active toolchain | `stable-x86_64-pc-windows-gnu` was the default. |
| First installation fixture | Offline Cargo build, build script, and Win32 executable all passed. |
| Repository fixture | Fresh offline, locked build and execution passed at approximately 09:10 Singapore time. |

The repository fixture was tested from `D:\Apps\stay-up` with the saved user settings loaded into a new PowerShell child process:

```powershell
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir C:\Users\test-user\AppData\Local\Rust\target\installation-check-20260920-091022-874
```

The command exited with code zero after a fresh build taking 11.50 seconds. It emitted `RUST_BUILD_SCRIPT_EXECUTION_OK` and `RUST_EXECUTION_PROBE_OK pid=6236 console_hwnd=789308`. Cargo ran the binary from the selected directory's `debug` subdirectory. The PID, handle, and timestamped output directory are historical values, not application settings.

No screenshots, input-device checks, lock/suspend tests, or baseline/helper idle comparisons were run during this installation verification. Terminal enumeration had separately found a visible candidate earlier that day. Later the same day, capture and state probes ran. Use the later record in this log and the [current feasibility status](stay-watch-feasibility.md) for current status.

## 20 September 2026: acceptance vectors

A sequential prerequisite review produced the time-based fixtures.
Those fixtures now live in [stay-watch-acceptance.md](stay-watch-acceptance.md).
They are not executed tests.
An earlier Rust `NOT FOUND` preflight from that review is superseded by the installation record above.

## 20 September 2026: native feasibility probes

Recorded in the afternoon, Singapore time (local time).
Working directory: `D:\Apps\stay-up`.
Python `3.11.16`. `rustc 1.98.1`. `cargo 1.98.1`.
The probes made no power request and did not simulate input.

Rust state probe:

```powershell
rustc --out-dir C:\Users\test-user\AppData\Local\Rust\target\feasibility-20260920-1336 D:\Apps\stay-up\tools\rust-state-probe.rs
C:\Users\test-user\AppData\Local\Rust\target\feasibility-20260920-1336\rust-state-probe.exe
```

The compiler exited with code zero.
The executable printed `RUST_STATE_PROBE_OK pid=20124 console_hwnd=0 last_input_ok=1` with `power_ok=1 ac=1 batt%=100 raw_ok=1 mouse=3 keyboard=6 hid=17`.

Python state probe:

```powershell
python -B tools\windows-state-probe.py --listen-seconds 25 --output .\local\stay-watch\feasibility-20260920-1345\windows-state.json
```

The command exited with code zero after a repair of the structure-size defect.
Raw Input registration succeeded for keyboard, mouse, and touchpad usage pages.
Device lists included keyboard collections, mouse collections, and `TOUCHPAD-TEST` touchpad collections.

No `WM_INPUT` event arrived in 25 seconds. `GetLastInputInfo` did not change.
Power source was AC. `powercfg /a` listed `Standby (S0 Low Power Idle) Network Connected`.
Display notification data after registration was `1`.
No lock, session return, suspend, or power-source change was observed.
`WTSSessionInfoEx` flags are not used as a lock verdict.

Explicit capture test:

```powershell
python -B tools\capture-feasibility-probe.py --output-dir .\local\stay-watch\feasibility-20260920-1345
python -B tools\capture-feasibility-probe.py --tab-away --output-dir .\local\stay-watch\feasibility-20260920-1345
```

Both commands exited with code zero.
`GetConsoleWindow` in the parent process was `0`.
The capture target was a dedicated window titled `STAYUP-CAP-3e918444`.
`PrintWindow` with `PW_RENDERFULLCONTENT` and screen-region `BitBlt` both saved PNG files with the title bar and tab strip.

Initial-image rejection, marker visibility, freshness, scroll-away, minimization, and tab-away passed.
Windows Graphics Capture was not invoked.
Return to the observer tab was not tested.

Evidence files are under `local/stay-watch/feasibility-20260920-1345/`, which Git ignores.
These probes do not pass `t_cc724421`. Live input events, lock/sleep runtime, Modern Standby runtime, Windows Graphics Capture, and tab return remain open.

## 20 September 2026: silent re-check of recorded probes

Recorded at 14:21 Singapore time (local time).
Working directory: `D:\Apps\stay-up`.

```powershell
python -B -m unittest tools.test_feasibility_probes -v
```

The command exited with code zero.
It printed `Ran 14 tests in 5.950s` and `OK`.
The suite did not open a capture window.
No result in `docs/stay-watch-feasibility.md` changed.
Gate `t_cc724421` stays blocked.

## Visual-refresh planning after issues #6 and #7

The user reports that the repository project works and requests visual improvements only.
This is user-reported operation, not a new controlled idle or power test.
The [visual-refresh plan](visual-refresh-plan.md) records the bounded adversarial review.
No application code, process state, power setting, or toolchain changed.

Screenshot logging is removed from the active plan, including explicit-test captures.
Earlier capture results remain historical evidence. Withdrawn checks are not passed checks.
The local board was not changed.

Both issue bodies were read, and all eight completed attachments were retrieved through authenticated GitHub CLI access.
Four photos were inspected. Video container metadata was read, but video playback was not available.
The README now includes all four images and links to all four videos.
The [media record](issue-media.md) lists their provenance, access limits, and the incomplete upload placeholder.

Documentation checks passed for local links, all eight media URLs in both the README and media record, and diff whitespace.
STE-flavored lint scores were 1.49 findings per 100 words for the visual plan and 1.85 for the media record.
These are mechanical style scores, not certification.
No Rust build, helper launch, screenshot capture, or interactive machine test ran for these documentation-only changes.
