# Repository instructions

Read the [Rust environment procedure](docs/rust-environment-verification.md)
before you install, move, troubleshoot, or treat the Rust environment as ready. Use the
[feasibility record](docs/stay-watch-feasibility.md) and
[observation log](docs/observations.md) to separate results from open checks.

## Environment verification

- Inspect installation paths, saved settings, process settings, and resolved commands.
- Keep Rust tools and outputs in the documented `AppData\Local` locations.
- After a toolchain or path change, run the Cargo probe in a fresh output directory.
- Require compiler launch, build-script execution, linking, and Win32 probe execution.
- Record exact failures. Separate sandbox denial from application-control policy.
- Inspect allow and block evidence before you request an administrator exception.
- Observe existing authorization requirements for all access and policy changes.
- Record commands, versions, paths, exit codes, markers, and limits.
- Read only relevant environment variables. Do not expose credentials.
- Reuse unchanged machine evidence. Documentation changes need link and format checks only.

## Root launch command

Run `python .\launch.py` from this repository. It resolves the source path,
uses approved Cargo settings, and builds under
`%LOCALAPPDATA%\Rust\target\stay-up`. The supported checkout is
`D:\Apps\stay-up`.

The launcher starts only the Rust executable. It passes `--seconds N` for a
timed test. Its JSON result gives status, process ID, executable path, and
window handle. It checks the Rust process and its owned
`StayWatchStatusWindow`. It does not take screenshots or prove helper health.

Sandbox write access needs separate authorization. After a denial, request
terminal authorization for the same command. Do not change access-control lists
or select another output directory.

## Application scope

Commit `fed8eb5` (`feat: add native output panes`) is the accepted baseline.
Preserve the [baseline contract](docs/native-output-panes.md#accepted-working-baseline).

The [visual refresh plan](docs/visual-refresh-plan.md) controls current work.
Preserve manual helper behavior, heartbeat behavior, process ownership, and
cleanup. Treat launch, console, or cleanup changes as separate work with
separate regression checks.

Screenshot logging and capture tests are withdrawn. These checks are not
passed and are not visual-refresh blockers. Do not allocate capture resources. Documentation media is separate from application logging.

A future observer must make no power request, simulate no input, or change a
power or locking setting. A working Rust probe does not prove input, idle, lock,
sleep, or helper behavior. Keep those unknowns in the historical
[observer proposal](docs/stay-watch-plan.md).
