# Consolidation record

Created 2026-09-19 in `D:\Apps\stay-up` for the personal GitHub repository
`project-owner/stay-up`. The source folders were copied, not deleted or moved.

| Original | Consolidated location |
|---|---|
| `D:\Apps\keep-awake.py` | `keep-awake.py` |
| `D:\Apps\PowerToys` working files | `research/powertoys-source/` |
| `D:\Apps\powertoys-awake-runtime` | `local/powertoys-awake-runtime/` (Git-ignored) |
| `D:\Apps\000-dotfiles\docs\operations\powertoys-awake-windows.md` | `docs/research-2026-09-19.md` |

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

## 19 September 2026: documentation review

The [adversarial review](adversarial-review-2026-09-19.md) checked the inventory structure, file count, and total size.
The inventory and local runtime each contained 3,271 files totaling 2,319,009,392 bytes.
This check did not repeat the original source-to-copy SHA-256 comparison or every individual artifact hash.
The copy-verification results above remain the historical consolidation record.

## Research scope

The copied research records both successful API calls and unsuccessful
installer/executable attempts, with Microsoft references. Paths in the
historical note describe where tests happened. For current use, run the
helper from this repository as shown in the root README.

Raw machine logs and conversation transcripts were not copied. Relevant
installer codes and diagnostic results are already recorded in the note.
No credentials are part of the consolidation.
