# Repository instructions

Read [required environment verification](docs/rust-environment-verification.md) before installing, relocating, or troubleshooting Rust, and before treating the native development environment as ready. The [feasibility record](docs/stay-watch-feasibility.md) contains observed results. The [observation log](docs/observations.md) distinguishes them from pending application checks.

## Verification expectations

- Inspect the actual installation paths, user settings, current process settings, and resolved commands. A user-profile installation is not automatically in an allowed executable location.
- For this managed machine, keep Rust tools and generated executables in the documented locations under `AppData\Local`.
- After a toolchain or path change, run the repository Cargo probe in a fresh output directory. Require compiler launch, build-script execution, successful linking, and execution of the Win32 probe. Installer success or version output alone is insufficient.
- If execution fails, record the exact error and distinguish sandbox restrictions from application-control policy. Inspect relevant allow/block evidence before concluding that a new administrator exception is necessary. Observe existing authorization requirements for changes.
- Record the command, versions, output location, exit status, success markers, and limitations in the observation log. Read only the relevant environment variables; do not dump credentials or the complete environment.
- Reuse valid evidence when the environment has not changed. Documentation-only edits need link and formatting checks, not repeated interactive machine tests.

## Application scope

Preserve the existing manual helper and heartbeat-monitor behavior. The planned observer must make no power requests, simulate no input, and change no power or locking settings. Screenshots belong only to an explicitly invoked test; ordinary tracking must not allocate capture resources.

A working Rust probe does not establish capture, input-device, lock, sleep, or idle behavior. Follow the [stay-watch plan](docs/stay-watch-plan.md) for those checks. The [feasibility record](docs/stay-watch-feasibility.md) lists which probe checks passed and which remain unknown. Keep owned-child launching and cleanup after the baseline/manual-helper milestone. Do not mark the full feasibility gate complete from installation checks alone.
