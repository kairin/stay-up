# Historical stay-watch observer proposal

> The [visual refresh plan](visual-refresh-plan.md) controls current work.
> Screenshot logging, image capture, and capture tests are withdrawn.
> This document records an earlier observer design. It is not an implementation
> specification.

The later observer was not implemented. The current Rust application starts the
two existing Python helpers and shows their output. See the
[feasibility record](stay-watch-feasibility.md) for historical probe results and
the [observation log](observations.md) for current application checks.

## Purpose of the historical design

The proposed observer would measure input inactivity, display state, session
state, power state, and optional helper-process life. It would make no power
request, simulate no input, and change no Windows setting.

The design kept these measurements separate:

- elapsed observer time;
- helper-process life;
- continuous input idle time;
- continuous awake time;
- continuous display-on time;
- continuous unlocked time;
- suspended time and observation gaps.

An hour of helper life would not prove an hour of continuous idle operation.
Separate qualifying intervals would not be added together.

## Observation rules

A result would qualify only while all required states were known. A display,
session, power-source, or event gap would end confirmed coverage. The observer
would keep earlier valid milestones and record the gap.

Power-source changes would split qualifying intervals. They would not reset the
input idle timer, helper-life timer, or total elapsed timer. Unknown power
source would end confirmed condition coverage.

The event path would use bounded queues. Queue overflow or log failure would
produce an explicit incomplete result. The application would not silently lose
a required observation.

The observer would prefer Windows events. A bounded polling fallback could
confirm state when an event source was unavailable. The record would identify
the source and its limits.

## Helper ownership

Tracking would not start the helper. The observer could attach to a helper that
the user started. A later option could start the unchanged helper as an owned
child.

The observer would stop only a child that it started and still owned. It would
leave separately started helpers running. Cleanup would use verified process
handles and a bounded timeout.

These rules remain useful design guidance. They do not change the current
launcher contract or prove that every cleanup case passed.

## Storage and privacy

The proposed event log would contain measured states, timestamps, test identity,
and known gaps. It would not contain keystrokes, image data, video, or user
content. The user would control retention.

The withdrawn design also proposed PNG screenshots during explicit tests. Those
requirements, their queues, and their acceptance gates are no longer in scope.
Do not allocate capture resources or treat the old capture probes as current
requirements.

## Historical acceptance model

The design separated four results:

1. The measured outcome.
2. Observation coverage.
3. Evidence completeness.
4. The end reason.

A passed duration would require one continuous interval with all required
conditions known. A stopped helper, lock event, display-off event, suspend gap,
or observation loss could end the interval.

The [acceptance vectors](stay-watch-acceptance.md) preserve the unexecuted test
cases. They are historical planning records. They do not show current task
status.

## Current boundary

Preserve `keep-awake.py`, `monitor-helper.py`, the root launch command, and
owned-child behavior. Any future observer must remain passive. It must make no
power request, simulate no input, or change a power or locking setting.

A working Rust build proves only that the native toolchain can build and run a
Win32 program. It does not prove input, lock, sleep, idle, or helper behavior.
