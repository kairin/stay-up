# Repository instructions

Read [required environment verification](docs/rust-environment-verification.md) before installing, relocating, or troubleshooting Rust, and before treating the native development environment as ready. The [feasibility record](docs/stay-watch-feasibility.md) contains observed results. The [observation log](docs/observations.md) distinguishes them from pending application checks.

## Verification expectations

- Inspect the actual installation paths, user settings, current process settings, and resolved commands. A user-profile installation is not automatically in an allowed executable location.
- For this managed machine, keep Rust tools and generated executables in the documented locations under `AppData\Local`.
- After a toolchain or path change, run the repository Cargo probe in a fresh output directory. Require compiler launch, build-script execution, successful linking, and execution of the Win32 probe. Installer success or version output alone is insufficient.
- If execution fails, record the exact error and distinguish sandbox restrictions from application-control policy. Inspect relevant allow/block evidence before concluding that a new administrator exception is necessary. Observe existing authorization requirements for changes.
- Record the command, versions, output location, exit status, success markers, and limitations in the observation log. Read only the relevant environment variables; do not dump credentials or the complete environment.
- Reuse valid evidence when the environment has not changed. Documentation-only edits need link and formatting checks, not repeated interactive machine tests.

## Root launch command

Use `python .\launch.py` from this repository to build and start the Rust application.
The command resolves the repository from `launch.py`.
It uses the approved Cargo command and the stable output path under `AppData\Local`.
It starts only the Rust executable.
It passes `--seconds N` to the Rust application for a timed test.
It returns a JSON startup result with the status, PID, executable path, and window handle.
It checks the live Rust process and the owned `StayWatchStatusWindow`.
It does not take screenshots or claim helper health.
The supported checkout is `D:\Apps\stay-up`.
The stable output is `%LOCALAPPDATA%\Rust\target\stay-up`.
Sandbox write approval is separate from this command.
After an access denial, request the required terminal authorization. Do not change ACLs or choose a new output directory.

## Application scope

Preserve the existing manual helper and heartbeat-monitor behavior. The [visual-refresh plan](docs/visual-refresh-plan.md) controls current work. Keep application changes limited to approved presentation work. Screenshot logging is removed from scope, including explicit-test captures. Do not allocate capture resources. User-supplied media in documentation is separate from application logging. Any later observer must make no power requests, simulate no input, and change no power or locking settings.

A working Rust probe does not establish input-device, lock, sleep, or idle behavior. The older [observer proposal](docs/stay-watch-plan.md) is historical, and its screenshot requirements are withdrawn. The [feasibility record](docs/stay-watch-feasibility.md) retains probe results and unknowns. Do not treat withdrawn capture checks as passed or as visual-refresh blockers. Preserve the launcher's existing owned-child behavior during visual work. Any launch, console, or cleanup change needs separate regression checks. Do not mark broader observer feasibility complete from installation checks alone.
