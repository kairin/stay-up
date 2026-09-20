# stay-up

A small Windows keep-awake helper and the research that led to it.
Runs with the installed Python standard library, without an installer or
administrator password. Holds Windows SYSTEM and DISPLAY power requests
while its process runs.

## Visual refresh

The application works for the user. The current task is a visual refresh, not a replacement of the working helper system.
The [visual plan and adversarial review](docs/visual-refresh-plan.md) recommends a compact Rust status card.
Keep both Python processes. Two visible terminals are not required by the application logic.
Console suppression and optional window placement need separate checks before implementation.
Screenshot logging is removed from the active plan. Application logging remains record-only.
No application behavior changed during this planning task.

## User-submitted images and videos

From [issue #6](https://github.com/kairin/stay-up/issues/6): the current Rust window and two mostly blank terminal windows.
This is the visual baseline, not the proposed design.

![Current stay-watch window with idle timer and two terminal windows](https://github.com/user-attachments/assets/48a572b0-e9d2-4589-bc20-7dafa59edd47)

<details>
<summary>More application photos from issue #6</summary>

Timer reading `00:03:43`:

![Current Rust status window showing idle 00:03:43](https://github.com/user-attachments/assets/2d9cc158-3ecc-4c20-b65f-293c49ce1791)

Timer reading `00:10:38`:

![Current Rust status window showing idle 00:10:38 beside terminal windows](https://github.com/user-attachments/assets/699f84fc-6d48-4b42-a56e-fbd2f6d210e0)

</details>

<details>
<summary>Sign-in context from issue #6, not proof of helper behavior</summary>

The issue also contains this sign-in photograph.
Its timing and relationship to the helper are not established.

![User-submitted photograph of a Windows sign-in screen](https://github.com/user-attachments/assets/9dd17192-d6f7-4555-9843-dc5430a82719)

</details>

Videos from **both issues**, linked to the original attachments:

- Issue #6: [video 1, about 20 seconds](https://github.com/user-attachments/assets/026dbf2b-b647-48ac-8ce2-76328c979dd1).
- Issue #6: [video 2, about 8 seconds](https://github.com/user-attachments/assets/f9bf4b8c-7cc1-4d44-a729-5eaa1bce87b7).
- Issue #7: [video 1, about 9 seconds](https://github.com/user-attachments/assets/cba1ad29-38b9-4b74-ab3a-e5758a88e1d9).
- Issue #7: [video 2, about 8 seconds](https://github.com/user-attachments/assets/1630e4a0-b3f7-4a00-ab97-dea76c8163ca).

These are user-submitted observations, not controlled test results.
Attachments can require GitHub access. Inline video playback depends on the viewer.
See the [media record](docs/issue-media.md) for inspection limits, source details, and the incomplete upload in issue #6.

## Run

From PowerShell in this repository, build and start the Rust application with:

```powershell
python .\launch.py
```

The command builds with the approved Cargo setup and uses the stable output path.
It starts only the Rust executable and returns a JSON startup result.
The result includes the status, process ID, executable path, and window handle.
The launcher checks the Rust process and its `StayWatchStatusWindow` only.

For a three-second test, pass the existing option through the launcher:

```powershell
python .\launch.py --seconds 3
```

The launcher reports an existing stable-path instance. It does not start a second session.
The requested arguments do not change an existing session. Use Stop before a new timed test.

The supported source location is `D:\Apps\stay-up`.
The stable build output is `%LOCALAPPDATA%\Rust\target\stay-up`.
The launcher checks the documented Rust paths and active toolchain before the build.

An agent still needs permission to write to the stable build output.
If the sandbox denies access, request the required terminal authorization and repeat the same command.
The launcher does not disable the sandbox, change ACLs, or select a new timestamped directory.
See the [build-access evidence](docs/observations.md#20-september-2026-cargo-build-access-from-an-agent).

To run the helper alone, use:

```powershell
python .\keep-awake.py
```

Press Ctrl+C to release the requests and stop. For a two-hour limit:

```powershell
python .\keep-awake.py --seconds 7200
```

The root command starts Rust. Rust starts both helpers and an idle timer.
A small window titled `stay-watch` shows the PIDs and idle time.
Keyboard, mouse, or trackpad input in this session resets idle to `00:00:00`.
The X button minimizes. Use Stop to end the launcher and the two Python processes.

To record a one-minute process heartbeat, start `monitor-helper.py` with the
keep-awake process ID:

```powershell
python .\monitor-helper.py 31908 --interval 60 --log .\keep-awake.monitor.log
```

The monitor follows the original process handle, records `OK` once per
interval, records `STOPPED` when the helper exits, and then exits itself.
It confirms that the helper process remains alive; it does not independently
query Windows for the state of each power request.

The Rust launcher selects `local/stay-watch/keep-awake.monitor.log`.
The monitor appends timestamped UTF-8 records across runs, about once every 60 seconds.
It records process liveness, not idle time, lock state, or screenshots.
The Rust Stop path kills the monitor before the helper, so a final `STOPPED` record is not guaranteed.
See [logging behavior and limits](docs/visual-refresh-plan.md#4-what-does-logging-do-now).

No Teams meeting is required. No registry settings, power plans, input
simulation, or persistent startup entries are involved.

## Validation and limits

On the inspected Windows computer, both requests were accepted without
elevation and released on timed exit. A short run used about 18 MiB RAM.
On 19 September 2026, the user reported no recalled need to log in again
during a session in which the helper had run for about 1 hour 57 minutes.
The observation and planned reboot review are recorded in the
[observation log](docs/observations.md).
An idle test with Teams closed beyond the ten-minute screen-saver timeout
is still pending. API success is not proof that every device policy permits
the requested behavior. Modern Standby battery operation and manual sleep
have additional limits described in the research notes.

The extracted official PowerToys Awake executable was blocked by this
computer's application policy. It is retained as research, not presented
as a working runtime for this machine.

The first stay-watch launcher is in `stay-watch/`.
The [visual-refresh plan](docs/visual-refresh-plan.md) controls current work and excludes screenshot logging.
The older [observer proposal](docs/stay-watch-plan.md) and [acceptance vectors](docs/stay-watch-acceptance.md) remain historical design references.
Their screenshot requirements are withdrawn, not completed.
The later lock and sleep observer is not implemented.
Native capture and state probes ran on 20 September 2026.
The [feasibility notes](docs/stay-watch-feasibility.md) retain those historical results and their limits.

## Kanban board

The project uses the local Hermes Kanban board `stay-up`.
Its display name is `stay-up implementation`.
The code workspace is `D:\Apps\stay-up`.

On this Windows machine, Hermes stores the board database here:

```text
C:\Users\W106036\AppData\Local\hermes\kanban\boards\stay-up\kanban.db
```

The board is outside this Git repository. A Git clone, pull, or push does not transfer its tasks.
This is a local Hermes board, not a GitHub Projects board.
Use the Hermes CLI, Kanban tools, or user interface. Do not edit the SQLite database directly.

List boards and read the current task states:

```powershell
hermes kanban boards list
hermes kanban --board stay-up list --json
```

Inspect the remaining feasibility work:

```powershell
hermes kanban --board stay-up show t_cc724421
```

Always specify `--board stay-up` in task commands. The selected default board can change between sessions.
In Hermes Desktop or the dashboard, open Kanban and select `stay-up implementation` (`stay-up`).

The [visual-refresh plan](docs/visual-refresh-plan.md) defines the current scope.
The board records task status and was not changed during this planning task.
Older screenshot tasks do not override the new scope.
The [feasibility record](docs/stay-watch-feasibility.md) retains completed probe checks and remaining unknowns.
Keep changing task counts on the board, not in this README.

## Development verification

Before declaring the Rust environment ready, follow the [required verification procedure](docs/rust-environment-verification.md). It checks approved installation and build-output paths, saved user settings, command resolution, a fresh Cargo build, build-script execution, and the resulting Win32 executable. The [repository instructions](AGENTS.md) define when these checks are required.

The repeatable probe is in `tools/rust-install-check/`.
It is separate from the proposed stay-watch implementation.
Installation success does not pass lock, sleep, live input-event, or helper checks.
Capture-probe results are in the [feasibility record](docs/stay-watch-feasibility.md).
Record results in the [observation log](docs/observations.md).

To re-check recorded probe evidence without a new capture window:

```powershell
python -B -m unittest tools.test_feasibility_probes -v
```

Pass when the command prints `OK` and exit status is zero.

## Contents

| Path | Purpose |
|---|---|
| `AGENTS.md` | Agent workflow for this repository. |
| `keep-awake.py` | Current lightweight helper; no third-party Python dependencies. |
| `monitor-helper.py` | Optional heartbeat logger for a running helper process. |
| `stay-watch/` | First Rust launcher: starts both helpers and shows idle time. |
| `tools/task-ranker/` | [Advisory TypeSafe scores for local Kanban tasks](tools/task-ranker/README.md). |
| `tools/terminal-target-probe.py` | Read-only Windows Terminal window enumeration. |
| `tools/windows-state-probe.py` | Read-only input, session, display, and power observations. |
| `tools/capture-feasibility-probe.py` | Explicit Windows Terminal capture test. |
| `tools/rust-state-probe.rs` | Read-only Rust Win32 state probe. |
| `tools/test_feasibility_probes.py` | Agent-runnable checks of recorded probe evidence. |
| `docs/visual-refresh-plan.md` | Current visual scope, layout proposal, and adversarial review. |
| `docs/issue-media.md` | Image and video sources from issues #6 and #7, with evidence limits. |
| `docs/stay-watch-plan.md` | Historical Rust observer proposal. Screenshot requirements are withdrawn. |
| `docs/stay-watch-acceptance.md` | Unexecuted stay-watch acceptance vectors. |
| `docs/stay-watch-feasibility.md` | Current feasibility results and implementation limits. |
| `docs/rust-environment-verification.md` | Required Rust installation and probe procedure. |
| `docs/observations.md` | Dated helper, install, and review observations. |
| `docs/research.md` | Provenance, copy verification, and historical investigation. |
| `docs/runtime-inventory.csv` | SHA-256 and sizes of every locally copied runtime artifact. |
| `research/powertoys-source/` | Snapshot of the existing sparse PowerToys checkout, including upstream license and notice files. |
| `research/powertoys-source/StayAwake/StayAwake.cs` | Earlier custom C# experiment using SetThreadExecutionState; not the Python helper. |
| `local/powertoys-awake-runtime/` | Complete local copy of downloaded/extracted binaries, ignored by Git. |

This repository owns the consolidated copies. Original workspace folders
remain intact. PowerToys Git history was not imported; provenance is pinned
in `docs/research.md`. This is a personal project, not a Microsoft fork
or an official portable PowerToys distribution.

The runtime cache contains 3,271 files totaling 2.32 GB of vendor binaries, and
contains files above GitHub's normal Git file-size limit. A Git clone gets
the helper, source snapshot, research, and artifact inventory. It does not
download the local binary cache. The Python helper does not need that cache.

Upstream PowerToys files retain their
[MIT license](research/powertoys-source/LICENSE) and
[third-party notices](research/powertoys-source/NOTICE.md).
