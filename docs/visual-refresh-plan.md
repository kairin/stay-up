# Visual refresh plan and adversarial review

Status: planning only. No application behavior changed.
Baseline: `e9c8fad` on `main`.

## Scope and decisions

The user reports that the project works. Preserve that working system.
This plan controls the current visual refresh.
It replaces the screenshot requirements and terminal-first interface in the older [observer proposal](stay-watch-plan.md).
Other observer work remains separate, not a prerequisite for visual changes.

- Preserve `keep-awake.py` and `monitor-helper.py`.
- Preserve manual launch, helper arguments, heartbeat interval, and log format.
- Preserve the current idle reset rule, timed exit, X-to-minimize behavior, and Stop behavior.
- Do not add power requests, simulated input, startup entries, or policy changes.
- Remove screenshot logging from the active plan, including explicit test capture.
- Keep historical probes and evidence. Do not run or delete them during visual work.
- User-supplied issue media belongs to documentation, not application logging.

The recommendations below are proposals, not implemented features.

## 1. Are two terminals necessary?

**Finding:** two processes are useful. Two visible terminal windows are not required by the application logic.

[main.rs](../stay-watch/src/main.rs) starts the existing helper and monitor independently.
It does not explicitly launch `wt.exe`, request two windows, or assign window positions.
The GUI executable uses the Windows subsystem, but child Python processes remain console applications.
Their console windows depend on the process flags and Windows terminal configuration.

The helper's standard output goes to a pipe. The launcher reads its PID and discards subsequent output.
The monitor writes directly to a file. Its standard output and error go to the null device.
The helper's standard error also goes to the null device.
Consequently, visible child terminals offer little diagnostic value today.

The [issue photos](issue-media.md) show the Rust window beside two mostly blank terminal windows.
This supports the reported visual problem. It does not establish each window's process ownership.
The Python-discovery command can also create a transient console, depending on the launch environment.

**Recommendation:** keep both processes. Prefer one visible Rust window eventually.
First change only the Rust layout. Treat console suppression as a separate, reversible launcher change.

For that later change, evaluate Windows `CREATE_NO_WINDOW` on the Python discovery and child launches.
Keep `python.exe`, the arguments, PID handshake, output pipes, and file logging unchanged.
Do not replace the launcher with `pythonw.exe`, a shell wrapper, or a new process supervisor merely for appearance.
Console flags affect signal behavior, so they require a separate startup and shutdown check.
Do not promise that this is only a paint change.

## 2. Can terminals resize automatically?

**Yes, if visible terminals are deliberately retained.** This is optional and not recommended for blank windows.

Windows Terminal supports launch geometry through `--size` and `--pos`.
Size uses columns and rows, not the Rust window's pixel dimensions.
A dedicated `wt.exe --window new` launch can avoid reusing an unrelated terminal window.
This would change the launch chain, so it is not part of the first visual change.

For a confirmed, owned top-level window, Win32 `SetWindowPos` can set its bounds after creation.
Console-host windows and Windows Terminal windows need different ownership checks.
`GetConsoleWindow` alone does not reliably identify the visible Windows Terminal window.
The current Python PID is not necessarily the visible host's PID.

If implemented later:

1. Identify the exact window owned by this launch.
2. Wait for creation with a bounded timeout.
3. Apply the requested size once without activation or topmost behavior.
4. Leave the window unchanged if ownership is uncertain.
5. Let failure affect placement only, never helper operation.

Do not alter global Terminal profiles, console defaults, or unrelated windows.

## 3. Can windows move to specific screen locations?

**Yes.** Use the same ownership checks and `SetWindowPos` for an existing owned window.
The Rust window is simpler because the application already owns its window handle.

A later optional layout could place Rust at the upper right, with diagnostic terminals stacked below or beside it.
Use the selected monitor's work area, not hardcoded screen coordinates.
Account for the taskbar, negative monitor coordinates, display scaling, and disconnected monitors.
Clamp restored bounds to an available work area.
If the requested layout does not fit, leave the windows at usable default bounds.

