# Observation log

The [Rust procedure](rust-environment-verification.md) defines commands and
pass criteria. These records state observed results. They do not pass later or
broader application checks.


Historical entries retain the paths that they used. Current scripts and logs use scripts/ and logs/ as described in the [repository layout](repository-layout.md).

Commands ran from `D:\Apps\stay-up`. Profile paths use environment variables
for privacy. Other recorded commands and results retain their original meaning.

## 19 September 2026: observation before planned reboot

The helper had run for about two hours. The latest heartbeat showed that the
helper was running. The record contained a local timestamp and a process ID.
Those values are not retained here.

This proves process life at that time. It does not prove uninterrupted idle
time, display state, login state, power source, or prevention of sleep. Reboot
and controlled idle checks remained pending.

## 19 September 2026: documentation review

The review checked scripts, inventory, and source references. It did not run
reboot, sleep, or idle tests. It retained three historical observer rules:
split results at power-source changes, record observation loss, and do not use
a stable window handle as proof of current content.

## 20 September 2026: corrected Rust installation and repository check

Rustup 1.29.1 was installed under `%LOCALAPPDATA%\Programs\Rust`. The former
`%USERPROFILE%\.cargo` and `%USERPROFILE%\.rustup` locations were removed
after structural inspection.

Observed versions were rustc `1.98.1 (48a229cea 2026-09-01)` and Cargo
`1.98.1 (797e8a9bc 2026-08-05)`. The toolchain was
`stable-x86_64-pc-windows-gnu`.

```powershell
$check = "$env:LOCALAPPDATA\Rust\target\installation-check-20260920-091022-874"
cargo run --offline --locked --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir $check
```

The fresh build returned zero after 11.50 seconds. It emitted
`RUST_BUILD_SCRIPT_EXECUTION_OK` and `RUST_EXECUTION_PROBE_OK`. This check
did not test input, idle, lock, suspend, or power behavior.

## 20 September 2026: acceptance vectors

The [acceptance vectors](stay-watch-acceptance.md) are unexecuted definitions.
An earlier Rust `NOT FOUND` result was superseded by the corrected install.

## 20 September 2026: native feasibility probes

Python `3.11.16`, rustc 1.98.1, and Cargo 1.98.1 ran from
`D:\Apps\stay-up`. The probes made no power request and simulated no input.

```powershell
$out = "$env:LOCALAPPDATA\Rust\target\feasibility-20260920-1336"
rustc --out-dir $out D:\Apps\stay-up\tools\rust-state-probe.rs
& "$out\rust-state-probe.exe"
```

The compiler exited with zero. The executable emitted `RUST_STATE_PROBE_OK` with
`power_ok=1 ac=1 batt%=100 raw_ok=1 mouse=3 keyboard=6 hid=17`.

```powershell
python -B tools\windows-state-probe.py --listen-seconds 25 --output .\local\stay-watch\feasibility-20260920-1345\windows-state.json
```

The Python state probe returned zero after a structure-size repair. Raw Input
registration succeeded. Device lists included keyboard, mouse, and touchpad
collections. No live event arrived during 25 seconds. The power source
was AC. S0 Low Power Idle was available. No lock, return, suspend, or
power-source change occurred.

Historical capture probes returned zero and saved marker images. Windows
Graphics Capture and observer-tab return were not tested. Capture is outside
the current scope.

## 20 September 2026: silent re-check of recorded probes

```powershell
python -B -m unittest tools.test_feasibility_probes -v
```

At 14:21 local time, the command returned zero and printed
`Ran 14 tests in 5.950s` and `OK`. It did not open a capture window.

## Visual-refresh planning after issues #6 and #7

The user reported that the project worked and requested visual improvements.
This report was not a controlled idle or power test. The plan removed
screenshot logging and explicit capture from active scope.

## 20 September 2026: Cargo build access from an agent

The documented Rust settings and output locations were active. The root launcher did not exist during this check. The first
sandbox build returned `101` at `debug\.cargo-build-lock`:

```text
error: failed to open: <target>\debug\.cargo-build-lock

Caused by:
  Access is denied. (os error 5)
```

A new-directory attempt also failed with access denied. AppLocker event 8002
recorded allowed Cargo execution. Thus the failure was sandbox file access,
not an application-control block.

Ordinary terminal builds in the approved output location compiled and linked. The
installation probe emitted both success markers. A stable output directory
does not grant sandbox write access. Do not change access-control lists or use
a new directory as a permission fix.

```powershell
cargo run --offline --locked --verbose --manifest-path .\tools\rust-install-check\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\installation-check-launch-9ffed62d45"
cargo build --offline --locked --verbose --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\stay-up"
cargo rustc --offline --locked --verbose --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:CARGO_TARGET_DIR\stay-up" --bin stay-watch -- -C debuginfo=1
```

