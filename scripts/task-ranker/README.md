# TypeSafe task ranker

This prototype estimates task difficulty with TypeSafe System One.
Local code controls weights, cache reuse, confidence flags, and snapshot readiness.
Scores are advisory. They do not authorize work or change the board.

## Board source

This project uses the local Hermes Kanban board `stay-up`, not GitHub Projects.
This workflow does not need GitHub `read:project` access or a GitHub authorization change.

`docs-derived-tasks.json` is a historical example with five records.
It is not the live board and contains no reliable task readiness state.
Use the exporter for current task IDs, descriptions, statuses, and parent dependencies.

## Export the board

Run these commands from the repository root:

```powershell
hermes kanban --board stay-up list --json
python .\scripts\task-ranker\export_kanban.py --board stay-up --output .\local\stay-up-ranking-tasks.json
```

The exporter reads task details through the Hermes CLI, not the SQLite file.
It includes archived tasks so completed parent states remain available.
It checks task membership and content again before it writes the export.
If the reads show a change, the export fails. Run it again.
The separate CLI reads do not form an atomic snapshot. Changes after the last read can still make it stale.

The exporter sends only list and show commands. It sends no task edit, priority, or status command.
Hermes list can refresh dependency-ready states. Do not treat it as a transaction with no possible writes.
The ranker itself never writes to the board.
The exporter omits comments, run histories, assignees, workspace paths, and attachments.
Task titles and bodies remain in the export. Review this text before sending it to TypeSafe.
Do not include credentials, personal data, or other sensitive content.

The export time is not a new evidence date.
The exporter extracts evidence dates only when the task body contains them.
It does not inspect linked files or verify task claims.
Update stale board descriptions and export again before scoring.

## Python and SDK setup

The exporter, unit tests, and cache-only ranking use the Python standard library.
Live scoring also needs `typesafe-sdk==0.7.0` and `TYPESAFE_API_KEY`.
Supply that key through your approved secret mechanism. Never put it in this repository.

Interpreter environments can differ. Check the selected interpreter rather than assuming that every Python installation lacks `venv`.
For an interpreter with virtual-environment support:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\scripts\task-ranker\requirements.txt
```

If the selected interpreter lacks `venv`, use a local SDK installation:

```powershell
python -m pip install --target .\local\typesafe-python -r .\scripts\task-ranker\requirements.txt
```

Use the same Python version for installation and live scoring.
The script checks `local/typesafe-python` if the SDK is not available through normal imports.
Do not reuse compiled SDK dependencies across incompatible Python versions.
Git ignores `local/`, `.venv/`, and Python bytecode.

## Rank exported tasks

With the SDK and key available to the selected interpreter:

```powershell
python .\scripts\task-ranker\rank_tasks.py .\local\stay-up-ranking-tasks.json --cache .\local\stay-up-ranking-cache.json
```

This command sends exported task text and evidence fields to TypeSafe on a cache miss.
The raw result cache uses task ID, question version, and the evidence fingerprint.
For board exports, the fingerprint also includes board identity, status, and parent states.
Keep live-board results separate from the historical example cache.

Cache writers use an OS lock and merge only new entries with the latest cache.
Each writer uses a unique temporary file before atomic replacement.
The lock wait has a five-second limit. API calls do not hold the cache lock.
Keep the `.lock` file. Do not delete it while a writer can be active.
Windows process-lock tests pass. POSIX locking still needs verification on a POSIX host.

Use cached results without an SDK or network request:

```powershell
python .\scripts\task-ranker\rank_tasks.py .\local\stay-up-ranking-tasks.json --cache .\local\stay-up-ranking-cache.json --cached-only
```

A cache miss in this mode fails. It does not produce a replacement score or call the API.
Add `--json` for machine-readable output.

Supply an optional JSON object with `--weights` to change local dimension weights.
Weight changes reuse raw dimension results without another API call.
All weights must be finite and non-negative, with a finite positive sum.
Change `QUESTION_VERSION` when you change the rubric.
The question version does not pin the remote model. Remove selected cached results when you need a new model evaluation.

## Interpret results

- `EASE`: higher means easier, not more important or ready to start.
- `REVIEW`: at least one dimension has confidence below the selected threshold.
- `STATUS`: task status in the export, or `unverified` for a documentation seed.
- `READY`: the snapshot says `ready`, and every parent says `done` or `archived`.

The default confidence threshold is `0.60`.
Confidence flags and board readiness are separate checks. A high score cannot clear either constraint.
A blocked task stays blocked. A later milestone cannot move before its prerequisites.

Recheck the live board before work. A snapshot can become stale after export.
`READY=yes` does not approve a reboot, capture, idle test, or other controlled action.
The tools never execute the ranked tasks.

## Input and failure checks

Input can be a JSON array or an object with a `tasks` array.
Each task needs unique, non-empty string fields `id` and `task_text`.
The scoring state also includes these fields when supplied:

- `prerequisite_state`
- `applicable_constraints`
- `current_observations`
- `expected_validation`
- `evidence_timestamps`
- `board_state`

The ranker rejects invalid scores, confidence values, and mismatched cached identities.
It keeps raw probability distributions and rubric legends with each result.
API error messages omit the raw service error text to reduce credential exposure.

## Verify

```powershell
python -m unittest discover -s .\scripts\task-ranker -p "test_*.py" -v
python .\scripts\task-ranker\rank_tasks.py .\scripts\task-ranker\docs-derived-tasks.json --cached-only
```

The unit tests use explicit fixtures and make no API calls.
The second command needs the historical cache. It does not verify the live board or its task readiness.
Keep generated exports, caches, and result reports under `local/`.
