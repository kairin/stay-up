# Observation log

The [required Rust environment procedure](rust-environment-verification.md) defines commands and pass criteria.
It covers installation, relocation, environment changes, and native execution failures.
The records below describe observed results.
Historical observations do not pass later application checks.

Stay-watch design rules are in the [stay-watch plan](stay-watch-plan.md). Unexecuted fixtures are in [stay-watch-acceptance.md](stay-watch-acceptance.md). Current machine results are in [stay-watch-feasibility.md](stay-watch-feasibility.md).

## 19 September 2026: observation before planned reboot

Recorded at approximately 09:55 Singapore time (UTC+08:00).

The user reports that, as far as they recall, they have not needed to log
in again during this session. Their assessment is that the stay-awake app
appears to be working. This is an initial observation; the duration of
uninterrupted idle time, Teams status, and power source were not recorded.

Runtime evidence from the check at approximately 09:52:

- Latest commit: `28d03c14edaefd286a3741f670b95ce806677660`,
  "Add keep-awake heartbeat monitor", committed at 07:57:39 that morning.
- The helper process, PID `31908`, started at 07:54:52 and was still running
  when checked, about 1 hour 57 minutes later.
- The latest heartbeat read from `keep-awake.monitor.log` was
  `2026-09-19T09:51:09+08:00 OK helper PID=31908 is running`.
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
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir C:\Users\W106036\AppData\Local\Rust\target\installation-check-20260920-091022-874
```

The command exited with code zero after a fresh build taking 11.50 seconds. It emitted `RUST_BUILD_SCRIPT_EXECUTION_OK` and `RUST_EXECUTION_PROBE_OK pid=6236 console_hwnd=789308`. Cargo ran the binary from the selected directory's `debug` subdirectory. The PID, handle, and timestamped output directory are historical values, not application settings.

No screenshots, input-device checks, lock/suspend tests, or baseline/helper idle comparisons were run during this installation verification. Terminal enumeration had separately found a visible candidate earlier that day. Later the same day, capture and state probes ran. Use the later record in this log and the [current feasibility status](stay-watch-feasibility.md) for current status.

## 20 September 2026: acceptance vectors

A sequential prerequisite review produced the time-based fixtures.
Those fixtures now live in [stay-watch-acceptance.md](stay-watch-acceptance.md).
They are not executed tests.
An earlier Rust `NOT FOUND` preflight from that review is superseded by the installation record above.

## 20 September 2026: native feasibility probes

Recorded in the afternoon, Singapore time (UTC+08:00).
Working directory: `D:\Apps\stay-up`.
Python `3.11.16`. `rustc 1.98.1`. `cargo 1.98.1`.
The probes made no power request and did not simulate input.

Rust state probe:

```powershell
rustc --out-dir C:\Users\W106036\AppData\Local\Rust\target\feasibility-20260920-1336 D:\Apps\stay-up\tools\rust-state-probe.rs
C:\Users\W106036\AppData\Local\Rust\target\feasibility-20260920-1336\rust-state-probe.exe
```

The compiler exited with code zero.
The executable printed `RUST_STATE_PROBE_OK pid=20124 console_hwnd=0 last_input_ok=1` with `power_ok=1 ac=1 batt%=100 raw_ok=1 mouse=3 keyboard=6 hid=17`.

Python state probe:

```powershell
python -B tools\windows-state-probe.py --listen-seconds 25 --output .\local\stay-watch\feasibility-20260920-1345\windows-state.json
```

The command exited with code zero after a repair of the structure-size defect.
Raw Input registration succeeded for keyboard, mouse, and touchpad usage pages.
Device lists included keyboard collections, mouse collections, and `ELAN07FF` touchpad collections.

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

Recorded at 14:21 Singapore time (UTC+08:00).
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

## 20 September 2026: Cargo build access from an agent

Recorded at approximately 20:14 Singapore time (UTC+08:00).
Working directory: `D:\Apps\stay-up`.
The user requested a check of the build method before implementation of a root launch script.

### Environment

Saved user settings and current process settings agreed:

| Setting | Value |
|---|---|
| `CARGO_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `C:\Users\W106036\AppData\Local\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `C:\Users\W106036\AppData\Local\Rust\target` |
| Toolchain | `stable-x86_64-pc-windows-gnu` |
| Versions | Rustup `1.29.1`, rustc `1.98.1`, Cargo `1.98.1`, Codex CLI `0.155.1` |

Command resolution selected the documented Cargo bin directory.
`rustup which` selected Cargo and rustc under the documented Rustup toolchain directory.
The user PATH contained the approved Cargo bin directory once, with no old `.cargo\bin` entry.
The old `.cargo` and `.rustup` directories were absent.

### Original Codex launch

The check included the local Codex session record, not only the displayed transcript.
Its file is `rollout-2026-09-20T19-58-18-01a0beae-7227-7563-bdd3-7560441146c6.jsonl` under `.codex/sessions/2026/09/20/`.

- Line 6 records `workspace-write` and `on-request` approval.
- Line 43 runs the default Cargo build without an escalation request.
- Line 46 records access denied at `debug\.cargo-build-lock`.
- Line 52 changes the output directory **and** requests `sandbox_permissions: "require_escalated"`.
- Line 67 records exit code zero and the launched executable path.

Thus, the successful retry changed two conditions. It did not prove that a fresh directory alone fixed the failure.

### Controlled checks

Each check used a new PowerShell 7 process with `-NoProfile -NonInteractive` from the repository root.
The ordinary checks ran through the Hermes terminal without a Codex sandbox.
The sandbox checks used `codex sandbox -- <PowerShell command>` from the same root.
The commands supplied no sandbox permission override.

| Check | Output directory below `CARGO_TARGET_DIR` | Exit code | Result |
|---|---|---|---|
| Original default app build | Root | 0 | Compiled and linked. Cargo reported 7.24 seconds. |
| Fresh installation probe | `installation-check-launch-9ffed62d45` | 0 | Compiler, build script, linker, and Win32 executable ran. |
| First app build in a stable directory | `stay-up` | 0 | Compiled and linked. Cargo reported 5.62 seconds. |
| Repeat app build in that directory | `stay-up` | 0 | Cargo reported `Fresh` and 0.02 seconds. |
| Recompile with a changed compiler argument | `stay-up` | 0 | Compiled and linked. Cargo reported 4.06 seconds. |
| Default build inside the Codex sandbox | Root | 101 | Access denied at `debug\.cargo-build-lock`. |
| Stable-directory build inside the Codex sandbox | `stay-up` | 101 | Access denied at `debug\.cargo-build-lock`. |
| New directory inside the Codex sandbox | `stay-up-sandbox-check-84c17a7211` | 1 | `New-Item` failed with access denied before Cargo ran. |

Commands for the ordinary checks:

```powershell
cargo build --manifest-path .\stay-watch\Cargo.toml --offline
cargo run --offline --locked --verbose --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\installation-check-launch-9ffed62d45"
cargo build --offline --locked --verbose --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\stay-up"
cargo rustc --offline --locked --verbose --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\stay-up" --bin stay-watch -- -C debuginfo=1
```

The stable build command ran twice before the recompile.
The probe emitted `RUST_BUILD_SCRIPT_EXECUTION_OK` and `RUST_EXECUTION_PROBE_OK pid=2848 console_hwnd=0`.
These are observed values, not fixed settings.
The recompile changed an argument, not a source file.

Both sandbox Cargo failures reported:

```text
error: failed to open: <target>\debug\.cargo-build-lock

