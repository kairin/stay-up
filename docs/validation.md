# Validation notes

The [required Rust environment procedure](rust-environment-verification.md) defines commands and pass criteria for installation, relocation, environment changes, and native execution failures. The records below describe observed results; historical observations do not pass later application checks.

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

## 19 September 2026: documentation review and pending checks

The [adversarial review](adversarial-review-2026-09-19.md) checked the documents against the helper scripts, inventory, and selected source references.
It did not repeat the runtime, reboot, sleep, or idle tests.
The observations above remain historical evidence.

The updated [stay-watch plan](stay-watch-plan.md) specifies these pending checks:

- Separate AC and battery intervals. A 29-minute AC interval followed by one minute on battery must not satisfy either 30-minute target.
- Start a fresh qualifying interval after each power-source change or period with an unknown source.
- Preserve earlier valid milestones and unrelated timers across those boundaries.
- Force required-observation queue overflow. Confirm visible incomplete status, a recorded gap, and fresh state observations before qualification resumes.
- Check image-queue overflow separately. A screenshot gap must not erase independent Windows observations.
- Switch terminal tabs within the same window, return, scroll into history, and minimize the window.
- Confirm that hidden, stale, or uncertain observer content cannot count as valid screenshot evidence.
- Reject test setup if the initial image cannot establish observer visibility and freshness.

The proposed first milestone validates baseline tests and attachment to a manually started helper.
Optional helper launching and owned-child cleanup remain later planned capabilities.
Their console signal and cleanup checks remain pending.

Baseline and helper comparisons require matching known power conditions.
Do not combine separate intervals to reach a target, even when they share the same power source.

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

No screenshots, input-device checks, lock/suspend tests, or baseline/helper idle comparisons were run during this installation verification. Terminal enumeration had separately found a visible candidate earlier that day; capture support and observer visibility remain unverified. See the [current feasibility status](stay-watch-feasibility.md).
