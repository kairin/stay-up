# Rust-only migration plan

> Status: Research only. The migration remains proposed. Implementation is not approved.

Review date: 22 September 2026.
Source: `d459cbfd6cad7fae0bd3219874f1e3d0de1cd46d` on `main`.

## Proposed direction

Use the staged M1 design from the [earlier review](rust-only-migration-review.md).
Keep the native Rust dashboard. Replace its Python helper and monitor with
separate Rust executables. Then replace the Python root launcher and all
retained project-owned tools and tests.

This is a port, not a new UI or observer. Keep the existing three-process
runtime and shared log. A separate native launcher exits after its startup check.
Do not merge the helper and monitor into the UI process.

M1 keeps the GUI subsystem separate from manual console tools. M2, one binary
with several process modes, remains an alternative after console behavior tests.
M3, one process, conflicts with the current external monitor and pane meaning.
Neither alternative removes the need to port the launcher and retained tools.

The earlier TypeSafe scores remain advisory evidence. This plan does not repeat
those scores or change their raw records. The earlier pause records that review's
end state. This document adds implementation steps for the new planning request.
Implementation and live acceptance remain pending.

## Meaning of Rust-only

Use these separate completion gates:

1. **Native runtime:** the UI, power helper, and monitor run without Python.
2. **Native launch:** a Rust command builds and starts the runtime without Python.
3. **Owned tools:** all retained project-owned tools and tests use Rust.
   Each removed Python tool needs an explicit retirement record.

The final claim applies to maintained project-owned code. It does not mean that
Windows, the linker, Git, Cargo dependencies, or external services use only Rust.
Keep vendor source and historical records unchanged.

Hermes is an external development tool with a Python agent implementation.
A Rust exporter that starts Hermes does not make that external workflow
Python-free. Keep that integration optional and outside required application
build, launch, and acceptance. A stricter ban on Python anywhere in the developer
workflow needs a separate decision to retire or replace that integration.

## Document review

The review covered the 14 tracked project-owned Markdown files and the existing
untracked migration review. It also checked the source and launcher call paths.
The PowerToys snapshot and runtime inventory remain historical source evidence,
not code to port. This review did not repeat media or binary-hash analysis.

| Document | Use in this migration |
| --- | --- |
| [Repository rules](../AGENTS.md) | Preserve approved paths, authorization, and evidence rules. Change the root-command rule only at native-launch acceptance. |
| [README](../README.md) | Current commands remain valid until each replacement passes. Distinguish the Python launcher from the Rust dashboard. |
| [Repository layout](repository-layout.md) | Update file purposes when replacements land. Do not perform another layout cleanup. |
| [Native output panes](native-output-panes.md) | Preserve the accepted visible and lifecycle behavior. Treat Python filenames and interpreter choice as implementation details to replace with approval. |
| [Visual refresh plan](visual-refresh-plan.md) | Preserve presentation. The migration is separate runtime work with its own checks. |
| [UI layout reference](ui-layout-reference.md) | Keep dimensions and controls. Update source references only when they change. |
| [Rust environment procedure](rust-environment-verification.md) | Use its machine checks after an environment change or native execution failure. |
| [Observation log](observations.md) | Reuse dated evidence within its limits. Add real native results after execution. |
| [Feasibility record](stay-watch-feasibility.md) | Keep unresolved device behavior separate from a language port. |
| [Observer proposal](stay-watch-plan.md) | Historical only. Add no observer feature. |
| [Acceptance vectors](stay-watch-acceptance.md) | Historical, unexecuted observer cases. Do not import withdrawn capture gates. |
| [Research record](research.md) | Keep provenance, policy limits, and vendor notices. |
| [Issue media](issue-media.md) | Context only. Add no capture work. |
| [Task-ranker guide](../scripts/task-ranker/README.md) | Preserve score, cache, export, privacy, and board limits if the tool remains. |
| [Earlier migration review](rust-only-migration-review.md) | Keep candidate comparison and immutable research evidence. This plan adds ordered work and exit checks. |

### Corrections and conflicts

- At review start, the README's current-design section called the app a Rust
  launcher. This review corrects that description. The root launcher is
  `launch.py`; `src/main.rs` is the Rust dashboard entrypoint.
- `stay-watch-feasibility.md:35` presents a `tools.test_feasibility_probes`
  command under a verification heading. The current directory is `scripts/`.
  Mark that command as historical, or replace it only with a checked current
  command. Do not revive capture checks to repair a documentation example.