Caused by:
  Access is denied. (os error 5)
```

File ACL checks showed inherited full access for the user on both target lock files.
AppLocker event 8002 recorded allowed Cargo execution during the sandbox failures.
This separates file access in the Codex sandbox from an application-control block on Cargo.
The tests do not indicate a need for a new administrator exception or a Rust reinstall.

### Launch design correction and limits

A stable project output directory works for repeated builds in the ordinary terminal.
It does not grant write access through the Codex sandbox.
A root launch script must retain the approved tool paths and output location.
The agent must also get the required permission to use that location.
Do not disable the sandbox or change ACLs as an automatic retry.
Do not describe `--offline`, `--locked`, or a new directory as a permission fix.

The sandbox test used the current CLI configuration, not the live token from the original interactive session.
The original session record independently confirms the explicit permission change on its successful retry.
The existing app remained alive as PID `21104` at the end of the check.
Its executable remained under `stay-up-launch-20260920-195931-861\debug`.
The check did not start or stop an app instance. No screenshot, input, power, lock, or sleep check ran.
No application source, toolchain setting, ACL, or security policy changed.
At the end of that check, the root launch script and its startup checks remained unimplemented.

## 20 September 2026: Root launch command and owned-process checks

Working directory: `D:\Apps\stay-up`.
The user approved implementation, closure of the old app, and a new launch.
A senior developer on `gpt-5.6-luna` prepared the root launcher.
A separate Luna review found defects in the first version.
The repairs added argument limits, command-path checks, process-handle checks, and structured error results.
The parent completed the active-toolchain check and verification.
The final independent Luna review passed with no blocking findings.

### Commands and results

```powershell
python -B -m unittest tools.test_launch -v
cargo test --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
python -B .\launch.py --seconds 12
python -B .\launch.py
```

Python `3.11.16` ran the launcher and its tests.
The Rust setup remained as recorded in the preceding build-access check.
No toolchain, environment setting, ACL, or security policy changed.
The stable output remained `%LOCALAPPDATA%\Rust\target\stay-up`.

| Check | Result |
|---|---|
| Launcher unit tests | Exit 0. All 24 tests passed. |
| Rust unit tests | Exit 0. All 12 tests passed. |
| Old app Stop action | Rust PID `21104` and helper PIDs `23396` and `22824` exited. Held process handles confirmed exit. |
| Concurrent root commands | Both commands exited 0. One returned `started`; the other returned `already_running`. Both reported PID `18792` and window `1704746`. |
| Timed exit | The 12-second session ended. Held handles confirmed exit of Rust, both helper launchers, both Python interpreters, and both console hosts. |
| Invalid arguments | Unknown options and negative seconds returned exit 2 without app startup. Unit tests also cover the Rust `u64` limit. |
| Sandbox denial | The root command returned exit 1 with `status=failed`. Cargo returned 101 at `debug\.cargo-build-lock` with `Access is denied. (os error 5)`. No app started. |
| Stop after a persistent launch | PID `1112` and its owned descendants exited through the existing Stop action. All held handles confirmed exit. |
| Final root launch | Exit 0 at approximately 21:15 Singapore time. The command returned `started` in 2.859 seconds. Rust PID `21004` owned visible window `2426406`. |
| Repeat from another working directory | Exit 0 with `already_running`, PID `21004`, and the same window. `--seconds 3` did not change the existing session. |

The final executable was:

```text
C:\Users\W106036\AppData\Local\Rust\target\stay-up\debug\stay-watch.exe
```

The final Rust process started helper launchers `24276` and `23580`.
Their Python interpreter PIDs were `16276` and `19040`.
The monitor recorded `OK helper PID=16276 is running` at `21:15:34+08:00`.
This is a process-lifetime observation, not an idle, lock, or sleep result.

### Verification limits and evidence

A test harness initially counted older processes that retained the same parent PID as a new Rust process.
That check failed before any Stop action on those processes.
The corrected harness checks creation times before it accepts a parent-child relation.
It also checks helper commands and executable paths, and holds process handles during shutdown.
The repeated Stop and final launch checks passed. No unrelated process was stopped.

The local JSON records are in `local/stay-watch/root-launch-verification/`.
They include the old Stop result, later Stop results, final live checks, final startup result, and final review.
The helper heartbeat remains in `local/stay-watch/keep-awake.monitor.log`.
These local files are excluded from Git.

The launcher starts only Rust. Rust retains helper startup and cleanup ownership.
No Rust source or helper source changed. No screenshot or capture resource was used.
Console presentation was not changed. Broader observer feasibility remains separate.
The root command does not grant sandbox write permission. An agent must request the required terminal authorization.
The command left the app open after startup.
A later read-back at approximately 21:20 found no app process or status window.
The user confirmed closure and requested that the app remain closed. No further launch occurred.
No commit or publication occurred.

## 20 September 2026: Native output panes

Working directory: `D:\Apps\stay-up`. Baseline: `bafa248`.
The user approved one Rust window with status and two native output/log panes,
and requested implementation by a Luna agent. A `gpt-5.6-luna` agent implemented
the Rust changes. Parent review requested restoration of the original PID
handshake, bounded buffering before copying, selection preservation, keyboard
routing, and child-window paint clipping. The same agent applied the corrections.

The final main process still waits for the helper PID or stdout EOF/error; no
new handshake timeout remains. Python discovery and both children use
`CREATE_NO_WINDOW`. The helper stdout and error streams feed bounded display
buffers. The monitor keeps writing its original file; a separate read-only
worker supplies the shared-history pane. The root launcher is unchanged.

Both Python scripts and `stay-watch/src/lib.rs` have no content diff from HEAD.
The helper Git blob hashes before and after the change were:

- `keep-awake.py`: `406c3ff96178c7159bd7d61c4974b411c64b3d0b`
- `monitor-helper.py`: `5a2d91a060000ee2f63050117f8eca556785c7e8`

### Environment and commands

Saved user settings and current process settings matched the documented Cargo,
Rustup, and target paths. Command resolution selected Cargo, rustc, and rustup
from `C:\Users\W106036\AppData\Local\Programs\Rust\cargo\bin`.
The stable output remained `C:\Users\W106036\AppData\Local\Rust\target\stay-up`.
No toolchain or path change was made; the previous installation-probe evidence
was reused. Observed versions: rustc `1.98.1 (48a229cea 2026-09-01)`, Cargo
`1.98.1 (797e8a9bc 2026-08-05)`, toolchain `stable-x86_64-pc-windows-gnu`,
and parent Python `3.12.9`.

The implementation agent ran:

```powershell
cargo test --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
cargo build --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
```

Both commands exited 0. The 17 Rust tests passed (12 existing, five output/log
and layout tests). Rustfmt was unavailable for this toolchain; no component was
installed. `git diff --check` passed.

In the parent's Python environment, the documented `python -B -m unittest
tools.test_launch -q` could not import `tools.test_launch`. Explicit discovery
with the repository added to `sys.path` ran all 24 launcher tests successfully:

```powershell
python -B -c "import sys, unittest; sys.path.insert(0, r'D:\Apps\stay-up'); suite=unittest.defaultTestLoader.discover(r'D:\Apps\stay-up\tools', pattern='test_launch.py'); result=unittest.TextTestRunner(verbosity=0).run(suite); sys.exit(not result.wasSuccessful())"
python -B tools\verify_output_panes.py --run
```

The live harness ran with terminal authorization for the approved output
directory and desktop. It used the root launcher and exited 0 at approximately
22:14 Singapore time. No screenshot or capture resources were used.

| Session | Result |
|---|---|
| Timed, 65 seconds | PASS. Rust PID `18400`; held owned PIDs `18400`, `24952`, `5160`, `26552`, `27108`. Two native read-only panes and exactly one visible owned window. SYSTEM, DISPLAY, and PID startup messages were displayed. The next heartbeat appeared while selection 0..6 remained unchanged. Three heartbeat records were appended. All held processes exited after the time limit. |
| Minimize, resize, split, Stop | PASS. Rust PID `27304`; held owned PIDs `27304`, `28440`, `28416`, `11156`, `14372`. The slider changed pane width. X minimized with owned processes alive. Panes and Stop stayed within the resized client area. Stop ended all held processes. Two heartbeat records were appended. |

Both sessions preserved the pre-existing heartbeat file bytes. Added records
retained the current helper PID and `interval=60s`. The unchanged Python scripts
made their usual power requests during the bounded test sessions. Process handles
and creation times limited checks and cleanup to the test session's descendants.
The app was left closed.

### Limits

No new long-term idle, sleep, lock, power-policy, screenshot, or input-device
test was performed. The tests establish the launch/pane changes and observed
owned-process cleanup only. Manual DPI/scaling, high-contrast, screen-reader,
and physical keyboard/mouse interaction checks remain outstanding. The metadata
resize check verifies control bounds, not every painted label's visual fit.
Normal append selection preservation passed; arbitrary log truncation while
selected and horizontal scroll retention were not exercised live.
No commit, push, or board update was performed for this change.

## 20 September 2026: User acceptance of the working baseline

After the native-pane implementation, the user stated, "the implementation is
working," and then explicitly confirmed, "yes this is the baseline."

The accepted implementation is commit `fed8eb5` (`feat: add native output panes`).
It includes the single Rust window, status dashboard, adjustable read-only panes,
and suppression of separate Python console windows. Future changes must preserve
the [accepted baseline contract](native-output-panes.md#accepted-working-baseline),
including the existing helper and heartbeat behavior.

This is user-reported acceptance in normal use, not a new controlled test.
The specific outstanding checks above remain unverified. Recording this
acceptance changed documentation only; no application launch or runtime test ran.
