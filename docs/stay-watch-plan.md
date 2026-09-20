# Historical stay-watch observer proposal

> **Superseded scope:** the [visual-refresh plan](visual-refresh-plan.md) controls current work.
> Preserve the working launcher and both Python helpers. Improve the Rust window without changing their behavior.
> Screenshot logging is removed, including explicit-test captures, PNG storage, image queues, and capture feasibility gates.
> The screenshot instructions and terminal-first layout below are historical, not implementation requirements.
> Other observer features remain deferred. This document is retained to explain earlier probes and decisions.
> The quoted implementation prompt at the end is also historical and must not be used as a current task instruction.

Status at the time of this proposal: first launcher exists. The later observer is not implemented.
Native feasibility probes from 20 September 2026 are in [stay-watch-feasibility.md](stay-watch-feasibility.md).
Remaining open checks are listed there.
Updated: 20 September 2026.

This plan contains the design rules, including power-source intervals, observation-loss handling, and observer-visibility checks.
Unexecuted time-based fixtures are in [stay-watch-acceptance.md](stay-watch-acceptance.md).
Current machine results are in [stay-watch-feasibility.md](stay-watch-feasibility.md).

The proposed utility is a separate Rust application named `stay-watch`.
It tracks input inactivity, Windows display and session states, and an optional stay-awake helper process.
An explicitly invoked test adds saved screenshots and a test result.
Normal tracking never captures screenshots, including images held only in memory.

The main test question is: how long does the computer remain awake, visible, and unlocked without observed input?
Overall helper runtime is a separate measurement.
An hour of keyboard activity does not establish that the helper prevents an idle timeout.

The existing [keep-awake.py](../keep-awake.py) requests that Windows keep the system and display awake.
The existing [monitor-helper.py](../monitor-helper.py) checks whether its selected process remains alive.
This plan adds a separate observer and leaves both implementations unchanged.
The [observation log](observations.md) explains the limits of the existing observations.

The current session uses Windows Terminal, with PowerShell inside it.
A process-tree check on 19 September 2026 established this relationship.
The screenshot target is the visible Windows Terminal window, including its title bar and visible borders.
Current window handles and process IDs must not become fixed application settings.

The user requirements below control the design.
Library choices, commands, and storage paths remain proposals until implementation planning.

| Requirement | Agreed behavior |
|---|---|
| Separate utility | Prefer Rust. Preserve the existing helper and heartbeat monitor. |
| Manual launch | The user starts each application. Neither starts at boot, login, or on a schedule. |
| Default mode | Track timers, activity, and Windows events without screenshots. |
| Test mode | Start image capture only after an explicit test command or control. |
| Screenshot interval | Save each successful five-second capture to disk during an active test. |
| Event evidence | Associate saved before images and fresh after images with relevant Windows events. |
| Image retention | Retain saved images until the user deletes them. No automatic deletion or overwrite. |
| Terminal display | Maintain a small block of colored status lines inside the existing terminal. |
| Terminal history | Preserve existing output, scrollback, and PowerShell command history. |
| Test independence | Make no power requests, simulate no input, and change no power or locking settings. |

The application has two modes: **tracking** and **test**.
Starting the application without a test command selects tracking.
Attaching to a helper does not start a test.
Inactivity, display changes, locking, and helper exit do not start a test either.

| Behavior | Tracking | Active test |
|---|---|---|
| Updating timer and status display | Yes | Yes |
| Input inactivity and return activity | Yes | Yes |
| Display, session, and power events | Yes | Yes |
| Optional helper observation | Yes | Yes |
| Small local event log | Proposed default | Required |
| Window screenshot capture | Disabled | Enabled when the desktop is available |
| Capture session or image cache | Disabled | Temporary buffers only, with successful captures saved to disk |
| Saved PNG images | None | Five-second samples and additional event images |
| Goal and result | No formal verdict | Outcomes against selected test conditions |

Tracking records a lock and the later return to an unlocked session.
It shows the elapsed interval, but creates no before or after image.
Its status display must say SCREENSHOTS OFF.
The disabled capture subsystem must not sample images and discard them in the background.

An active test adds evidence to the same tracking session.
Starting a test preserves the overall tracking timers and creates separate test counters.
Ending a test stops new captures and returns the application to tracking.
The saved images and completed test report remain on disk.

