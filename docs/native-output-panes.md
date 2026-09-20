# Native output panes

## Accepted working baseline

On 20 September 2026, the user reported that the implementation was working
and explicitly confirmed it as the baseline. The accepted implementation is
commit `fed8eb5` (`feat: add native output panes`).

Future changes must preserve the single Rust window, session status, adjustable
read-only output/log panes, and suppression of separate Python console windows.
Preserve the working helper behavior, heartbeat logging, PID handshake, idle
reset rule, timed exit, X-to-minimize behavior, and Stop cleanup order.

This records user acceptance in normal use. It does not complete the specific
manual or broader behavior checks still listed in the verification record.

## Scope

The user approved one Rust window containing session status and two adjustable,
read-only output panes. This extends the earlier dashboard presentation work.
The Python helper and monitor remain unchanged. Interactive terminals, Bash,
ConPTY, and screenshot logging are outside this change.

Implemented in the Rust tree and reviewed in the parent session.
The [20 September verification record](observations.md#20-september-2026-native-output-panes)
records the automated checks and remaining manual checks.

## Implementation tasks

1. Retain the helper's startup messages, including those consumed by the PID
   handshake. Drain subsequent stdout and stderr into bounded display buffers.
2. Display a read-only tail of the existing heartbeat file. Identify it as a
   shared log containing records from other runs. Show read failures without
   treating them as helper failures or changing the log.
3. Replace dashboard placeholders with native text controls that support
   scrolling, selection, and copying. Keep the status and Stop control visible
   while resizing. Provide an adjustable division between the panes.
4. Suppress console windows for Python discovery and both Python children.
   Retain the same interpreter selection, arguments, working directory, PID
   handshake, process ownership, and normal shutdown order.
5. Verify the changed launch presentation separately from the display buffers
   and layout. Record actual results in the observation log.

## Contracts to preserve

- `keep-awake.py` and `monitor-helper.py` remain byte-for-byte unchanged.
- The helper receives the same optional `--seconds` argument.
- The monitor follows the helper PID with `--interval 60` and the existing log
  path, `local/stay-watch/keep-awake.monitor.log`.
- The monitor remains the writer. The view must not truncate, rotate, rewrite,
  annotate, or create the heartbeat log.
- Stop ends the monitor before the helper. X minimizes. Timed helper exit still
  ends the application. The existing idle reset rule remains unchanged.
- A heartbeat establishes process liveness only. Displaying a PID or log record
  must not claim logging health or that Windows honors every power request.
- The existing root command, `python .\launch.py`, continues to own build and
  startup checks. Rust continues to own the two Python children.

The view adds file reads and output buffering. Suppressing consoles changes
process creation flags. These are small launch/presentation changes that need
regression checks, even though the scripts and their behavior stay the same.

## Acceptance checks

| Area | Required result |
|---|---|
| Data | Startup output includes SYSTEM, DISPLAY, and the PID message. Heartbeat records appear in the second pane. |
| Memory | Display history and background reads are bounded. Slow UI updates do not block Python output. |
| Log access | Missing files and truncation are handled; reading does not alter file bytes. |
| Selection | New text does not pull a reader away from selected or older text. |
| Layout | Both panes resize; the split is adjustable; text and Stop stay inside the client area. |
| Access | Stop has a native accessible name; controls support keyboard navigation and copy. |
| Windows | Only the Rust application window is visible for the owned test session. |
| Lifecycle | Minimize leaves children alive; timed exit and Stop release all owned test processes. |
| Logging | Existing bytes remain intact, the format stays the same, and a session beyond 60 seconds produces a subsequent heartbeat. |

The explicit live harness is [verify_output_panes.py](../tools/verify_output_panes.py).
It refuses an existing stable-path app and starts bounded sessions through the
root launcher. It reads window text and process metadata; it uses no capture
resources. The test helpers make their usual power requests while running.

```powershell
python -B tools\verify_output_panes.py --run
```

Run with the required authorization for the approved stable Cargo target.
Do not change output paths or machine policy to bypass an access failure.
The harness does not establish long-term idle, lock, sleep, or power-policy
behavior. Manual DPI, high-contrast, and assistive-technology checks must be
reported separately from automated checks.

Each captured stream retains at most 48 KiB of raw display history. The monitor
pane reads the last 48 KiB of the shared file about once a second. The on-disk
log is not capped by the view. Normal appends preserve the selection and vertical
scroll position. If the displayed prefix changes while text is selected (for
example, after tail truncation), display replacement waits until the selection
is cleared so the selected text is not replaced underneath the reader.
