# Research and provenance

Created 2026-09-19 in `D:\Apps\stay-up` for the personal GitHub repository
`kairin/stay-up`. The source folders were copied, not deleted or moved.

Current usage is in [the README](../README.md). Paths below that start with
`D:\Apps\keep-awake.py` or `D:\Apps\powertoys-awake-runtime` are historical.

| Original | Consolidated location |
|---|---|
| `D:\Apps\keep-awake.py` | `keep-awake.py` |
| `D:\Apps\PowerToys` working files | `research/powertoys-source/` |
| `D:\Apps\powertoys-awake-runtime` | `local/powertoys-awake-runtime/` (Git-ignored) |
| `D:\Apps\000-dotfiles\docs\operations\powertoys-awake-windows.md` | `docs/research.md` |

## PowerToys provenance

- Remote: https://github.com/microsoft/PowerToys.git
- Checkout revision: `85d904edd74e64314041365561f00e9e4b4dfd78`
- Sparse-checkout selection: `src/modules/awake` (plus checkout root files).
- The untracked `StayAwake/StayAwake.cs` experiment was included.
- `.git/` was excluded: the snapshot is ordinary tracked files, not a nested
  repository or submodule. It is not a complete buildable PowerToys checkout.
- Upstream `AGENTS.md` is retained as source material within that snapshot;
  it does not define the workflow for the root stay-up project.

## Runtime provenance

The download is Microsoft's x64 per-user PowerToys 0.101.2362.0 installer:

https://github.com/microsoft/PowerToys/releases/download/v0.101.2362.0/PowerToysUserSetup-0.101.2362.0-x64.exe

Installer SHA-256:
`D56FA7130FA68AFE553068C15A59A6B24C8DBCC9A0989A43EF0FC5A373230DE3`.

The whole runtime workspace was copied, including bundle metadata, payload,
cabinets, raw files, and the reconstructed application directory. The
inventory records relative paths, byte counts, and SHA-256 values so the
copy can be checked without putting executable blobs in Git history.

Extraction research used these steps; it did not run the installer:

1. Download the URL above and verify the published SHA-256 and Authenticode.
2. Use 7-Zip to extract the bundle's first cabinet and read its Burn manifest
   (entry `0`).
3. Locate the attached `MSCF` cabinet matching the manifest's container size
   and SHA-512. Extract the verified cabinet with 7-Zip.
4. The manifest maps entry `a2` to the PowerToys MSI. Extract `cab*.cab` from
   that MSI with 7-Zip, then extract each cabinet's files.
5. Read the MSI File, Component, and Directory tables with Python 3.12's
   `msilib` in read-only mode. Reconstruct the base-application files, Awake
   images, and Awake language resources under `app/` using those mappings.
6. Verify the Awake executable's signature. Its workspace launch on this
   computer was rejected by group policy; do not describe extraction as a
   verified portable installation.

Python 3.13 removed `msilib`; the extraction experiment used Python 3.12.
The keep-awake helper itself does not import `msilib` or require extraction.

## Copy verification

SHA-256 comparison against the original folders completed successfully:

- Source: 104 files, 1,221,253 bytes; all copies matched.
- Runtime: 3,271 files, 2,319,009,392 bytes; all copies matched.
- The copied helper acquired and released SYSTEM and DISPLAY requests in a
  two-second run, exiting successfully.
- No runtime cache files or nested Git repositories are staged for upload.
- New documentation and helper files passed Git whitespace checks. Existing
  whitespace in the unmodified upstream snapshot was retained.

A later documentation review checked the inventory structure, file count, and total size.
The inventory and local runtime each contained 3,271 files totaling 2,319,009,392 bytes.
That check did not repeat the original source-to-copy SHA-256 comparison or every individual artifact hash.

## Research scope

The copied research records both successful API calls and unsuccessful
installer/executable attempts, with Microsoft references. Paths in the
historical note describe where tests happened. For current use, run the
helper from this repository as shown in the root README.

Raw machine logs and conversation transcripts were not copied. Relevant
installer codes and diagnostic results are already recorded in the note.
No credentials are part of this record.

## Investigation: 19 September 2026

Requirement: run from the user's workspace without an
administrator password, like other allowed user applications.

### Result