| Transition | Required behavior |
|---|---|
| Application starts normally | Enter tracking. Do not start the helper or a test. |
| User starts a test | Record its conditions, create a unique test folder, and enable capture. |
| Test setup cannot save evidence | Stay in tracking and show why the test could not start. |
| User requests a test while the desktop is unavailable | Stay in tracking. Do not defer an automatic test start until the desktop returns. |
| User input resumes during a test | Reset current idle time, preserve the completed interval, and keep the test active. |
| Power source changes during a test | Close the qualifying interval. Start a separate segment for the new known source. Keep the test active. |
| A required observation is lost | Mark coverage incomplete from the last trustworthy observation. Resume qualification only after required states are known again. |
| Session locks during a test | Record the event, link the saved before image, and suspend unavailable captures. |
| Desktop returns during that test | Continue the same test and request a fresh after image. |
| Test reaches its idle target | Record that the target was reached. Keep the test active until the user ends it. |
| User ends a test | Stop new captures, finish pending writes, save the report, and return to tracking. |
| User exits during a test | End the test as user-stopped, save available evidence, and exit. |
| Application crashes or computer restarts | Keep saved evidence. Mark the unfinished test interrupted on the next manual launch. |

A later manual launch starts in tracking unless the user explicitly invokes a new test.
It must not resume an interrupted test or restart a helper from a previous run.
Normal sleep or hibernation can preserve the existing processes and active test.
Their continuation after resume belongs to the manually started run.
It does not create a new run or test.

All screenshots must belong to an explicitly invoked test.
The capture worker checks the test identity before it starts an image request.
Ending a test cancels queued requests and prevents late event handlers from starting another capture.
An unfinished write can complete for an image captured before the test ended.
Its record keeps the actual capture time.

Both applications remain manual tools.
There are no startup entries, services, scheduled tasks, or automatic relaunches.
The observer can operate without the helper, including a baseline test of normal idle behavior.
A convenience command can launch the helper only when the user explicitly supplies that command.

The proposed first validation milestone covers baseline tests and attachment to a separately started helper.
Defer optional helper launching and owned-child cleanup until the core measurements pass their checks.
Explicit helper launching remains a planned capability, subject to its separate cleanup feasibility check.

The following commands describe the proposed interface.
They are not implemented commands.
The test subcommand explicitly invokes a test with screenshots.

```powershell
# Track without starting the helper or capturing images.
stay-watch.exe

# Track a helper that the user already started.
stay-watch.exe track --pid TEST-PID

# Test normal idle behavior without launching a helper.
stay-watch.exe test --idle-target 15m

# Test with an existing, manually started helper.
stay-watch.exe test --pid TEST-PID --idle-target 30m

# Later milestone: explicitly start a test and launch the unchanged helper.
stay-watch.exe test --idle-target 30m -- python .\keep-awake.py
```

The example process ID is a placeholder.
The interface should also offer explicit Start test and End test controls within a running tracking session.
The exact controls remain a design choice.
Starting or ending a test counts as user input and must not hide that activity from the idle measurement.
The idle target is a measurement threshold, not an automatic shutdown timer.

Attaching to an existing helper does not transfer ownership of that process.
Ending a test or exiting the observer leaves a separately launched helper running.
The observer follows the original process handle so that process ID reuse cannot select a different process.
It records process start, exit, and exit status when available.
Attaching later must not imply knowledge of earlier display or session behavior.

For the later helper-launch capability, record the exact executable, arguments, process identity, and startup output.
Ending the test alone leaves the child running under observation.
Exiting the observer should stop its owned child and allow the unchanged Python cleanup code to run.
Console signal routing and cleanup require a feasibility check before implementation commits to this behavior.
Do not silently detach an owned child or restart a child that exits.

Capture child output through one terminal writer to protect the status block.
The request-accepted messages from the helper establish reported startup success only.
They do not establish that Windows continuously honors each request.
The observer continues tracking after helper exit and records that the test conditions changed.

