# Required Rust environment verification

Use this procedure after installing or relocating Rust, changing its user settings or build-output location, or investigating a native execution failure. Run it from the repository root in a newly opened PowerShell terminal. Restart existing terminals after changing user environment settings.

The checks establish that the development toolchain and a small native program can execute on this managed Windows machine. They do not establish the behavior of the proposed stay-watch application.

## Expected locations

Sources remain in `D:\Apps\stay-up`. The current approved setup uses:

| Item | Expected value |
|---|---|
| `CARGO_HOME` | `%LOCALAPPDATA%\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `%LOCALAPPDATA%\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `%LOCALAPPDATA%\Rust\target` |
| User PATH entry | `%LOCALAPPDATA%\Programs\Rust\cargo\bin` |
| Active toolchain | `stable-x86_64-pc-windows-gnu` |

The environment variables hold expanded absolute paths. `CARGO_TARGET_DIR` is a user-wide default for Cargo output. An explicitly selected project output directory must also be in an approved executable location. Keep build products outside the source repository on this machine.

The 20 September 2026 AppLocker logs showed Python, WinGet, and Hermes allowed by a rule named `%OSDRIVE%\Users\*\AppData\Local\*`. The former Rust installation under `%USERPROFILE%\.cargo` and `%USERPROFILE%\.rustup` was outside that location and was blocked. Check current evidence if policy or machine context changes. Signing status alone did not explain this case: Hermes and the blocked Rust launcher were both unsigned.

Rust supports these locations through [Cargo environment settings](https://doc.rust-lang.org/cargo/reference/environment-variables.html) and [RUSTUP_HOME](https://rust-lang.github.io/rustup/environment-variables.html). The GNU toolchain supports basic builds without Visual Studio; later native dependencies may need additional tools. See [Rustup's Windows guidance](https://github.com/rust-lang/rustup/blob/main/doc/user-guide/src/installation/windows.md).

## 1. Confirm paths and command resolution

Inspect only the relevant settings:

```powershell
Get-ItemProperty -LiteralPath 'HKCU:\Environment' -Name CARGO_HOME,RUSTUP_HOME,CARGO_TARGET_DIR |
    Select-Object CARGO_HOME,RUSTUP_HOME,CARGO_TARGET_DIR
Get-Item Env:CARGO_HOME,Env:RUSTUP_HOME,Env:CARGO_TARGET_DIR
Get-Command rustup,rustc,cargo | Select-Object Name,Source
```

Pass when the saved user values and current process values agree with the expected locations, and all three commands resolve through the new Cargo bin directory. Confirm that this directory appears once in user PATH and the former `.cargo\bin` entry is absent. If saved values are correct but the current process is stale, restart the terminal before diagnosing a missing or broken installation.

After an authorized replacement, also confirm removal of the old installation:

```powershell
Test-Path -LiteralPath "$env:USERPROFILE\.cargo"
Test-Path -LiteralPath "$env:USERPROFILE\.rustup"
```

Both returned `False` for the replacement performed on 20 September 2026. These are inspection commands, not instructions to delete directories. Existing Cargo folders can contain user configuration or credentials; inspect their contents structurally before any authorized removal.

## 2. Confirm compiler and package-manager launch

```powershell
rustup show active-toolchain
if ($LASTEXITCODE -ne 0) { throw 'Rustup check failed.' }
rustc --version
if ($LASTEXITCODE -ne 0) { throw 'Compiler launch failed.' }
cargo --version
if ($LASTEXITCODE -ne 0) { throw 'Cargo launch failed.' }
```

Pass when all commands exit with code zero and the selected toolchain matches the intended setup. Record the actual versions. The versions observed on 20 September 2026 were Rustup 1.29.1, rustc 1.98.1, and Cargo 1.98.1; these observations are not a permanent version pin.

## 3. Confirm a fresh build and native execution

The repository fixture is [tools/rust-install-check/Cargo.toml](../tools/rust-install-check/Cargo.toml). It has no external dependencies. Its [build script](../tools/rust-install-check/build.rs) emits a success marker, and its binary uses the [Win32 probe](../tools/rust-execution-probe.rs), which calls `GetCurrentProcessId` and `GetConsoleWindow` before exiting.

Use a fresh directory beneath the configured Cargo output root. This avoids treating cached output as evidence of a new compilation or build-script execution.

```powershell
if (-not $env:CARGO_TARGET_DIR) { throw 'CARGO_TARGET_DIR is not configured.' }
$rustCheckTarget = Join-Path $env:CARGO_TARGET_DIR ('installation-check-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir $rustCheckTarget
if ($LASTEXITCODE -ne 0) { throw 'Rust build or execution check failed.' }
```

| Confirmation | Required evidence |
|---|---|
| Fresh compilation and linking | Cargo compiles the fixture and finishes successfully in the new output directory. |
| Build-script execution | Output includes `RUST_BUILD_SCRIPT_EXECUTION_OK`. |
| Native program execution | Output includes `RUST_EXECUTION_PROBE_OK`, a process ID, and a console-handle value. |
| Command result | Cargo exits with code zero. |
| Output location | Cargo's `Running` line points to the new directory under the approved output root. |

A console handle of zero is not a failure of this installation check. A nonzero console handle is not proof of a visible capture target. The installation check makes no screenshots, power requests, or input changes.

## 4. Keep terminal discovery separate from capture

When terminal-target feasibility is in scope, run:

```powershell
python -B tools\terminal-target-probe.py
if ($LASTEXITCODE -ne 0) { throw 'Terminal enumeration failed.' }
```

Discovery passes only when enumeration succeeds and at least one candidate is visible, not minimized, has a nonzero rectangle, and is confirmed not cloaked. An unknown cloaked state is unverified. Treat every HWND and PID as temporary data; never put observed values into fixed application settings.

This metadata-only probe does not verify tab ownership, fresh observer content, a capture backend, or saved images. Those require an explicitly invoked capture test with the checks in the [stay-watch plan](stay-watch-plan.md). An empty or failed sandbox enumeration does not establish that Windows Terminal has no visible window.

## Failure handling and reporting

Record the failed command and its exit status. Distinguish installation, command resolution, compiler launch, linking, build-script execution, program execution, and desktop access. Do not summarize all of these as “Rust is not installed.”

For an application-control error, inspect the relevant executable path and the matching allow/block evidence. AppLocker event 8002 records an allowed executable and 8004 a blocked one. A working program in another directory does not prove the failed path is allowed. Do not infer that a new policy exception is necessary until the actual rule and installation layout have been checked. Follow the applicable authorization process before changing installation locations or policy. [Microsoft AppLocker event guidance](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker).

Each verification record must state:

- Date, command, working directory, and relevant tool versions.
- Toolchain and build-output locations, plus whether saved settings reached the current process.
- Exit status and observed success markers, or the exact failed stage.
- What remains untested.

Store actual results in the [observation log](observations.md) and keep the current [feasibility status](stay-watch-feasibility.md) consistent. Capture and input probes are separate from this installation procedure. Lock, sleep, power-segmentation, observation-loss, and helper comparisons remain separate checks. Prepared [acceptance vectors](stay-watch-acceptance.md) are not executed tests.
