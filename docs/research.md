# Research and provenance

This record describes the research that led to the helper in
`D:\Apps\stay-up`. Source folders were copied. They were not moved or
deleted.

Current use is in the [README](../README.md). The ignored runtime cache is not
part of Git history.

## PowerToys provenance

- Source: https://github.com/microsoft/PowerToys.git
- Checkout revision: `85d904edd74e64314041365561f00e9e4b4dfd78`
- Sparse checkout: `src/modules/awake` and checkout root files.
- The snapshot includes the untracked `StayAwake/StayAwake.cs` experiment.
- `.git/` was excluded.
- The snapshot is not a submodule or a complete PowerToys checkout.
- Upstream `AGENTS.md` is source material only.

The tested runtime was the Microsoft x64 per-user PowerToys 0.101.2362.0
installer:

https://github.com/microsoft/PowerToys/releases/download/v0.101.2362.0/PowerToysUserSetup-0.101.2362.0-x64.exe

Installer SHA-256:
`D56FA7130FA68AFE553068C15A59A6B24C8DBCC9A0989A43EF0FC5A373230DE3`.

The release had no portable application ZIP:
[Microsoft release](https://github.com/microsoft/PowerToys/releases/tag/v0.101.2362.0).

The installer was not run. Existing tools read its embedded cabinets. Python
3.12 read the MSI database in read-only mode. Python 3.13 removed `msilib`.
The extracted files remain in an ignored local research directory.

The installer and extracted Awake executable had valid Authenticode signatures.
Windows refused to launch Awake with: **This program is blocked by group
policy.** No elevation, policy change, or power-setting change occurred. The
exact application-control rule was not identified.

Microsoft defines MSI error 1625 as installation forbidden by system policy:
[MSI error reference](https://learn.microsoft.com/en-us/windows/win32/msi/error-codes).

## Copy verification

The source copy contained 104 files and 1,221,253 bytes. The runtime copy
contained 3,271 files and 2,319,009,392 bytes. The original SHA-256 comparison
found no differences.

The [runtime inventory](runtime-inventory.csv) records relative paths, sizes,
and hashes. A later documentation check confirmed its file count and total
size. That check did not repeat every hash comparison.

The copied helper completed a two-second run. It acquired and released SYSTEM
and DISPLAY requests. No runtime cache file or nested repository is staged for
Git.

## Observed Windows limits

The test system reported these general limits:

- A balanced power plan.
- Display and sleep timeouts were controlled by local policy.
- S0 Low Power Idle, hibernate, and fast startup were available.
- S3 sleep was not available.
- A secure screen saver was configured, but activation was not observed.
- The PowerToys search was not an all-user inventory.
- The test did not have permission to use `powercfg /requests`.

These observations do not prove long-term idle, lock, sleep, or battery behavior.

## Native helper result

The helper uses Windows `PowerCreateRequest` and `PowerSetRequest`. A timed
run acquired and released DISPLAY and SYSTEM requests without elevation. A
second run used about 18 MiB of memory. A negative duration was rejected before
the helper made a request.

The helper does not simulate input, change system settings, install software,
or need administrator access.

```powershell
python .\scripts\keep-awake.py
python .\scripts\keep-awake.py --seconds 7200
```

The helper exits nonzero if Windows rejects a request. It clears acquired
requests and closes its handle on expiry, Ctrl+C, or a later failure. It creates
no permanent setting.

Microsoft documents an API distinction. `SetThreadExecutionState` does not
stop a screen saver:
[Windows API reference](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).

Microsoft states that `PowerRequestDisplayRequired` prevents display
power-off, automatic screen-saver activation, and automatic session locking. A
system request is also necessary to prevent sleep:
[POWER_REQUEST_TYPE](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ne-wdm-_power_request_type).

API acceptance does not prove that each device policy permits the behavior.
On Modern Standby battery power, system and execution requests end five minutes
after the system sleep timeout. Manual sleep and lid closure also end requests.
Start validation on mains power.

[PowerSetRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest),
[PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest).

## PowerToys conclusion

The extracted PowerToys executable did not run under the observed application
policy. Per-user installation or file extraction did not remove that block.

If policy later permits execution, use the documented command and test display,
screen-saver, lock, sleep, and battery behavior separately:

```powershell
PowerToys.Awake.exe --display-on=true --time-limit=7200
```

See the [Awake command documentation](https://learn.microsoft.com/en-us/windows/powertoys/awake).

## Stay-watch follow-up

The [historical plan](stay-watch-plan.md) and
[feasibility record](stay-watch-feasibility.md) retain probe results and open
checks. The [visual plan](visual-refresh-plan.md) controls current work and
excludes screenshot logging. The later lock and sleep observer is not
implemented.