These commands exited with zero. The stable build passed twice before the
recompile. The same stable build inside the sandbox returned 101. A new
directory failed with exit 1 before Cargo ran.

## 20 September 2026: Root launch command and owned-process checks

Working directory: `D:\Apps\stay-up`.

```powershell
python -B -m unittest tools.test_launch -v
cargo test --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
python -B .\launch.py --seconds 12
python -B .\launch.py
```

All 24 launcher tests and 12 Rust tests passed. Concurrent commands returned
`started` and `already_running`. Invalid options returned `2`. Timed exit
and held handles confirmed process cleanup.

The sandbox denial returned `1` with `status=failed`. Cargo returned `101`
with `Access is denied. (os error 5)`. No application started in that check.

The authorized launch returned zero and `started` in about 2.859 seconds. The
executable was under `%LOCALAPPDATA%\Rust\target\stay-up`. The Rust process
owned the visible window and helper processes.

These checks prove startup, concurrent-command handling, timed exit, Stop, and
owned-process cleanup. They do not prove idle, sleep, lock, input, or power
behavior.

## 20 September 2026: Native output panes

The environment used rustc 1.98.1, Cargo 1.98.1, the stable GNU toolchain, and
Python 3.12.9.

```powershell
cargo test --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
cargo build --offline --locked --manifest-path .\stay-watch\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
```

Both commands returned zero. Seventeen Rust tests passed. Rustfmt was
unavailable. `git diff --check` passed.

The launcher test needed explicit discovery because direct module import failed:

```powershell
python -B -c "import sys, unittest; sys.path.insert(0, r'D:\Apps\stay-up'); suite=unittest.defaultTestLoader.discover(r'D:\Apps\stay-up\tools', pattern='test_launch.py'); result=unittest.TextTestRunner(verbosity=0).run(suite); sys.exit(not result.wasSuccessful())"
python -B tools\verify_output_panes.py --run
```

Explicit discovery passed all 24 launcher tests. The live harness exited with
zero and left the application closed.

The 65-second live session showed both read-only panes and one owned window.
The next heartbeat appeared while selection `0..6` remained unchanged. Three
records were appended, and all held processes exited. A second session passed
minimize, resize, slider, and Stop checks.

Both sessions preserved all preexisting heartbeat bytes. New records kept the
helper process ID and `interval=60s`. No capture resource was used.

Manual DPI, high-contrast, screen-reader, and physical input checks remain
open. The resize check verified control bounds, not every painted label.
Arbitrary log truncation while selected and horizontal-scroll retention were
not exercised live.

## 20 September 2026: User acceptance of the working baseline

The user reported that commit `fed8eb5` (`feat: add native output panes`)
worked and accepted it as the baseline. It includes one Rust window, a status
dashboard, adjustable read-only panes, and suppressed Python console windows.

Future changes must preserve the
[accepted baseline contract](native-output-panes.md#accepted-working-baseline).
This acceptance is not a controlled input, idle, lock, sleep, or power test.

## 22 September 2026: repository layout cleanup

The cleanup moved the Rust package to Cargo.toml, Cargo.lock, and src/. It
moved application and verification scripts to scripts/. It moved active and
archived logs to logs/. The package name, library name, binary name, helper
arguments, process ownership, and approved AppData target stayed unchanged.

```powershell
cargo test --offline --locked --manifest-path .\Cargo.toml --target-dir "$env:LOCALAPPDATA\Rust\target\stay-up"
```

The root Cargo test returned zero. It ran 12 library tests and 6 binary tests.
The moved launcher test returned zero after 24 tests.

```powershell
$rustCheckTarget = Join-Path $env:CARGO_TARGET_DIR ('installation-check-layout-20260922-052739-965')
cargo run --offline --locked --manifest-path .\scripts\rust-install-check\Cargo.toml --target-dir $rustCheckTarget
```

The fresh fixture returned zero. It emitted
RUST_BUILD_SCRIPT_EXECUTION_OK and RUST_EXECUTION_PROBE_OK.

A launch from D:\Apps used D:\Apps\stay-up\launch.py --seconds 3. It
returned started and used the stable executable under the approved AppData
target. The session ended and left no root log or old active-log path.

An initial live output-pane run reached the canonical log but failed its
selection refresh check. The log exceeded the 48 KiB display tail. The unchanged
view deferred replacement while selection held because the tail prefix changed.
The old harness expected an immediate refresh while selection held. It reported
WinError 0 or no refresh before the deadline. All owned processes ended. The
corrected harness waited for the heartbeat on disk, preserved the selected text,
and passed the timed and Stop sessions. It did not use capture resources.

The feasibility test for terminal eligibility returned no eligible candidate. This is an environment limit. It did not open a terminal or use capture resources.

The changed prose passed the STE lint in one pass. Each file scored below the
2.5 per 100 words flavored target.