- The current visual contract preserves Python files byte for byte. A language
  port needs an explicit exception for implementation language and executable
  names. It does not waive visible behavior, log behavior, or cleanup checks.
- The earlier review proposes a bounded ready handshake. Current code uses
  blocking `recv()` without a timeout at `src/main.rs:140`. Treat a deadline and
  fail-closed readiness as a named behavior change, not existing behavior.
- The earlier review leaves the Hermes implementation boundary unknown. The
  official [Python library guide](https://hermes-agent.nousresearch.com/docs/guides/python-library)
  confirms a Python agent implementation. Do not claim that Hermes is Rust-only.

Keep dated commands in `observations.md` unchanged. They record actual runs.

## Current code boundary

| Area | Evidence | Migration consequence |
| --- | --- | --- |
| UI and output | `src/main.rs`, `src/ui.rs`, `src/output.rs` | Already Rust. Keep the native Win32 controls and bounded output readers. |
| Python discovery | `src/main.rs:28-43` | Remove interpreter lookup after both native children pass acceptance. |
| Child launch | `src/main.rs:107-165`, `src/lib.rs:40-63` | Replace script paths with explicit sibling executable paths. Preserve arguments and working directory. |
| Power helper | `scripts/keep-awake.py:56-88` | Port one handle, SYSTEM then DISPLAY, reverse cleanup, and flushed status output. |
| Monitor | `scripts/monitor-helper.py:11-53` | Preserve the original process handle, local timestamp, append behavior, polling, and record text. |
| Stop | `src/ui.rs:313-315`, `src/ui.rs:941-950` | Keep monitor-before-helper termination. Forced Stop does not promise graceful cleanup output. |
| Root launcher | `launch.py:228-285`, `launch.py:631-681` | Port validation, exact image and owned-window checks, mutex, build, and result handling. |
| Cargo package | `Cargo.toml`, `Cargo.lock` | One package, one binary, and no external crates now. Each added dependency needs an explicit reason. |

Known limits are not new features to hide inside the port:

- UI death does not automatically terminate both children.
- The UI reopens the helper by PID for its timer check at `src/ui.rs:905-913`.
- Monitor death alone does not end the UI at `src/ui.rs:935-937`.
- The launcher can report a startup timeout while its child stays live.
- Stop kills the monitor first. A final `STOPPED` record is not guaranteed.

Record these cases in the comparison tests. Plan lifecycle improvements as
separate changes. Do not preserve an unsafe handle bug in new code merely to
copy a pre-existing limit.

## Target structure

These paths and targets are proposals. They do not exist yet.

| Target | Proposed source | Responsibility |
| --- | --- | --- |
| `stay-watch.exe` | Existing `src/main.rs` and UI modules | GUI subsystem. Own two native children and the existing panes. |
| `keep-awake.exe` | `src/bin/keep-awake.rs`, `src/power.rs` | Console subsystem. Own power requests and manual Ctrl+C cleanup. |
| `monitor-helper.exe` | `src/bin/monitor-helper.rs`, `src/monitor.rs` | Console subsystem. Observe the helper and append heartbeat records. |
| `stay-up-launch.exe` | `src/bin/stay-up-launch.rs`, `src/launcher.rs` | Console command. Validate, build selected runtime targets, check startup, and emit JSON. |
| Native test harness | `tests/` or a small test-tool target | Compare contracts and run explicitly selected desktop checks. |
| Optional task tools | Separate crate under `scripts/task-ranker/` | Rank and export tasks without adding network dependencies to the runtime package. |

Share narrow Win32 wrappers and pure parsing code where useful. Do not rewrite
working UI bindings as part of this port. Prefer generated `windows-sys`
bindings for new Windows calls if the approved GNU build and offline cache pass.
Use a tested JSON library and SHA-256 implementation for launcher and tool
contracts. Do not create custom JSON escaping or cryptographic code.

Select crate versions and features during the first implementation gate. Record
licenses, build scripts, native library needs, and cache contents. Keep blocking
control flow. Add no async runtime, service, scheduler, installer, updater,
terminal emulator, IPC bus, or Job Object change for this port.

## First build and later builds

Keep the checkout at `D:\Apps\stay-up`. Keep application products under
`%LOCALAPPDATA%\Rust\target\stay-up`. Keep Cargo and Rustup in the locations
from the environment procedure. A different directory is not an access fix.

The first native launcher cannot build itself before it exists. Use the approved
external Cargo command to build it. Do not introduce a replacement Python,
PowerShell, or batch launcher script. Shell command examples are not maintained
application code.

After the new targets exist, the proposed first-build command is:

```powershell
cargo build --offline --locked --manifest-path .\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up" --bin stay-up-launch
```

The proposed root launch command is then:

```powershell
& "$env:LOCALAPPDATA\Rust\target\stay-up\debug\stay-up-launch.exe"
```

The native launcher must build only the runtime targets:

```text
cargo build --offline --locked --manifest-path <repo>/Cargo.toml --target-dir <approved-stable-target> --bin stay-watch --bin keep-awake --bin monitor-helper
```

Use the validated absolute Cargo path in code. Do not use `--bins`: that can
select the running launcher. Update the launcher only through external Cargo
after all launcher invocations exit. Resolve the checkout independently of the
launcher executable's parent directory.

New crates require a prepared cache under the approved `CARGO_HOME`. Plan an
explicit authorized dependency-fetch step before offline builds. Commit the
lockfile with the code change. Do not let normal launch download packages or
install Rust. A prebuilt distribution remains separate future work; this plan
keeps the existing source-build workflow.

## Ordered milestones

The IDs below are plan labels, not live Kanban task IDs. No board state changes
occur in this review. At implementation approval, map these dependencies onto
the existing local `stay-up` board. Do not infer readiness from old observer tasks.

| ID | Work | Depends on | Exit evidence |
| --- | --- | --- | --- |
| R0 | Approve scope and contracts. Choose bindings, dependencies, bootstrap, and retirement decisions. | None | Written decisions, source test map, approved-path build strategy, and fixed test fixtures. |
| R1 | Port the power helper with a small Rust entrypoint. Keep Python as the comparison path. | R0 | Unit tests for every request and cleanup branch. Manual console and timed checks under Windows. |
| R2 | Port the monitor and its timestamp formatter. | R0 | Byte-level log fixtures, wait-result tests, and a separate-process liveness check. |
| R3 | Wire native siblings into the UI. Port the pane harness. | R1, R2 | Timed and Stop sessions, later heartbeat, unchanged log prefix, hidden children, and owned-process cleanup. |
| R4 | Port the root launcher and its tests. Change the supported command. | R3 | First build and later build without Python. Exact JSON, mutex, image, window, and error checks. |
| R5 | Port retained tools and tests. Record approved retirements. | R0; runtime checks remain separate | Fixture parity, cache-only tests, process-lock tests, and a closed disposition for every Python source. |
| R6 | Remove accepted Python replacements from maintained paths. Review release instructions. | R4, R5 | No required Python path, no Python child, Rust tests, and final source and dependency audit. |

R1 and R2 can proceed in parallel with separate file ownership. R5 can proceed
independently after its scope decision. A parent reviewer owns integration and
acceptance. Do not start code work from this planning record alone.

### R1: helper acceptance

- Preserve omitted duration and `--seconds 0` as indefinite operation.
- Reject negative and malformed durations before any power request.
- Test request creation failure, SYSTEM failure, and DISPLAY failure after SYSTEM succeeds.
- Clear only accepted requests, in reverse order. Attempt handle closure after failures.
- Report cleanup errors. Do not use `std::process::exit` while cleanup guards still own requests.
- Print and flush SYSTEM, DISPLAY, and the existing PID record in order.
- Use a monotonic deadline. Check direct console output, redirection, timed exit, and Ctrl+C.
- Keep control-handler work small. Signal the main loop to perform normal cleanup.
- Do not equate Ctrl+C with console close, logoff, forced kill, or shutdown.

### R2: monitor acceptance

- Keep `--interval 60`, `--log`, the helper PID argument, and the canonical log path.
- Open the helper once with `SYNCHRONIZE`. Test PID reuse without attaching to a replacement process.
- Preserve `monitor started`, immediate `OK`, later `OK`, `STOPPED`, and `ERROR` text.
- Keep ISO 8601 local timestamps with seconds and UTC offsets. Test offset and date boundaries.
- Append UTF-8 with LF endings. Open, flush, and close for each record; promise no `fsync`.
- Test open, wait, and file failures. Preserve existing wait-result exit behavior unless separately approved.
- Test helper exit before the first sample. Do not silently change polling into an event-driven observer.

### R3: UI and child acceptance

- Build native siblings together. Use explicit sibling paths, not a PATH search or Python fallback.
- Update the transitional `launch.py` build targets and output checks in this slice.
  Its current `--bin stay-watch` command cannot build the new siblings.
- Keep one visible Rust window and hidden owned consoles. Keep direct helper launch usable.
- Preserve both read-only panes, Split, keyboard access, selection, bounds, and idle reset.
- Keep `src/output.rs` unchanged unless a demonstrated compatibility problem requires a separate fix.
- Add a bounded ready deadline only as an approved startup change.
- For that change, reject missing, invalid, oversized, late, or mismatched ready output.
- Clean up owned children after readiness or spawn failure. Never terminate an unrelated PID.
- Run a session beyond 60 seconds and check the next heartbeat on disk.
- Preserve the existing log prefix, including when its display tail exceeds 48 KiB.
- Test timed exit, X-to-minimize, resize, Stop order, and held-handle process exit.
- Keep DPI, high contrast, screen-reader, and physical input checks separate from automated checks.

### R4: launcher acceptance

Port all cases from `scripts/test_launch.py`; record the Rust test mapping.
Keep these additional comparison gates explicit:

- Fixed checkout, source checks, approved environment, command resolution, compiler overrides, and active toolchain.
- Decimal `--seconds` validation, the Rust `u64` limit, help, errors, and process-start ordering.
- The checkout mutex name, SHA-256 input, timeout, abandoned-lock handling, and release.
- Concurrent launches, exact executable identity, owned window class, and process-handle liveness checks.
- Existing-instance behavior: do not rebuild or apply new arguments to a live instance.
  Preserve an existing-instance result with `window_handle=0` when no owned window appears.
  A new `started` result still requires an owned `StayWatchStatusWindow`.
- Ten-second startup wait and current failure statuses. Record any separately approved timeout cleanup change.
- Sorted JSON keys, field types, optional error field, escaping, newline, stdout isolation, and exit codes.
- Build failure before process start. Separate sandbox write denial from application-control blocks.
- Runtime-only target selection while the native launcher runs. No self-overwrite or child rebuild conflict.

## Every owned Python source

The tracked inventory contains 13 project-owned Python files. The table gives
one proposed disposition for each file. Retirement needs approval; a proposal
alone does not satisfy R6. Keep the previous source in Git history for rollback.

| Current file | Proposed disposition | Required evidence |
| --- | --- | --- |
| `launch.py` | Port in R4, then remove. | Launcher contracts and first-build sequence. |
| `scripts/keep-awake.py` | Port in R1, then remove after R3. | Power, output, duration, and manual Ctrl+C parity. |
| `scripts/monitor-helper.py` | Port in R2, then remove after R3. | Log bytes, process identity, timing, and error parity. |
| `scripts/test_launch.py` | Port to Rust tests in R4. | Every existing case maps to a retained or explicitly revised test. |
| `scripts/verify_output_panes.py` | Port to an explicit Rust desktop harness in R3/R4. | Same owned-session, pane, heartbeat, and cleanup checks; no capture. |
| `scripts/task-ranker/rank_tasks.py` | Port in R5. | Weights, confidence, input rejection, cache identity, locking, and output fixtures. |
| `scripts/task-ranker/export_kanban.py` | Port as an optional Rust integration in R5. | Same Hermes list/show interface and stale-export checks. External Hermes remains outside the Rust-only claim. |
| `scripts/task-ranker/test_rank_tasks.py` | Port in R5. | Mock service, cache-only, lock, merge, and invalid-input tests. |
| `scripts/task-ranker/test_export_kanban.py` | Port in R5. | Membership, content, identity, parent-state, and failure fixtures. |
| `scripts/windows-state-probe.py` | Recommend retirement from maintained paths. | Explicit decision that historical observer probes are not current product tools. If retained, port separately. |
| `scripts/terminal-target-probe.py` | Recommend retirement from maintained paths. | Explicit decision; hidden native children do not need terminal discovery. If retained, port separately. |
| `scripts/capture-feasibility-probe.py` | Recommend retirement; do not reimplement capture. | Record withdrawn scope and preserve historical evidence. |
| `scripts/test_feasibility_probes.py` | Recommend retirement with the historical probe suite. | Preserve recorded results. If any non-capture check remains required, port it before retirement. |

The existing Rust installation and state probes remain Rust. Do not treat the
small state probe as automatic replacement coverage for the larger Python probe.
Keep historical limitations visible. Remove `typesafe-sdk` requirements and
Python setup instructions only after the retained task tools pass their gates.

### R5: tool-specific checks

Use the documented [TypeSafe HTTP API](https://docs.typesafe.ai/api) from Rust
instead of wrapping the Python SDK. Verify request and response schemas with
fixtures. Live service acceptance remains a separate authorized network test.
Do not send task text, credentials, or fresh scoring requests during this review.

Keep the rubric version, score direction, weights, probability data, confidence
threshold, and readiness rules. A cached-only miss must fail without a network
call. Preserve the evidence fingerprint's JSON representation, or approve a
versioned cache migration. Test Unicode and numeric edge cases.

Keep the five-second cache lock, merge-on-write behavior, unique temporary files,
and atomic replacement. Keep API calls outside the cache lock. Do not delete
an active lock file. Windows and POSIX claims need separate host tests if both
remain supported.

The exporter must validate task IDs before lookup. Preserve archived parents,
repeated membership and content checks, and sensitive-field exclusions. Use the
existing Hermes CLI contract; do not read its database directly. List/show
calls can refresh dependency state. They are not a guaranteed read-only
transaction or an atomic snapshot.

## Verification, rollback, and limits

For each code slice, write deterministic tests before the port. Then compare
Python and Rust outputs against fixed fixtures. Keep Windows live checks
explicit and separate from default unit tests. Never run capture to validate
this migration. Never simulate input or change power and locking settings.

After a toolchain or path change, run the fresh Cargo fixture from the environment
procedure. Require compiler launch, build-script execution, linking, and Win32
probe execution. Reuse unchanged machine evidence for documentation work.
Record commands, paths, versions, exit codes, source identity, and limits.

Keep each slice small enough to restore the previous accepted implementation.
Retain the Python launcher until R4 passes. Do not put an automatic Python
fallback in the native endpoint. A rollback to Python restores the earlier
product, not a Rust-only completion claim. Preserve shared logs during rollback.

R6 must check a controlled process environment without Python available to the
product. Do not uninstall machine Python. Inspect source references, selected
build targets, dependencies, child images, and required test commands. An
unavailable PATH entry alone does not exclude a hidden absolute Python path.
Run the required app tests and cache-only tool tests without Hermes or TypeSafe.
Check optional external integration separately.

This review runs no Cargo build, helper, application, power test, probe, or
capture test. A native build will not prove idle, lock, sleep, or device-policy
behavior. The historical unknowns remain open.

## Review checks

Three Hermes worker runs used `gpt-5.6-luna` with `openai-codex`.
Each worker returned a report and exited with code zero.

| Scope | Worker session | Parent review |
| --- | --- | --- |
| Runtime and lifecycle | `20260922_091743_577659` | Confirmed blocking readiness, partial power cleanup, forced Stop, and the transitional build gap. |
| Launcher and build | `20260922_091746_f902bc` | Confirmed fixed paths, explicit runtime targets, and first-build needs. Corrected existing-instance window semantics. |
| Documents and tools | `20260922_091744_489b44` | Matched all 13 owned Python files. Separated historical probes from current acceptance. |

The parent checked retained findings against source. Worker reports are review
input, not runtime evidence. The parent did not accept custom SHA-256 or JSON
code merely to avoid crates. The plan also rejects a new launcher output root
without a demonstrated need. Explicit target selection keeps the current path.

The parent checked local document links, source-reference bounds, and inventory
coverage. It also checked source hashes and Git differences. Application source
and build files remain unchanged. The README correction changes its current
hash; the earlier research hash record still describes its original snapshot.
No TypeSafe scoring round ran. No native behavior check passed in this review.

## Primary references

- [Cargo build](https://doc.rust-lang.org/cargo/commands/cargo-build.html): repeated target selection, locked builds, and offline dependency limits.
- [PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest): power-request handle ownership.
- [PowerClearRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powerclearrequest): request cleanup.
- [SetConsoleCtrlHandler](https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler): direct console control behavior.
- [HandlerRoutine](https://learn.microsoft.com/en-us/windows/console/handlerroutine): handler thread and close-event limits.
- [Rust process exit](https://doc.rust-lang.org/std/process/fn.exit.html): no stack-destructor execution on explicit process exit.
- [TypeSafe API](https://docs.typesafe.ai/api): direct HTTP transport without the Python SDK.
- [Hermes Python library](https://hermes-agent.nousresearch.com/docs/guides/python-library): external Python implementation boundary.