The recommended terminal library is **Crossterm**.
It supplies cursor movement, color, and buffered output for a small status block.
[Crossterm documentation](https://docs.rs/crossterm/latest/crossterm/).

Ratatui is an alternative if the interface needs more layout support.
Its inline viewport supports ordinary terminal output above the interface.
Indicatif suits a simple timer or progress indicator, but several independent states favor a custom status block.
[Ratatui inline viewport](https://docs.rs/ratatui/latest/ratatui/enum.Viewport.html), [Indicatif documentation](https://docs.rs/indicatif/latest/indicatif/).

Use about six lines with one update per second.
Keep names and numbers readable without special fonts.
Color can distinguish healthy states, durations, uncertainty, and observed failures.
Every color must have a text label.

```text
stay-watch  TRACKING          helper RUNNING        power AC
Tracking   01:23:45           Without lock          01:23:45
Input idle 00:18:12           Best idle + available 00:24:08
Display    ON                Session UNLOCKED      Suspends 0
Last event INPUT RESUMED      14:32:10              Locks    0
Evidence   SCREENSHOTS OFF    No test active
```

During a test, the display identifies the test and image status.
These values illustrate an active test.

```text
stay-watch  TEST ACTIVE       helper RUNNING        power AC
Test       00:18:12           Without lock          00:18:12
Input idle 00:18:12           Best idle + available 00:18:12
Display    ON                Session UNLOCKED      Suspends 0
Last event TEST STARTED       14:32:10              Locks    0
Evidence   SAVED 3s AGO       219 PNGs              Goal 30m
```

The renderer updates only the lines it owns.
It must not clear the screen, erase scrollback, or enter an alternate fullscreen buffer.
It handles resize, wrapping, and narrow windows without overwriting earlier output.
Normal terminal scrolling and selection remain available.
After exit, leave a summary and restore the cursor, colors, and any changed console modes.

The observer occupies the foreground command while it runs.
The user can use another tab for other commands.
During a test, a tab change can make the observer invisible to the capture target.
The capture rules below require verified observer content before an image counts as valid evidence.
Redirected output uses occasional plain status records without cursor controls.
Window screenshots require a supported visible terminal target.

Each timer needs a clear scope and reset rule.
The overall tracking session and each test have separate counters.
A qualifying interval starts no earlier than its scope and reliable observation coverage.

| Measurement | Meaning |
|---|---|
| Tracking elapsed | Time since the observer run started, including suspended time. |
| Test elapsed | Time since the active test started, including suspended time. |
| Helper elapsed | Elapsed lifetime of the selected helper. Freeze this value when it exits. |
| Without lock | Continuous observed unlocked interval within the current scope. |
| Input idle | Time since last observed input, with gaps or unknown input origin identified. |
| Idle while available | Continuous time without observed input, with display on, session unlocked, and system awake. |
| Longest qualifying interval | Best continuous idle-while-available interval within the current scope, reported separately for each known power source. |

For a helper test, qualifying time also requires the selected helper to remain running.
The display distinguishes all-session counters from test counters.
Starting a test does not transfer an earlier tracking interval into its result.
When activity resumes, reset the current idle interval and preserve its completed duration.

A display-off, lock, or suspend event ends the current qualifying interval.
An observation gap ends its confirmed coverage.
Dimmed display status is a separate warning unless the selected conditions require full brightness.
The without-lock timer does not reset merely because the display turns off while the session stays unlocked.

A change between AC and battery power ends the current qualifying interval and starts a separate condition segment.
An unknown power source ends confirmed condition coverage until the source is known again.
These boundaries do not reset the input-idle, without-lock, helper-lifetime, or overall elapsed timers.
Report the longest continuous qualifying interval and target result separately for AC and battery power.
Never add durations across segments, including separate segments that use the same source.
For example, 29 minutes on AC followed by one minute on battery establishes no 30-minute result for either source.
Keep earlier valid milestones under their original conditions.
Label a test that crosses sources as mixed conditions.

The application cannot execute while the system hibernates.
After resume, calculate elapsed time from Windows counters that account for suspended time.
Use readable timestamps for event records and monotonic counters for durations.
Detect clock changes instead of interpreting them as activity or sleep.
Windows also supplies an unbiased counter that excludes sleep and hibernation.
[Windows interrupt-time documentation](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryunbiasedinterrupttime).

Use native Windows notifications for display, session, and power changes where available.
Record initial state separately from transitions.
Use a hidden native window and event loop where the notification APIs require them.
Do not register a service to receive these events.

| Event | Interpretation |
|---|---|
| Display dimmed | Brightness state changed. This does not establish a lock. |
| Display off or on | Windows reported a session-display transition. |
| Session locked | The observed session became locked. |
| Session unlocked | Windows reported that the session became unlocked. |
| Suspend or resume | A power transition occurred. Classify its type only when the evidence supports it. |
| Session disconnect or reconnect | Connection state changed, including remote-session changes. |
| Power source changed | Record the source and close the qualifying interval. Start a new condition segment when the source is known. |
| Input resumed | Preserve the completed inactivity interval and start a new one. |
| Helper exited | Record the exit and end coverage that requires a running helper. |
| Observation unavailable | Record an unknown interval instead of assuming healthy state. |

Windows supplies separate lock/unlock and display-state notifications.
Use session-scoped display notifications for this interactive application.
Do not infer these states solely from screenshot brightness.
[Session notifications](https://learn.microsoft.com/en-us/windows/win32/termserv/wm-wtssession-change), [Display notifications](https://learn.microsoft.com/en-us/windows/win32/power/power-setting-guids).

A generic suspend event does not identify hibernation by itself.
Use "suspend observed, type unknown" when classification is unavailable.
A black screen saver, disconnected monitor, and physical monitor power button can differ from Windows display-off state.
Modern Standby and multiple displays need checks on the actual computer.
Do not interpret an unexplained scheduling gap as a confirmed sleep event.

Windows Raw Input is the proposed source for keyboard and pointing-device activity.
It supports background input observation after registration.
Check keyboard, external mouse, and laptop touchpad coverage on this computer.
[Raw Input documentation](https://learn.microsoft.com/en-us/windows/win32/inputdev/about-raw-input).

Use GetLastInputInfo as a fallback and cross-check.
It reports input within the calling session and can include software-generated input.
Handle its timestamp behavior and counter wrap explicitly.
[GetLastInputInfo documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getlastinputinfo).

Call the measurement input idle, rather than certified human inactivity.
Software and virtual devices can generate input, and a hardware mouse jiggler can resemble a physical mouse.
Record only event times and broad device categories, not typed characters or passwords.
Batch frequent movement events to avoid a log entry for every mouse packet.
Record gaps in input observation while the secure desktop is active.

Record the session unlock event separately from the first input observed after it.
Do not claim that the observer saw the input used to authenticate.
Starting with unknown input time requires an unknown value or an observed lower bound.
Do not invent activity times from an assumed login or launch time.

Screenshot capture exists only inside a test.
Each successful sample goes to disk immediately through the evidence writer.
A temporary image buffer supports encoding, but is not the evidence record.
The application reports an image as saved only after its file write completes.

Use a unique test directory and unique PNG names containing time and sequence information.
Write each image through a temporary file, flush it, and publish the completed file atomically where supported.
Incomplete files must not appear as successful screenshots.
A sudden power loss can still lose an unfinished write.
The design cannot guarantee survival of physical disk failure.

Successful saved files persist after application exit or restart.
The application never automatically deletes evidence or silently overwrites it.
At five-second intervals, a continuously available desktop produces about 720 scheduled screenshots per hour.
Startup, event, and final captures can add images.
Measure actual file sizes before estimating storage use.

At test start, draw the test status and save an initial image with verified observer visibility and freshness.
If that image cannot be verified or saved, return to tracking and report the test setup failure.
During the active test, save a new sample every five seconds when the target is available.
Do not recover missed samples by capturing a burst after resume.

On dimming, display-off, lock, or suspend, link the most recent valid saved image from before the event.
Attempt an extra immediate screenshot when possible.
Label an image captured after the event as an event-time image, not a before image.
The event handler must not wait for slow capture or PNG encoding.

After a session unlock, update and flush the terminal display before requesting a fresh screenshot.
Wait for the desktop and target window to become available, with bounded retries.
After display-on or resume without locking, save a corresponding return image.
If the session remains locked after resume, defer desktop capture until it is accessible.
Keep the original event time and the actual later capture time.

Windows reports a session lock after that lock occurs.
It does not guarantee an accessible desktop at notification time.
Normal suspension allows little processing time, and critical suspension can occur without advance notice.
These limits justify periodic saved images during a test.
[Session event semantics](https://learn.microsoft.com/en-us/windows/win32/termserv/wm-wtssession-change), [Power-event handling](https://learn.microsoft.com/en-us/windows/win32/power/system-power-management-events).

Five seconds is the capture target, not a guaranteed maximum age for the before image.
The latest valid image can be older if the window or desktop is unavailable.
Always report the actual image age.
Never substitute a blank, stale, reconstructed, or unrelated image as successful fresh evidence.

Each screenshot record contains the test ID, sequence, capture timestamp, associated event IDs, and image path.
Also record the relevant timer values, window identity, capture method, dimensions, and known visibility limits.
Record image validity and the reason for any unverified image separately from file-write success.
Store event timestamps independently from image timestamps.
Record the last successful render time where available so a delayed terminal refresh remains visible in the evidence.

Retain each observed Windows transition separately, even when several transitions belong to one incident.
The bounded-queue rules below define how to report loss when full retention becomes impossible.
A display-off, lock, and suspend sequence can share one saved before image.
Retain separate event times and the shared image relationship.
Events outside a test receive no image association from a later test.
There is no retrospective screenshot of an event that occurred during tracking.

Image failures affect evidence completeness, not the truth of an observed Windows event.
Continue the timers and event log when capture fails.
Show the failure reason, including unavailable desktop, wrong window, write error, or full disk.
Use bounded retries or wait for a relevant state change.
Do not repeat a failed capture in a busy loop.

If the disk is full, mark the evidence incomplete and preserve existing files.
Do not delete earlier screenshots to make space.
The user can end the test and continue tracking.
If the test remains active, capture can recover when storage becomes available.
The report retains the gap even after recovery.

Select the visible Windows Terminal window that contains this utility.
Use stable window identity during a test and detect closure or replacement.
If several windows are plausible, require explicit target selection before the test starts.
Do not automatically capture a different foreground application.

Do not rely only on GetConsoleWindow to find the target.
In a pseudoconsole, it can return an invisible window handle.
[Console-window documentation](https://learn.microsoft.com/en-us/windows/console/getconsolewindow).

Include terminal contents, the title or tab bar, and visible outer borders.
Check cropping after resizing and movement between monitors with different scaling.
Window frame bounds can help identify the capture rectangle.
[Windows frame bounds](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute).

Windows Graphics Capture is one candidate for the capture backend.
A visible screen-region capture is another candidate when the whole window is unobscured.
Check output quality, window-border coverage, permission behavior, and resource cost on this computer.
[Microsoft window-capture overview](https://blogs.windows.com/windowsdeveloper/2019/09/16/new-ways-to-do-screen-capture/).

Do not assume PrintWindow works for this terminal without examining its images.
It is synchronous and must not block the event thread.
[PrintWindow documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-printwindow).

The initial supported setup keeps the observer tab selected and the status block visible.
A hidden tab cannot appear in a screenshot of the outer window.
Minimization, overlapping windows, and terminal scrollback can prevent useful visual evidence.
Report known limitations and keep event records when images are unavailable.
Never force focus, switch tabs, restore windows, or simulate input to get an image.

A stable outer window handle does not establish which tab or content appears in a capture.
Windows Terminal supports [tab selection within one window](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments#focus-tab-command).
The [window-capture API](https://learn.microsoft.com/en-us/windows/win32/api/windows.graphics.capture.interop/nf-windows-graphics-capture-interop-igraphicscaptureiteminterop-createforwindow) targets a window handle.
For each test capture, establish that the image shows the observer status and reflects its expected render state.
The visibility check belongs to active-test capture.
It must not introduce image sampling in tracking mode.
If visibility or freshness cannot be established, mark the image unverified and exclude it from valid evidence.
Retain any file already saved, with its unverified status and reason.
Do not count it as a valid before or after image.
Continue independent Windows event observation during an image gap.

Before selecting a capture backend, test switching away from and back to the observer tab within the same window.
Also test scrollback, minimization, and cases where visibility cannot be established.
The method must distinguish a completed file write from valid observer evidence.
This feasibility gate remains open until those checks pass.
A failed gate prevents claims of verified screenshot support.

The proposed output root is local/stay-watch/ inside this repository.
The existing .gitignore excludes /local/, so runtime evidence stays outside Git by default.
The plan belongs in docs/stay-watch-plan.md and can be versioned.
The output root should accept an explicit override.

```text
docs/
  stay-watch-plan.md
local/
  stay-watch/
    <run-id>/
      events.jsonl
      tests/
        <test-id>/
          screenshots/
            <timestamp>-000001.png
            <timestamp>-000002.png
          summary.md
```

Each observer run has one authoritative append-only `events.jsonl`. Test events remain in that stream and carry `test_id` when applicable. Separate session, test, and image manifests are unnecessary.

Run and test start records include the relevant power source, selected helper, idle target, and known initial sensor states. Each record contains:

| Field | Meaning |
|---|---|
| `seq` | Monotonic record sequence within the run. |
| `timestamp` | ISO 8601 time with offset. |
| `elapsed_ms` | Duration from the chosen monotonic clock, including suspended time. |
| `event` | The observed transition, interval, capture, or recording state. |
| `test_id` | Optional active test identity. |
| `details` | Relevant bounded metadata. |

Append and flush important transitions promptly. Log run and test starts and ends, initial known states, meaningful idle-resume intervals, lock/unlock/display/suspend/resume/helper transitions, saved image relative path and capture time, image and sensor availability, recording failure and recovery, and a heartbeat once per 60 seconds with last-known input/idle and observer health. Do not log raw keys, mouse packets, or 1 Hz redraws.

Coalesce activity simply. Log resumption after at least 60 seconds idle and a test-end interval snapshot. The current idle timer resets on every observed input; completed intervals and the longest-interval calculation remain retained and updated. Do not add a configurable logging framework, database, cloud sink, schema registry, or exhaustive inventory.

Record power-source boundaries and preserve the condition segment associated with each qualifying interval and milestone.
Coalescing input activity must preserve the timing needed to reset idle measurements and calculate completed intervals.

A saved image means its completed write and flush. A log, metadata, or summary write failure sets a sticky visible `RECORDING INCOMPLETE` state. Continue live UI and event observation with bounded memory. If the sink recovers, record the known failure period without claiming lost events were recovered.

An unclean exit may leave a partial final JSONL record. Retain complete records, treat the trustworthy tail as ending at the last relevant observation, and leave the rest unknown rather than inferring sleep or death. A new manual launch starts tracking unless the user explicitly invokes a new test command; it does not autoresume.

A report separates four fields: (A) observed objective outcome, (B) observation coverage, (C) screenshot completeness, and (D) end reason. Screenshot gaps do not erase an otherwise observed outcome, but unresolved required-state coverage prevents confirmed success for that interval. Use labels such as target reached, goal not met, incomplete, interrupted, and user-stopped. Record both first failure and longest qualifying interval when a test continues after interruption. Keep observation separate from inferred cause.

Report outcomes by power source and identify mixed-condition tests.
A target requires one continuous qualifying interval under the reported conditions.
Report unverified saved images separately from valid screenshots.
An image gap does not invalidate an independently observed Windows state.

Ending a test closes the current interval at the test boundary. If no activity resumed, label it still idle when observation ended; a real end-control input is ordinary observed input and resets the current idle timer. Never fabricate `INPUT RESUMED`. Idle onset before a test remains distinct from the portion observed during that test. Target reached is a milestone, not an automatic end.

For a baseline with no selected helper, report `no helper selected; other inhibitors unverified` unless the user establishes that condition. Do not add process surveillance, automated killing, or power-policy audits. Recheck machine-specific settings before treating them as current conditions.
Display and system power requests have specific Windows limits.
Battery operation under Modern Standby and user-initiated sleep require separate test conditions.
Do not describe these as equivalent to an automatic idle test on AC power.
[PowerSetRequest behavior](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest).

Use native notifications and ordinary timers to limit resource use.
Refresh text about once per second and avoid elevated timer resolution.
Create capture resources only for an active test and release them when the test ends.
Suspend visual refresh and unavailable captures while the desktop is inaccessible.
Bound event queues and image buffers so slow disk writes cannot consume unlimited memory.

Queue overflow must not block the native event loop or silently discard required observations.
If a required observation is lost, immediately set the visible `RECORDING INCOMPLETE` state outside the saturated queue.
End confirmed coverage at the last trustworthy observation before the loss.
Keep bounded loss metadata outside that queue, including known times, affected sources, and counts when available.
When recording becomes available, write an `OBSERVATION_GAP` record with that metadata.
Establish the current required states again before starting a new qualifying interval.
Do not infer missed transitions or claim that recovery repairs the earlier gap.
Previously confirmed intervals remain valid unless the loss affects their coverage.

Image-queue overflow creates a screenshot gap.
It does not erase independent sensor observations.
A log-write failure creates incomplete durable evidence even if live observation continues.
If observations also become unavailable, apply the observation-gap rules above.

Screenshot capture is likely to dominate the resource cost.
Measure CPU use, memory, disk writes, and power behavior separately in tracking and test modes.
Make no keep-awake requests and generate no input.
Check whether rendering or capture changes normal idle behavior despite those restrictions.
A baseline that never reaches normal idle behavior cannot establish the effect of the helper.

Before task decomposition, establish feasibility on this computer.
The managed application policy must permit the Rust executable to run.
Ordinary tracking should not require administrator access.
If a sensor needs unavailable permissions, record the limit instead of reporting a healthy state.
Do not change policies or bypass restrictions to make the test pass.

These acceptance checks define the proposed result.
They are checks for later implementation, not tests executed while writing this plan.

| Check | Expected result |
|---|---|
| Start normal tracking | Status and events work. No capture session, images, or image buffers exist. |
| Lock and return during tracking | Events and timers update. No screenshots appear. |
| Attach to helper | Tracking remains the mode until an explicit test starts. |
| Start test after an earlier tracking event | New evidence starts now. No claimed image exists for the earlier event. |
| Start active test | Initial and five-second images persist in its unique directory. |
| End test | New captures stop. Tracking continues and saved files remain. |
| Receive delayed event after test end | No new capture starts from that event. |
| Run two tests in one session | Evidence and counters remain separate. Tracking timers continue. |
| Return through keyboard, mouse, or touchpad | Current idle resets and the completed interval remains recorded. |
| Lock and return during a test | Before and after records contain actual timestamps and honest availability status. |
| Suspend, hibernate, or resume | Elapsed duration remains correct. Labels match the available evidence. |
| Change system clock | Duration counters remain consistent and the clock change is identifiable. |
| Change AC to battery and back | Each change closes the qualifying interval. Results remain per source and contiguous segment. Other timers and earlier valid milestones remain intact. |
| Reach 29 minutes on AC, then one minute on battery | Neither source receives a 30-minute result. Returning to AC starts a fresh qualifying interval. |
| Power source becomes unknown | End confirmed condition coverage. Start a fresh interval only after the source and other required states are known. |
| Helper exits | Record the original process exit. Do not attach to a reused process ID. |
| Resize or change scaling | Preserve earlier output and capture the intended window frame. |
| Switch tabs within the same window, then return | Detect missing or unverified observer content despite a stable window handle. Resume valid evidence only after visibility and freshness are established. |
| Scroll into history, minimize, or lose visibility certainty | Mark affected images unverified. Retain saved files, exclude them from valid evidence, and continue independent event observation. |
| Initial image cannot establish observer visibility | Reject test setup with a reason and return to tracking. |
| Overflow a required-observation queue | Show incomplete coverage immediately. Preserve bounded loss metadata, record the gap when possible, and re-establish states before a fresh qualifying interval. |
| Overflow only the image queue | Record a screenshot gap without invalidating independent Windows observations. |
| Image or log write fails | Preserve complete earlier records, show sticky RECORDING INCOMPLETE, continue bounded live observation, and record recovery without claiming lost events were recovered. |
| Unclean exit | Retain complete JSONL records; treat the tail after the last relevant observation as unknown. |
| Test ends during idle | Close the current interval at the boundary without fabricating INPUT RESUMED. |
| Tracking or baseline without a helper | Show no helper selected; other inhibitors unverified unless established by the user. |
| Crash or restart | Saved files remain. Next manual launch does not restart the previous test or helper. |
| Stop observer attached to helper | The independently launched helper continues. |
| Later milestone: stop observer with an owned child | Establish graceful cleanup and console signal routing before enabling explicit helper launching. |
| Compare tracking and test baselines | Identify whether rendering or capture changes idle behavior without the helper. |
| Test helper under matching conditions | Measure idle display, session, and power outcomes independently. |

Start with a baseline under the same AC or battery conditions as the helper test.
Compare results only from continuous intervals under matching known power conditions.
Retain source changes in the report and do not combine intervals to reach the target.
Close or document applications that can affect idle behavior, such as meetings or media playback.
Compare tracking alone with test mode, then compare test mode with and without the helper.
Use intentional lock and sleep actions to check detectors separately from automatic idle outcomes.
A thirty-minute idle target is a proposed first helper test, subject to current timeout settings.

Remaining design choices are the exact in-session test controls and later graceful child-stop handling.
PrintWindow and screen-region BitBlt passed a marker test. Windows Graphics Capture remains untested.
Observer-visibility checks passed except return to the observer tab.
Queue-loss recovery and per-source interval boundaries also require the acceptance checks above.
Feasibility checks must also establish live touchpad events and Modern Standby runtime behavior.
Current machine results are in [stay-watch-feasibility.md](stay-watch-feasibility.md).
This document fixes no dependency versions, executable layout, or task assignments.

The following prompt carries the agreed scope into later implementation planning.

> Plan a separate Rust utility named stay-watch for PowerShell inside Windows Terminal.
> Preserve the existing keep-awake.py and monitor-helper.py implementations.
> Require manual launch for both applications, with no startup, login, scheduled, or automatic restart behavior.
>
> Default to tracking mode with a compact colored display, input-idle timers, Windows events, and optional helper observation.
> Preserve terminal history and update only the status lines owned by the utility.
> Tracking must not create screenshots, image caches, or capture sessions, even when the system locks or sleeps.
>
> Enable screenshots only after the user explicitly invokes a test.
> Save every successful five-second screenshot directly to disk, including the terminal title bar and visible borders.
> Establish observer visibility and freshness for each test capture. A stable window handle alone is insufficient.
> Mark images unverified when their content cannot be established. Retain saved files but exclude them from valid evidence.
> Require a verified initial image before starting a test. Do not sample images in tracking mode to check visibility.
> Associate saved before images and fresh after images with display, lock, and suspend events.
> Keep actual capture times, image ages, and capture failures visible in one append-only run event stream.
> Retain saved evidence until the user deletes it.
> Record sequence, offset timestamp, suspended-time-aware elapsed duration, event, optional test ID, and relevant details.
> Separate objective outcome, observation coverage, screenshot completeness, and end reason.
> Bound queues without silent loss of required observations or a blocked event loop.
> On lost required observations, latch incomplete status outside the full queue and retain bounded loss metadata.
> End confirmed coverage at the last trustworthy observation.
> Record the gap when possible and re-establish states before qualification resumes.
> Distinguish observation loss from image-only gaps and log-write failures while live observation continues.
>
> Ending a test stops new captures and returns to tracking without deleting evidence.
> Continue the same active test after normal sleep or hibernation when its process survives.
> After a crash or restart, require a new manual launch and an explicit new test invocation.
>
> Measure helper lifetime separately from input inactivity, display state, session state, and suspended time.
> Preserve completed idle intervals when activity resumes.
> Report the longest continuous observed idle interval for each power source, with display on, session unlocked, and system awake.
> Split qualifying intervals at power-source changes. Unknown power source ends confirmed condition coverage.
> Never sum separate segments to meet the target.
> Preserve earlier valid milestones and label mixed-condition tests.
> Power-source boundaries do not reset input-idle, without-lock, helper-lifetime, or overall elapsed timers.
> Show uncertainty where observation is unavailable.
>
> Support baseline tests, attachment to a manually started helper, and an explicit command that launches the unchanged helper.
> Validate baseline and attachment first.
> Keep optional helper launching and owned-child cleanup for a later milestone.
> Do not start the helper merely because tracking starts or a process is absent.
> Keep separately launched helper processes running when the observer exits.
>
> Favor native Windows events and low resource use.
> Make no power requests, simulate no input, and change no power or locking policies.
> Establish executable, input, capture, and event feasibility before decomposing the first milestone.
> Establish child cleanup feasibility before decomposing the later helper-launch capability.
> Test observer visibility across tab changes, scrollback, minimization, and uncertain detection before claiming verified screenshot support.
