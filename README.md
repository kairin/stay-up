# stay-up

`stay-up` is a small Windows keep-awake helper. It asks Windows to keep the
system and display awake while the helper runs. It needs no installer,
administrator access or third-party Python packages. The dashboard also needs
Python and the documented Rust toolchain.

![Compact stay-up dashboard after more than three minutes](docs/assets/stay-up-dashboard-banner.png)

## Run

Run the Rust application from PowerShell in `D:\Apps\stay-up`:

```powershell
python .\launch.py
```

For a timed test, add `--seconds N`:

```powershell
python .\launch.py --seconds 3
```

The launcher checks the documented Rust paths and active toolchain. It builds to `%LOCALAPPDATA%\Rust\target\stay-up`. It starts only
the Rust executable. Its JSON result gives the status, process ID, executable
path, and window handle.

The application starts `keep-awake.py` and `monitor-helper.py`. Its window
shows their process IDs, output, the shared heartbeat log, and input idle time.
Use the Split slider to size the panes. Use Stop to end all three processes.
The X button minimizes the window.

If a stable-path instance already runs, the launcher reports it and does not
apply new arguments. Use Stop before you start a new timed test. The launcher
checks only the Rust process and its owned `StayWatchStatusWindow`.

An agent needs permission to write to the stable output path. If the sandbox
denies access, authorize the same launch command. Do not change access-control
lists or select a different output directory.

Run the helper by itself when you do not need the dashboard:

```powershell
python .\keep-awake.py
python .\keep-awake.py --seconds 7200
```

Press Ctrl+C to stop the helper and release its power requests.

## Behavior and limits

- The helper requests `SYSTEM` and `DISPLAY` availability.
- It does not change the registry, power plan, lock settings, or startup settings.
- It does not simulate keyboard, mouse, or touch input.
- Input in the current session resets the idle timer.
- The monitor records process liveness about once each minute.
- The heartbeat does not prove the state of each Windows power request.
- The heartbeat does not record lock, display, sleep, idle, image, or video data.
- A final `STOPPED` record is not guaranteed after the Rust Stop action.

Windows accepted both power requests during the recorded tests. A short helper
run used about 18 MiB of memory. Device policy can still limit the result. The
pending idle, sleep, and lock checks are in the
[observation log](docs/observations.md).

The visual refresh preserves the accepted native output panes from commit
`fed8eb5`. Screenshot logging and capture tests are outside the current scope.
See the [visual plan](docs/visual-refresh-plan.md) and
[baseline contract](docs/native-output-panes.md#accepted-working-baseline).

## Privacy

The repository contains no user desktop captures, sign-in images, or personal
media. The dashboard preview above is a repository asset created for this
project. Historical issue attachments are not linked from the public
documentation.

### Runtime data and portability

The application does not read names, emails, credentials, account files, or
network data. It uses Windows power APIs, process IDs, window handles, idle
ticks, timestamps, and local log files.

The launcher requires the checkout at `D:\Apps\stay-up`. It also requires
`%LOCALAPPDATA%` and the documented Rust environment variables. These values
are machine configuration, not personal identity data.

The launcher reports an absolute executable path in its JSON result. On
Windows, that path can contain the account name from the profile path. The
path is diagnostic output and is not an input to the application.

The optional probes in `tools/` can inspect device names or window content.
They are not part of the application launch path.

## Development

Read the [Rust environment procedure](docs/rust-environment-verification.md)
before you install, move, or troubleshoot Rust. Installation and version output
do not prove that the environment can build and run this project.

The repeatable probe is in `tools/rust-install-check/`. Record new machine
results in [docs/observations.md](docs/observations.md). Documentation-only
changes do not require a new machine test.

| Document | Purpose |
|---|---|
| [Visual refresh plan](docs/visual-refresh-plan.md) | Current presentation scope and limits |
| [Native output panes](docs/native-output-panes.md) | Accepted working baseline |
| [Observation log](docs/observations.md) | Dated machine and application results |
| [Feasibility record](docs/stay-watch-feasibility.md) | Historical probes and remaining unknowns |
| [Observer proposal](docs/stay-watch-plan.md) | Historical observer design |
| [Acceptance vectors](docs/stay-watch-acceptance.md) | Unexecuted historical checks |
| [Research record](docs/research.md) | Source provenance and earlier investigation |

The PowerToys source snapshot keeps its
[MIT license](research/powertoys-source/LICENSE) and
[third-party notices](research/powertoys-source/NOTICE.md). This repository is
independent of Microsoft. It is not an official PowerToys distribution.
