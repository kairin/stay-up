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
The [feasibility notes](docs/stay-watch-feasibility.md) record the current
machine limits.
The utility is not implemented. Capture feasibility and runtime checks remain pending.

## Development verification

Before declaring the Rust environment ready, follow the [required verification procedure](docs/rust-environment-verification.md). It checks approved installation and build-output paths, saved user settings, command resolution, a fresh Cargo build, build-script execution, and the resulting Win32 executable. The [repository instructions](AGENTS.md) define when these checks are required.

The repeatable probe is in `tools/rust-install-check/`; it is separate from the proposed stay-watch implementation. Installation success does not pass the later screenshot, input, lock, or power checks. Record results in the [observation log](docs/observations.md).

## Contents

| Path | Purpose |
|---|---|
| `AGENTS.md` | Agent workflow for this repository. |
| `keep-awake.py` | Current lightweight helper; no third-party Python dependencies. |
| `monitor-helper.py` | Optional heartbeat logger for a running helper process. |
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
