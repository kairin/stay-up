# Validation notes

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
