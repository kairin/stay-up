# Visual refresh plan

Commit `fed8eb5` (`feat: add native output panes`) is the accepted working
baseline. The user accepted it on 20 September 2026. Preserve the
[baseline contract](native-output-panes.md#accepted-working-baseline).

This plan controls presentation work. The historical
[observer proposal](stay-watch-plan.md) does not override it.

## Scope

- Preserve `keep-awake.py` and `monitor-helper.py`.
- Preserve manual launch, arguments, log format, and heartbeat interval.
- Preserve timed exit, idle reset, X-to-minimize, and Stop behavior.
- Keep one Rust window with status, helper output, and the heartbeat log.
- Keep both native text panes read-only, selectable, scrollable, and resizable.
- Do not add capture, simulated input, power requests, startup entries, or policy changes.
- Keep user-supplied media in documentation only.

A presentation change must not alter process ownership, launch, shutdown, or
cleanup. A change to those areas needs separate regression checks.

## Window design

Use the existing responsive native Win32 layout. Keep these elements:

- a running-state header.
- helper and monitor process identifiers.
- a large input idle timer.
- a keyboard-accessible Stop button.
- helper-output and heartbeat-log panes.
- a central Split slider.

Use the system UI font, clear spacing, and text with each status color. Keep the
timer as the most prominent value. Do not label it as uptime, unlocked time, or
certified human inactivity.

Support keyboard focus, high contrast, resizing, and Windows display scaling.
Avoid animation, transparency, a custom title bar, and a faster refresh rate.
The [layout reference](ui-layout-reference.md) records current dimensions. The
Rust source is authoritative.

## Terminal windows

The two Python processes are required. Visible terminal windows are not
required for their logic. The accepted baseline suppresses those windows and
shows the useful output in the Rust window.

Do not add terminal placement or global terminal settings. If launch flags
change later, check discovery, the PID handshake, error handling, and shutdown.

## 4. What does logging do now?

The launcher selects `logs/keep-awake.monitor.log`. The monitor
appends UTF-8 records with local ISO 8601 timestamps and UTC offsets. It opens,
flushes, and closes the file for each record. This does not guarantee a disk
`fsync`.

The log can contain:

- `monitor started`, with the helper process ID and interval.
- `OK`, when the original process handle remains active.
- `STOPPED`, when the monitor observes helper exit.
- `ERROR`, after an unexpected wait result.

The first `OK` follows startup. Later checks occur about every 60 seconds.
Scheduling can change this interval. Runs share one file, and the file has no
rotation or run identifier.

A heartbeat proves process life only. It does not prove Windows power-request
state. It does not record input idle time, display state, lock state, sleep, or
screenshots. Stop ends the monitor before the helper, so the final `STOPPED`
record is not guaranteed.

The visual refresh must keep this format and these limits. It must not show a
logging-health claim that the application does not measure.

## Acceptance

A presentation change passes when it:

1. preserves the accepted single-window layout and both output panes.
2. preserves helper arguments, the PID handshake, and process ownership.
3. preserves heartbeat format, interval, and shared-file behavior.
4. preserves idle reset, timed exit, X, and Stop behavior.
5. keeps text visible at 100%, 150%, and 200% scaling.
6. keeps controls usable with the keyboard.
7. adds no capture resource or hidden observer feature.

Use the approved Rust paths for application checks. Documentation-only changes
need link and formatting checks. They do not need a new runtime session.

## Known limits

- The idle timer starts with the application.
- A process ID does not prove logging health.
- The launcher does not continuously check log freshness.
- The Stop order can omit a final `STOPPED` record.
- Device policy can limit accepted Windows power requests.
- Broader lock, sleep, and idle behavior remains unproved.

The [observation log](observations.md) records completed checks and open items.
