# Required Rust environment verification

Use this procedure after a Rust install, relocation, settings change, or native
execution failure. Open a new PowerShell terminal and run it from the repository
root. Restart terminals after a user-environment change.

These checks prove that the toolchain can build and run a small Win32 program.
They do not prove application, idle, lock, sleep, or power-request behavior.

## Expected locations

| Item | Expected value |
|---|---|
| Source | `D:\Apps\stay-up` |
| `CARGO_HOME` | `%LOCALAPPDATA%\Programs\Rust\cargo` |
| `RUSTUP_HOME` | `%LOCALAPPDATA%\Programs\Rust\rustup` |
| `CARGO_TARGET_DIR` | `%LOCALAPPDATA%\Rust\target` |
| User PATH entry | `%LOCALAPPDATA%\Programs\Rust\cargo\bin` |
| Toolchain | `stable-x86_64-pc-windows-gnu` |

Store expanded absolute paths in the environment variables. Keep build products
outside the repository on this managed system.

AppLocker evidence from 20 September 2026 allowed programs under
`%OSDRIVE%\Users\*\AppData\Local\*`. It blocked the former Rust locations
under `%USERPROFILE%\.cargo` and `%USERPROFILE%\.rustup`. Recheck the policy
after a machine or policy change. Signing status did not explain this result.

Rust documents [Cargo environment variables](https://doc.rust-lang.org/cargo/reference/environment-variables.html),
[RUSTUP_HOME](https://rust-lang.github.io/rustup/environment-variables.html),
and [Windows installation](https://github.com/rust-lang/rustup/blob/main/doc/user-guide/src/installation/windows.md).

## 1. Check paths and command resolution

```powershell
Get-ItemProperty -LiteralPath 'HKCU:\Environment' -Name CARGO_HOME,RUSTUP_HOME,CARGO_TARGET_DIR |
    Select-Object CARGO_HOME,RUSTUP_HOME,CARGO_TARGET_DIR
Get-Item Env:CARGO_HOME,Env:RUSTUP_HOME,Env:CARGO_TARGET_DIR
Get-Command rustup,rustc,cargo | Select-Object Name,Source
```

Pass when saved and process values match the table. All commands must resolve
through the new Cargo bin directory. That directory must occur once in user
PATH. The old `.cargo\bin` entry must be absent.

After an authorized replacement, inspect the old locations:

```powershell
Test-Path -LiteralPath "$env:USERPROFILE\.cargo"
Test-Path -LiteralPath "$env:USERPROFILE\.rustup"
```

Both checks returned `False` on 20 September 2026. These commands do not
authorize deletion. Inspect possible configuration or credentials before an
authorized removal.

## 2. Check tool launches

```powershell
rustup show active-toolchain
if ($LASTEXITCODE -ne 0) { throw 'Rustup check failed.' }
rustc --version
if ($LASTEXITCODE -ne 0) { throw 'Compiler launch failed.' }
cargo --version
if ($LASTEXITCODE -ne 0) { throw 'Cargo launch failed.' }
```

All commands must exit with zero. Record the selected toolchain and versions.
The 20 September 2026 results were Rustup 1.29.1, rustc 1.98.1, and Cargo
1.98.1. These versions are observations, not pins.

## 3. Check a fresh build and execution

The fixture at [tools/rust-install-check](../tools/rust-install-check/Cargo.toml)
has no external dependency. Its build script and Win32 program print separate
success markers.

```powershell
if (-not $env:CARGO_TARGET_DIR) { throw 'CARGO_TARGET_DIR is not configured.' }
$rustCheckTarget = Join-Path $env:CARGO_TARGET_DIR ('installation-check-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir $rustCheckTarget
if ($LASTEXITCODE -ne 0) { throw 'Rust build or execution check failed.' }
```

Require all of this evidence:

- Cargo compiles and links in the new output directory.
- Output contains `RUST_BUILD_SCRIPT_EXECUTION_OK`.
- Output contains `RUST_EXECUTION_PROBE_OK`, a process ID, and a console handle.
- Cargo exits with zero.
- The `Running` line uses the approved output root.

A zero console handle is not an installation failure. A nonzero handle does not
prove a visible window. This probe takes no screenshot and changes no power or
input state.

## Failure handling

Record the command, exit status, and exact failed stage. Separate installation,
resolution, compiler, linker, build-script, program, sandbox, and desktop errors.

For application-control errors, check the executable path and matching policy
event. AppLocker event 8002 records an allow result. Event 8004 records a block.
Do not request a policy exception until you check the actual rule and path. See
[Microsoft AppLocker event guidance](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker).

Record these items in [observations.md](observations.md):

- date, command, working directory, and versions;
- toolchain and output paths;
- saved and process setting state;
- exit status and success markers, or the exact error;
- tests that remain open.

Keep [feasibility status](stay-watch-feasibility.md) consistent. Capture is
withdrawn from current scope. Input, lock, sleep, power, observation-loss, and
helper checks remain separate.