Apply placement once at launch or through an explicit Arrange action.
Do not continuously move windows back after the user moves them.
Do not steal focus, force topmost status, or change another application's position.

**Recommendation:** default to normal Windows placement in the first visual change.
Consider saved placement for the Rust window later. Defer terminal arrangement unless the user wants visible diagnostics.

References: [Windows Terminal arguments](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments),
[SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos),
[process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).

## 4. What does logging do now?

The Rust launcher selects `local/stay-watch/keep-awake.monitor.log`.
[monitor-helper.py](../monitor-helper.py) opens this file in append mode for each record.
It writes UTF-8 text with a local ISO 8601 timestamp and UTC offset, flushes, and closes the file.
This is not an explicit disk `fsync` guarantee.
The launcher supplies a 60-second interval.

Current records are:

- `monitor started`: helper PID and interval.
- `OK`: the original process handle is not signaled, so the helper remains alive.
- `STOPPED`: the monitor observed the helper's exit.
- `ERROR`: an unexpected wait result.

The initial `OK` follows startup. Later checks occur about every 60 seconds, subject to scheduling.
The file is shared across runs, with no rotation or run identifier.
The repository ignores `local/`.
A standalone monitor uses the path supplied through `--log` instead.

### Limits that the interface must not hide

- A heartbeat proves process liveness, not that Windows honors every power request.
- It does not record idle intervals, lock/unlock, display state, sleep, or screenshots.
- The Rust UI currently has no persistent event log.
- The UI's Stop path kills the monitor before the helper. A final `STOPPED` record is therefore not guaranteed.
- A timed helper exit can also race with monitor cleanup before its next poll.
- The launcher discards error output. It does not surface monitor write failures or continuously verify log freshness.
- A displayed monitor PID is not proof of current logging health.

**Decision:** preserve the existing heartbeat log in the visual-only phase.
A log path or an Open log action can be proposed without labeling logging as healthy.
Do not add idle histories, JSONL, log rotation, or lifecycle repairs as hidden requirements of a visual change.

If event records are approved later, use a separate append-only local file.
Record only measured events, timestamps, run identity, and known recording gaps.
Keep the heartbeat format intact. Do not record keystrokes, screenshots, video, image buffers, or capture metadata.
The older proposal's PNG schedule, image queues, capture backends, and screenshot gates are withdrawn.
Removing them does not mean those tests passed.

## 5. Modern Rust window layout

The current [ui.rs](../stay-watch/src/ui.rs) uses one text block and a fixed-position Stop button.
It creates a 480 × 280 window and repaints the client area each second.
It has no responsive layout or explicit font hierarchy.
The issue photos show the result and the surrounding terminal clutter.

### Options

| Layout | Benefits | Costs and limits |
|---|---|---|
| Compact status card | Clear timer, few controls, small desktop footprint | Recommended. Uses existing information only. |
| Two-column dashboard | More room for details and a log panel | More screen space. A live log panel adds file-reading behavior. |
| Narrow toolbar | Minimal footprint | Less room for clear labels and accessible controls. Tray behavior would be new scope. |

### Recommended compact card

Start near 480 × 320 device-independent pixels, then check text fit at supported scaling levels.
Keep the native title bar and Windows resizing controls.
Use responsive rows rather than fixed text and button coordinates.

```text
┌─ stay-watch ──────────────────────────────┐
│ Session                                  │
│                                          │
│                 00:10:38                 │
│          Idle timer · since launch/input │
│                                          │
│ Helper PID                         13560 │
│ Monitor PID                        25736 │
│                                          │
│ [Details ▾]                  [Stop]      │
│ X minimizes. Stop ends both helpers.     │
└──────────────────────────────────────────┘
```

Numbers are illustrative. Do not hardcode them.
The existing timer starts at launch and resets after a changed last-input sample.
It does not initialize from the complete Windows idle duration before launch.
Do not relabel it as uptime, time unlocked, or certified human inactivity.

