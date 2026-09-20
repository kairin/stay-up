# stay-watch acceptance vectors

These are proposed fixtures, not executed tests.

Design rules stay in [stay-watch-plan.md](stay-watch-plan.md).
Current machine results stay in [stay-watch-feasibility.md](stay-watch-feasibility.md).

Unless a row says otherwise, time starts at `t=0`.
The test target is 10 minutes.
Initial required states are known.
No input event occurs.
Power and input adapters can use deterministic simulation.
Separate real-device checks remain required.

Task IDs name later implementation work on the stay-up board.
This file does not record board status.

## V1 / `t_c466d6a8`

At `t=0`, raw idle onset is `-120s`.
Start the test at `t=30s` with a 600s target.

Without a start-input event:

- At `t=30s`, raw idle is 150s and test coverage is 0s.
- At `t=600s`, raw idle is 720s and test coverage is 570s. The target is not reached.
- At `t=630s`, raw idle is 750s and test coverage is 600s. The target is reached.

In the observed Start-input branch, input at `t=30s` resets raw idle to 0s.
At `t=630s`, raw idle and test coverage are both 600s.
Do not hide the start input.

Fixture: deterministic clock/input fixture. Real input integration is separate.

## V2 / `t_e620a0cf`, `t_28377916`

Target is 30 minutes.
`t=0` is AC. `t=29m` is battery. `t=30m` is AC.

Inspect at `t=59m`. Segments are:

- AC `0..29m` (29m)
- battery `29..30m` (1m)
- AC `30..59m` (29m)

Neither reaches 30 minutes. Do not sum the durations.
At `t=60m`, the current AC segment reaches 30 minutes and may report the first AC success.

Fixture: deterministic power adapter. Real AC/battery integration is separate.

## V3 / `t_e620a0cf`, `t_c466d6a8`

`t=0` is known AC. `t=4m` is unknown. `t=7m` is known AC.

Inspect at `t=13m`. Confirmed segments are `0..4m` (4m) and `7..13m` (6m).
Unknown coverage is 3 minutes.
There is no 10-minute success. Do not sum the segments.

Fixture: deterministic power/event adapter. Real device integration is separate.

## V4 / `t_e620a0cf`

Attach process A at `t=0` with handle identity A.
Record exit at `t=40s`.
Then present process B with a reused PID at `t=50s`.

Helper-required coverage ends at 40s.
B is never attached by PID alone.

Fixture: deterministic process-event fixture.

## V5 / `t_1f0a1839`

Last trustworthy observation is at `t=10s`.
A required event is lost at `t=12s`.
Latch `RECORDING INCOMPLETE` immediately.
The sink recovers at `t=20s`.
Required states re-establish at `t=25s`.
Inspect at `t=35s`.

Confirmed intervals are `0..10s` and `25..35s`.
Do not sum them.
Sink recovery alone is insufficient.

Fixture: deterministic queue/state fixture.

## V6 / `t_1f0a1839`, `t_fcc30590`

Branch A: the image queue overflows at `t=40s`.
Record a screenshot gap while live sensor state continues.

Branch B: a durable event-log write fails at `t=45s`.
Latch sticky `RECORDING INCOMPLETE`.
Expose the durable evidence gap.
Keep live state separate.

Do not invent repair.
Do not claim that lost records were persisted.

Fixture: deterministic queue and sink-failure fixtures.

## V7 / `t_fcc30590`

Tracking at `t=0` creates no capture resources.
An explicitly invoked test at `t=10s` may attempt its initial image.
If visibility or freshness is unverified, reject setup and return to tracking.

In a valid setup, a later hidden, stale, or uncertain image at `t=30s` is retained as invalid/unverified.
Exclude it from valid screenshots.
Independently observed objective state is unaffected.

A rejected initial-image attempt is distinct from ordinary tracking.
Tracking must create no capture resources.
An explicitly invoked test may attempt its initial image before it rejects setup.
Hidden, stale, invalid, or uncertain content cannot count as verified evidence.

Fixture: initial setup and image-status simulation. Visible-terminal integration is separate.

## V8 / `t_fcc30590`

End an active test explicitly at `t=60s`.
Deliver a delayed event at `t=61s`.
Finish pending writes as specified.
Start no new capture from the late event.
Continue tracking with saved evidence retained.

Fixture: deterministic event fixture.

## V9 / `t_fcc30590`, `t_28377916`

At `t=600s`, record `target reached` as a milestone.
Keep the test active.
Send an explicit End test control at `t=650s`.
End the test then.
Retain the earlier milestone.

Exit and interruption are separate end-path variants.
Target attainment alone never ends the test.

Fixture: deterministic timer/terminal-event fixture.

## V10 / `t_1f0a1839`, `t_fcc30590`

Write complete JSONL through `t=30s`.
Truncate only the tail at `t=31s`.
Then manually relaunch at `t=60s`.

Mark the prior test interrupted.
Retain complete records.
Do not resume the test.
Do not restart its helper.

Fixture: deterministic file fixture.