A lightweight Python helper using Windows PowerCreateRequest
and PowerSetRequest successfully acquired DISPLAY and SYSTEM requests as
the current user. See [Teams-free alternative](#teams-free-alternative).
This establishes API acceptance, not a completed unattended idle test.

The official signed Awake executable was extracted to the workspace without
installing PowerToys or requesting administrator rights. Windows rejected
its launch with: **This program is blocked by group policy.**

Therefore the extracted package is not a working solution on this computer
under the current application policy. The fact that another workspace
application runs does not establish that Awake is permitted. No policy
changes, installer execution, elevation, or power-setting changes were made.

### Evidence

| Check | Result |
|---|---|
| Windows | DisplayVersion 25H2, build 26200.9168. Registry ProductName retains Windows 10 Education; that legacy label alone is not a reliable release identifier. |
| Power plan | Balanced. |
| Display idle timeout | 180 seconds on mains power and battery. |
| Sleep idle timeout | 180 seconds on mains power; 900 seconds on battery. |
| Sleep capability | S0 Low Power Idle (network connected), hibernate, fast startup; S3 unavailable. |
| Screen-saver policy | ScreenSaveActive=1, ScreenSaveTimeOut=600, ScreenSaverIsSecure=1 under HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop. A secure screen saver is configured after 10 minutes; actual activation was not observed. |
| Existing PowerToys | No matching uninstall registration, current-user Appx package, running process, or Awake executable found in inspected locations before this investigation. This is not an exhaustive all-user inventory. |
| Existing workspace source | D:\Apps\PowerToys contains source, plus a custom StayAwake.cs file. No executable was found there. Source presence is not an installed application. |
| Historical install failure | The 2026-09-02 per-user PowerToys 0.101.2362.0 MSI log reports 1625; bootstrapper reports 0x80070659. |
| PowerToys policy keys | HKLM and HKCU SOFTWARE\Policies\Microsoft\PowerToys absent. This does not rule out application-control restrictions. |
| PowerShell | 7.6.6, ConstrainedLanguage; LocalMachine execution policy RemoteSigned, other queried scopes Undefined. |
| WinGet | v1.29.290 works outside the agent sandbox. Failure inside the sandbox was not a host WinGet failure. |
| Diagnostic permissions | powercfg /requests requires additional permissions even outside the agent sandbox. Active power requests were not inspected. |

Microsoft defines MSI 1625 as installation forbidden by system policy.
This describes the historical installation attempt, separately from the
new executable-launch rejection.
[MSI error reference](https://learn.microsoft.com/en-us/windows/win32/msi/error-codes).

### Workspace extraction and launch test

The stable release checked was 0.101.2362.0. Its published assets had
installers and symbols, but no portable application ZIP.
[Microsoft release](https://github.com/microsoft/PowerToys/releases/tag/v0.101.2362.0).

Downloaded the official x64 per-user installer to:

```text
D:\Apps\powertoys-awake-runtime\PowerToysUserSetup-0.101.2362.0-x64.exe
```

Its SHA-256 matched Microsoft's published value:

```text
D56FA7130FA68AFE553068C15A59A6B24C8DBCC9A0989A43EF0FC5A373230DE3
```

Authenticode status was Valid for the installer and the extracted Awake
executable. The installer was not executed. Existing 7-Zip and Python tools
extracted its embedded cabinets. The payload cabinet's SHA-512 matched the
bundle manifest. Python's MSI database reader opened the MSI read-only to
map packaged filenames and directories; no MSI installation was performed.

The extraction copied 683 base application, Awake icon, and Awake resource
files into `D:\Apps\powertoys-awake-runtime\app`. The package includes its
.NET 10.0.11 runtime, so the host's installed .NET 8 runtime was not assumed
to satisfy Awake's dependencies. This is a manual extraction experiment,
not an official portable deployment method or a verified minimal package.

Tested this command outside the agent sandbox in the current user's session:

```powershell
Start-Process -FilePath 'D:\Apps\powertoys-awake-runtime\app\PowerToys.Awake.exe' `
    -ArgumentList '--display-on=true','--time-limit=30' `
    -WorkingDirectory 'D:\Apps\powertoys-awake-runtime\app' `
    -WindowStyle Hidden -PassThru
```

Windows refused to create the process because of group policy. The test
did not request RunAs, UAC elevation, or an administrator password. No
keep-awake behavior was activated or verified. The precise application
control rule responsible was not determined.

The download, extracted cabinets, raw package files, and application files
were later copied to `local/powertoys-awake-runtime/` in this repository.
The original workspace copy remained at `D:\Apps\powertoys-awake-runtime`.
No raw logs or personal account paths are recorded here.

### What is needed next for PowerToys Awake

To use this specific PowerToys executable without an administrator password,
the device's application policy must permit it. An application approval or
an already-allowed equivalent is needed; installing per-user or extracting
to the workspace alone does not solve the observed launch block. No
working no-admin PowerToys route was established.

If the executable is subsequently allowed, its documented command is:

```powershell
& 'D:\Apps\powertoys-awake-runtime\app\PowerToys.Awake.exe' --display-on=true --time-limit=7200
```

That requests two hours. Omit the time limit for indefinite operation;
use `--display-on=false` to allow display power-off. These modes are
documented by Microsoft, but remain unverified on this computer.
[Awake command-line documentation](https://learn.microsoft.com/en-us/windows/powertoys/awake).

Once execution is allowed, verify more than three minutes of idle time
with the screen on, observe the separate ten-minute screen-saver behavior,
and check DISPLAY/SYSTEM requests with `powercfg /requests` if permitted.
Then exit Awake and confirm normal power behavior returns.

### Screen-saver and lock limitations

Preventing display power-off is different from preventing a secure screen
saver. Windows documents that SetThreadExecutionState does not stop a
screen saver. The ten-minute policy remains relevant even if Awake becomes
permitted. [Windows API reference](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).

Microsoft documents a lock-screen limitation for Awake. Do not promise
unattended locked operation on this Modern Standby machine. Keeping work
running while locked needs a separately permitted power configuration or
a supported application tested for that scenario. No lock-policy change
is part of this investigation.
[Awake lock-screen behavior](https://learn.microsoft.com/en-us/windows/powertoys/awake).

This record does not change the repository's WSL-based setup support boundary.

### Teams-free alternative

The user reports that an active Teams meeting prevents sleep, screen-off,
and session locking on this computer. We have not inspected Teams' actual
power requests, so attributing that behavior to a particular API remains
an inference. There is no demonstrated persistent Teams switch to retain
after the meeting process exits. A small separate process can own its own
Windows power requests instead.

The investigation created the local standard-library-only helper at
`D:\Apps\keep-awake.py`. The repository copy is `keep-awake.py`.
It uses the already-installed Python and requests PowerRequestSystemRequired
and PowerRequestDisplayRequired, then sleeps between timer checks. It does
not simulate input, change registry/power-plan settings, install software,
or request administrator rights.

Run from a normal PowerShell terminal in this repository:

```powershell
# Until Ctrl+C or closing this process:
python .\keep-awake.py

# Alternatively, expire after two hours:
python .\keep-awake.py --seconds 7200
```

The helper prints an error and exits nonzero if Windows rejects either
request. It clears successfully acquired requests and closes the handle on
normal expiry, Ctrl+C, or a subsequent failure. Exiting the process also
releases the process-owned handle; it does not leave a permanent setting.

Validation on 2026-09-19:

- A three-second run acquired both requests, released them, and exited 0.
- A second timed run acquired both requests. During the run its working set
  was 18,853,888 bytes (about 18 MiB), and total process CPU time was 0.0625
  seconds. These are point-in-time measurements, not a benchmark.
- A negative duration was rejected before any request was made.
- No administrator password or elevated process was used.
- A Teams-closed idle test longer than the three-minute screen timeout and
  ten-minute secure screen-saver timeout remains to be performed by the user.

The relevant distinction from the earlier Awake discussion is the API:
Microsoft documents that PowerRequestDisplayRequired prevents idle display
power-off, automatic screen-saver activation, and automatic session locking.
It needs an accompanying system request to prevent sleep. This differs from
SetThreadExecutionState's documented screen-saver limitation. Do not extend
the earlier limitation to every Windows power-request API.
[POWER_REQUEST_TYPE documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_power_request_type).

This is still subject to the host's effective power policies. On Modern
Standby battery power, Windows limits system/execution requests to five
minutes beyond the system sleep timeout. Manual sleep or closing the lid
also terminates requests. Start validation on mains power; do not infer
battery or manually locked behavior from API acceptance.
[PowerSetRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest),
[PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest).

## Stay-watch design follow-up

A later documentation review retained the distinction between successful API calls and observed idle behavior.
It did not repeat the historical experiments in this note.

The [stay-watch plan](stay-watch-plan.md) reports AC and battery results separately.
Power-source changes close qualifying intervals, and unknown source periods end confirmed condition coverage.
A comparison needs continuous intervals under matching known conditions.
This follows the different power-request limits described above.

The plan also defines observation-loss handling and requires verified observer content for screenshot evidence.
The observer implementation, capture feasibility, and runtime checks remain pending.
