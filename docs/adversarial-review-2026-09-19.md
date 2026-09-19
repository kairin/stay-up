# Documentation adversarial review: 19 September 2026

Status: design corrections recorded. Implementation and runtime checks remain pending.

The review covered the README and all four first-party Markdown documents in `docs/`, including the uncommitted stay-watch plan.
It checked the helper scripts, runtime inventory structure and totals, selected upstream source, and Microsoft references.
Upstream documents served as evidence. The review did not examine every upstream document.
The review did not repeat runtime, idle, reboot, policy, or capture tests, or verify every artifact hash.

Two medium-priority specification gaps and one capture feasibility risk affected the [stay-watch plan](stay-watch-plan.md).
The existing usage and research documents distinguish historical observations, successful API calls, and pending idle tests.
The inventory and local runtime totals agree: 3,271 files and 2,319,009,392 bytes.

## Power conditions: medium-priority specification gap

The previous plan recorded power-source changes but did not close the qualifying interval.
A result could combine 29 minutes on AC power with one minute on battery power.
That would establish no 30-minute result under either condition.
Windows applies different [power-request limits on Modern Standby battery power](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest).

The revised plan closes qualifying intervals at power-source changes.
Unknown power source ends confirmed condition coverage.
Results use continuous intervals and remain separate for each source.
Separate segments cannot be added, even when they use the same source.
Earlier valid milestones remain valid under their original conditions.
Input-idle, without-lock, helper-lifetime, and overall elapsed timers do not reset solely because the source changes.

Status: corrected in the design.
Acceptance checks cover AC-to-battery-to-AC changes, unknown source, and the 29-minute plus one-minute example.
Runtime behavior remains untested.

## Event queue overflow: medium-priority specification gap

The previous plan required event retention and bounded queues without an explicit overflow rule.
Slow processing could lose a required transition while a report still showed continuous coverage.

The revised plan prohibits silent observation loss and a blocked event loop.
Lost required observations trigger visible incomplete status and end coverage at the last trustworthy observation.
Bounded loss metadata stays outside the saturated queue.
The observer records the gap when recording becomes available.
Qualification starts again only after required current states are known.
Recovery cannot establish what happened during the gap.

Image-only queue loss affects screenshot completeness.
A log-write failure affects durable evidence while live observation can continue.
These failures do not automatically erase independent sensor observations.

Status: corrected in the design.
Acceptance checks require separate observation-queue and image-queue overflow tests.
Implementation and recovery checks remain pending.

## Observer visibility: capture feasibility risk

A stable terminal window handle does not establish that the observer tab is visible.
Windows Terminal supports [tab changes within one window](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments#focus-tab-command).
The [window-capture API](https://learn.microsoft.com/en-us/windows/win32/api/windows.graphics.capture.interop/nf-windows-graphics-capture-interop-igraphicscaptureiteminterop-createforwindow) targets the outer window.
A file write can therefore succeed while the image shows different content.

The revised plan requires observer visibility and freshness checks for each active-test capture.
Unknown or invalid content cannot count as valid screenshot evidence.
Any saved file remains retained with its unverified status.
A verified initial image is required to start a test.
These checks must not introduce image sampling in normal tracking.

Status: the requirement is explicit, but feasibility remains unresolved.
Test tab changes and return, scrollback, minimization, and uncertain detection before claiming verified screenshot support.
Independent Windows observation continues during image gaps.

## Proposed implementation sequence

Validate baseline tests and attachment to a manually started helper first.
Defer optional helper launching and owned-child cleanup until the core measurements pass their checks.
Explicit helper launching remains in the planned scope.
Its console signal and cleanup behavior needs a separate feasibility check.

The [validation notes](validation.md) list pending checks.
The [historical research](research-2026-09-19.md) and [consolidation record](consolidation.md) retain their original evidence boundaries.