Use Segoe UI or the system UI font, with tabular digits for the timer.
Use an 8-pixel spacing grid, about 20 pixels of outer padding, and aligned labels.
Give the timer the largest type. Keep process identifiers secondary but selectable where practical.
Use a neutral background and one accent color. Pair every status color with text.
Keep Stop visible, keyboard-accessible, and separate from passive details.
Retain the exact existing X and Stop semantics.

Details can contain the full log path and current explanatory text.
An Open log action is optional and needs a missing-file error state.
Do not add green “Protected,” “Unlocked,” or “Logging healthy” badges without the corresponding evidence.

Support high contrast, keyboard focus, screen-reader labels, and 100%, 150%, and 200% scaling.
Use standard accessible controls for actions and important values where practical.
Avoid animation, transparency, a custom title bar, or a faster refresh rate.
Do not make dark mode a prerequisite for the first change.

### Rendering approach

Prefer the current Win32 window for the first iteration.
Change fonts, spacing, control layout, and painting without moving process or timer logic.
Avoid full-window erase on each tick where possible, to reduce flicker.
Native controls need less custom accessibility work than an entirely painted dashboard.

A Rust UI framework remains an alternative, not the default.
A framework migration adds dependencies, event-loop changes, build work, and shutdown integration risk.
Consider it only if the native layout cannot meet the agreed design and accessibility needs.

## Adversarial findings and minimal corrections

| Priority | Evidence | Risk | Minimal decision |
|---|---|---|---|
| High | `main.rs`: redirected child output. Issue #6: two blank windows. | Building terminal tiling solves a symptom with more launch complexity. | Preserve processes. Redesign Rust first. Evaluate console suppression separately. |
| High | `ui.rs`: `drop_state` stops the monitor before the helper. | A polished “Stopped and logged” message could claim a record that does not exist. | Preserve behavior. Document the missing-final-record limit. Defer lifecycle repair. |
| High | `ui.rs`: timer starts from `Instant::now`; monitor status is not rendered from a live health check. | New labels could overstate what the application measures. | Keep labels tied to current data. Do not invent health or lock states. |
| Medium | Older observer plan requires captures and a terminal interface. | Future work could restore a feature the user removed. | Mark it historical. Make this plan authoritative. Retire screenshot acceptance gates. |
| Medium | `ui.rs`: fixed button position and repeated whole-window repaint. | Cosmetic changes alone could retain clipping, flicker, and scaling failures. | Add responsive spacing, font hierarchy, and bounded repaint work. |
| Medium | Issue #6 includes a sign-in photo. Videos have no descriptive captions. | Media could imply causation or expose unrelated desktop information. | Label source and limits. Link originals. Do not call them controlled test results. |

## Proposed sequence and acceptance

1. Agree on the compact card. Use a static mockup before changing application code.
2. Change only Rust presentation. Preserve process, timer, log, X, and Stop behavior.
3. Check scaling, resize, keyboard access, contrast, and text clipping.
4. Compare helper arguments, heartbeat format and interval, timed exit, and Stop with the existing baseline.
5. If approved, suppress child consoles in a separate change. Check discovery, startup handshake, failures, and shutdown.
6. Add placement only if the user still needs it.

Application checks must use the repository's approved executable locations.
No new capture tests are required. Do not disturb the user's running helper merely to validate documentation.
An appearance change must not claim to repair pre-existing cleanup or logging limits.

## Review boundary

Examined: Rust launch and UI code, both Python helpers, current documentation, both issue bodies, and all four photos.
Retrieved: all four video attachments. Their container metadata identifies QuickTime media.
Not examined: video playback, live window ownership, live DPI behavior, or a new runtime session.
No Astra/Luna delegation tools were available. This was a direct bounded review, not a model-tier review or fleet run.
No application code, toolchain, process state, power setting, or board task changed.
