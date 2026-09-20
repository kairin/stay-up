# stay-up

A small Windows keep-awake helper and the research that led to it.
Runs with the installed Python standard library, without an installer or
administrator password. Holds Windows SYSTEM and DISPLAY power requests
while its process runs.

## Run

From PowerShell in this repository:

```powershell
python .\keep-awake.py
```

Press Ctrl+C to release the requests and stop. For a two-hour limit:

```powershell
python .\keep-awake.py --seconds 7200
```

To start both helpers and an idle timer from Rust:

```powershell
cargo run --offline --manifest-path .\stay-watch\Cargo.toml
```

A small window titled `stay-watch` shows the PIDs and idle time.
Keyboard, mouse, or trackpad input in this session resets idle to `00:00:00`.
The X button minimizes. Use Stop to end the launcher and the two Python processes.
For a three-second check:

```powershell
cargo run --offline --manifest-path .\stay-watch\Cargo.toml -- --seconds 3
```

To record a one-minute process heartbeat, start `monitor-helper.py` with the
keep-awake process ID:

```powershell
python .\monitor-helper.py TEST-PID --interval 60 --log .\keep-awake.monitor.log
```

The monitor follows the original process handle, records `OK` once per
interval, records `STOPPED` when the helper exits, and then exits itself.
It confirms that the helper process remains alive; it does not independently
query Windows for the state of each power request.

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

The proposed [stay-watch plan](docs/stay-watch-plan.md) separates AC and battery results.
It defines observation-loss handling.
It requires verified observer content for screenshot evidence.
Unexecuted fixtures are in [stay-watch-acceptance.md](docs/stay-watch-acceptance.md).
The first stay-watch launcher is in `stay-watch/`.
The later observer for capture, lock, and sleep is not implemented.
Native capture and state probes ran on 20 September 2026.
The [feasibility notes](docs/stay-watch-feasibility.md) record passed checks and remaining open checks.

## Kanban board

The project uses the local Hermes Kanban board `stay-up`.
Its display name is `stay-up implementation`.
The code workspace is `D:\Apps\stay-up`.

On this Windows machine, Hermes stores the board database here:

```text
C:\Users\test-user\AppData\Local\hermes\kanban\boards\stay-up\kanban.db
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

The [plan](docs/stay-watch-plan.md) defines scope. The board records current task status.
The [feasibility record](docs/stay-watch-feasibility.md) lists completed probe checks and remaining open checks.
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
| `docs/stay-watch-plan.md` | Design rules for the proposed Rust observer. |
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
