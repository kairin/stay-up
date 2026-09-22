# Rust-only migration decision record

> **Status:** Paused after research. Implementation is pending.

Date: 22 September 2026

This record evaluates a Python-free stay-up application, launcher, and owned
maintained tools. It is a planning record. It reports no new application,
Cargo, tool, or runtime test.

## Scope and gates

The required endpoint has three stages:

1. Run the UI, power helper, and monitor in Rust while the Python launcher
   remains as a transitional bootstrap.
2. Replace the Python launcher with a native launcher. This completes the
   Python-free application and launcher endpoint.
3. Port every retained owned maintained Python tool and test to Rust, or record
   an explicit retirement or archive decision. The withdrawn capture tool is
   excluded from reimplementation and needs that explicit record.

The historical Python baseline is a hold and rollback comparator. It fails the
Python-free endpoint and is not a fourth candidate.

| Candidate | Gate |
| --- | --- |
| M1 separate native helper and monitor binaries | Plan-compatible. Native implementation acceptance remains pending. |
| M2 one binary with explicit modes across three processes | Plan-compatible. GUI and console behavior plus native acceptance remain pending. |
| M3 one Rust process | Ineligible while separate process observation and current pane meaning remain required. A product decision can reopen it. |
| Python baseline | Hold and rollback comparator. It fails the endpoint. |

Accepted visible panes, manual helper behavior, heartbeat format and interval,
Stop behavior, process and window identity, canonical logs, approved AppData
paths, Windows policy, and sorted launcher JSON remain hard constraints. Scores
cannot waive these gates. The migration adds no capture work.

## Facts, proposals, and unknowns

Facts come from source commit
d459cbfd6cad7fae0bd3219874f1e3d0de1cd46d. The source digest record captured
before final document edits is
[research/rust-migration/source-digests.json](../research/rust-migration/source-digests.json).
The final document and README hashes are recorded separately after this revision.

Observed facts:

- src/main.rs starts two Python children and waits for a helper PID handshake.
- src/ui.rs owns two Child handles and uses forced kill and wait on ordinary
  Stop. The current Stop path kills the monitor before the helper, so a final
  STOPPED record is not guaranteed. UI death does not automatically terminate
  either child.
- launch.py validates the fixed checkout and approved AppData paths, builds
  stay-watch, checks the exact process image and owned window, and uses a
  hashed checkout mutex.
- scripts/keep-awake.py creates one power request, sets SYSTEM and DISPLAY
  requests, clears acquired requests in reverse order, and closes its handle.
- scripts/monitor-helper.py opens SYNCHRONIZE, writes local-time ISO lines,
  polls the helper, and records STOPPED or ERROR. Its heartbeat proves process
  liveness only. It does not prove power, lock, sleep, or idle state.
- src/main.rs:3 uses the Windows GUI subsystem. README.md:48 documents manual
  helper Ctrl+C and visible helper output.
- scripts/task-ranker/requirements.txt declares typesafe-sdk==0.7.0.
  export_kanban.py invokes the external Hermes CLI. This repository does not
  establish whether Hermes itself is Python-free.
- No maintained .ps1, .sh, .cmd, or .bat files appear under scripts.
  PowerToys scripts, historical vendor data, and generated data are exclusions.

Proposals:

- Share native power and monitor modules. Use small entrypoints or modes.
- Emit a bounded ready record after successful PowerSetRequest calls. Preserve
  stdout, log text, local offset and precision, flush behavior, interval, and
  direct Ctrl+C cleanup.
- Build the native launcher first with external Cargo or an approved prebuilt
  executable. Later builds use repeated --bin options for runtime targets and
  exclude the launcher.
- Port one accepted slice at a time. Keep rollback to the previous accepted
  slice.
- Add no service, scheduler, async runtime, GUI framework, installer, updater,
  IPC bus, Job Object hardening, or capture implementation for this port.

Unknowns:

- Native Win32 binding and console control implementation.
- Direct UI invocation under the proposed M2 console-subsystem route.
- Native launcher bootstrap distribution and offline dependency cache.
- Hermes implementation language and ownership boundary.
- All native behavior and tool parity remain untested in this review.

The relevant Windows contracts include
[PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest),
[PowerClearRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powerclearrequest),
[SetConsoleCtrlHandler](https://learn.microsoft.com/en-us/windows/console/setconsolectrlhandler),
[std::process::exit](https://doc.rust-lang.org/std/process/fn.exit.html),
[Rust Child](https://doc.rust-lang.org/std/process/struct.Child.html),
[WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject),
and [Cargo build options](https://doc.rust-lang.org/cargo/commands/cargo-build.html).

## Maintained tool inventory and dispositions

| Current Python file | Proposed Rust file or action | Behavior and acceptance | Stage |
| --- | --- | --- | --- |
| launch.py | src/launcher.rs and src/bin/stay-up-launch.rs | Port path, mutex, build, process, window, and JSON behavior. | Native endpoint |
| scripts/keep-awake.py | src/power.rs and src/bin/keep-awake.rs | Port power requests, partial cleanup, Ctrl+C, ready output, and cleanup errors. | Runtime |
| scripts/monitor-helper.py | src/monitor.rs and src/bin/monitor-helper.rs | Port PID wait, local timestamp, append, flush, interval, and records. | Runtime |
| scripts/test_launch.py | tests/launcher.rs | Port launcher validation, mutex, identity, startup, and JSON tests. | Native endpoint |
| scripts/verify_output_panes.py | Rust desktop harness under tests or tools | Port panes, owned process checks, log prefix, heartbeat, Stop, resize, and minimize checks. | After runtime parity |
| scripts/windows-state-probe.py | Rust state probe or explicit retirement record | Preserve only if the state evidence remains required. | Tool phase |
| scripts/terminal-target-probe.py | Rust terminal probe or explicit retirement record | Preserve only if terminal evidence remains required. | Tool phase |
| scripts/capture-feasibility-probe.py | Archive or retire with an explicit record | Withdrawn capture scope needs no reimplementation or capture test. | Tool decision |
| scripts/test_feasibility_probes.py | Rust probe tests or explicit retirement record | Keep evidence checks that remain required. | Tool phase |
| scripts/task-ranker/rank_tasks.py | Existing scripts/task-ranker Rust tool crate proposal | Port ranking, cache, confidence, and weight behavior. | Tool phase |
| scripts/task-ranker/export_kanban.py | Existing scripts/task-ranker Rust tool crate proposal | Port read-only Hermes export behavior. Do not replace Hermes with SQLite or an invented CLI. | Tool phase |
| scripts/task-ranker/test_rank_tasks.py | Rust ranker tests | Port score, cache, lock, and input checks. | Tool phase |
| scripts/task-ranker/test_export_kanban.py | Rust exporter tests | Port membership, content, and stale-export checks. | Tool phase |

The Rust fixtures scripts/rust-execution-probe.rs,
scripts/rust-state-probe.rs, and scripts/rust-install-check/ can be reused if
they provide the required evidence. The external Hermes CLI remains outside
application deployment. The complete developer workflow cannot be called
Python-free until its ownership and implementation boundary are known.

## Candidates

### M1: separate native helper and monitor binaries

The GUI Rust UI starts native console helper and monitor binaries. The runtime
still has three processes. One Cargo package supplies shared power and monitor
modules and small entrypoints, so the binaries do not duplicate implementations.

M1 keeps the same parent-owned two Child handles, external monitor process
handle, helper power handle, explicit partial cleanup, ordinary forced Stop, and
UI-crash child gap as M2. Direct helper mode has control handling and visible
output. GUI child startup stays hidden. Costs include three runtime artifacts,
sibling path wiring, and same-release builds.

### M2: one Rust binary with explicit modes

One runtime binary serves UI, helper, and monitor modes. It still runs as three
processes. Mode dispatch occurs before UI, log, or power side effects. It uses
the same parent-owned handles and external monitor semantics as M1.

The proposed route uses a console-subsystem runtime. The native launcher starts
the UI hidden, owned helper modes hidden, and manual helper mode with terminal
output and control handling. Direct UI invocation behavior is untested and needs
a decision. M2 has fewer runtime artifacts and no helper-image version mismatch.
It has more mode dispatch paths and unresolved GUI and console behavior.

### M3: one Rust process with internal modules

One process owns the UI, power request, and monitor modules. It has no external
helper or monitor observer. It changes process identity, pane meaning, startup
coordination, cancellation, panic behavior, and liveness semantics. It can
reduce child startup and sibling path coordination. It is conditional on an
explicit product decision that accepts those changes.

## Rubric and arithmetic

TypeSafe Score returns an expected ordered level and confidence from its
distribution. Confidence is not correctness or runtime acceptance. See the
[Score primitive](https://docs.typesafe.ai/primitives/score),
[composite scoring](https://docs.typesafe.ai/patterns/composite-scoring), and
[confidence guidance](https://docs.typesafe.ai/confidence).

The fixed weights are behavior preservation 25, implementation simplicity 20,
ownership and failure clarity 20, build and distribution simplicity 15,
testability and rollback 10, and maintenance cost 10.

Each criterion uses levels 0 through 4. The full level descriptions are in the
immutable round3-matrix.json. Their anchors are:

| Criterion | Level 0 | Level 2 | Level 4 |
| --- | --- | --- | --- |
| Behavior preservation | Breaks accepted visible, manual, heartbeat, or protocol behavior. | Preserves several observable contracts but leaves material gaps. | Preserves all observable, manual, log, and protocol contracts with no unresolved behavior change. |
| Implementation simplicity | Broad redesign or unrelated machinery. | Moderate focused change with material coordination. | Smallest coherent endpoint change. |
| Ownership and failure clarity | Ownership is ambiguous. | Partial ownership with material lifecycle risks. | Clear process, handle, error, and cleanup responsibility. |
| Build and distribution simplicity | Fragile bootstrap or changed paths. | Workable build with unresolved bootstrap decisions. | Simple reproducible approved-path sequence. |
| Testability and rollback | Cannot isolate or restore baseline. | Partial isolation with material untested areas. | Small isolated tests, comparison, and rollback per slice. |
| Maintenance cost | High duplication or framework burden. | Moderate burden or duplicated contracts. | Minimal code, dependency, and contract maintenance. |

The behavior criterion does not score rollback. The testability criterion scores
rollback. The levels are ordinal anchors treated as equally spaced for this
decision aid. The composites are planning estimates, not calibrated effort,
success rates, or causal proof of improvement.

Profiles declared before inference were preservation-heavy (35, 15, 25, 5,
15, 5) and simplicity-heavy (20, 35, 15, 20, 5, 5). A margin below 5 points
triggers policy review. It is not a statistical claim.

## Round history

### Round One

Round One used the initial endpoint scope. Maintained tools were separate from
the application and launcher endpoint. Its 21 questions included 18 candidate
Scores and three broad quality Scores.

| Candidate | Default | Preservation-heavy | Simplicity-heavy |
| --- | ---: | ---: | ---: |
| M1 | 69.600 | 72.038 | 66.987 |
| M2 | 52.650 | 51.500 | 51.775 |
| M3 | 27.375 | 19.962 | 29.438 |

Round One quality Scores were fairness 2.62/confidence 0.52, completeness
2.25/0.47, and overengineering 2.59/0.48. Round One used broad quality anchors.
Its raw request and response remain immutable. Its derived analysis was updated
later to include the omitted quality fields; it is not the raw evidence.

[Round One matrix](../research/rust-migration/round1-matrix.json) |
[request](../research/rust-migration/round1-request.json) |
[response](../research/rust-migration/round1-response.json) |
[manifest](../research/rust-migration/round1-manifest.json) |
[analysis](../research/rust-migration/round1-analysis.json)

### Round Two

Round Two corrected candidate fields and expanded the endpoint to all owned
maintained tools. Its raw request and response remain immutable. Its quality
questions only asserted symmetry and did not contain the full sibling
definitions, gates, or matrix. Its fairness Score 0.86/confidence 0.28 is an
input error, not an architectural verdict. The derived action ledger correction
is separate from the raw response.

Round Two default totals were M1 64.763, M2 59.438, and M3 32.763. The
preservation-heavy totals were 66.675, 58.975, and 28.212. The
simplicity-heavy totals were 62.637, 58.763, and 32.175.

[Round Two matrix](../research/rust-migration/round2-matrix.json) |
[request](../research/rust-migration/round2-request.json) |
[response](../research/rust-migration/round2-response.json) |
[manifest](../research/rust-migration/round2-manifest.json) |
[analysis](../research/rust-migration/round2-analysis.json)

### Round Three

Round Three corrected the quality input, removed behavior and rollback overlap,
expanded every tool disposition, and scored M1 and M2 ownership once with a
candidate-neutral question. The same answer and probability distribution was
assigned to both. This corrects double-counting. It does not prove the
implementations equivalent.

The request contained 17 design questions and three quality questions. The
quality questions included all candidate definitions, anchors, weights, gates,
tool dispositions, and evidence sources. The candidate questions contained only
common facts and proposals plus the target design.

TypeSafe resolved jev-latest to jev-1.13.0. Usage was 30,056 input tokens and
387 output tokens.

[Round Three matrix](../research/rust-migration/round3-matrix.json) |
[request](../research/rust-migration/round3-request.json) |
[response](../research/rust-migration/round3-response.json) |
[manifest](../research/rust-migration/round3-manifest.json)

## Round Three results

### Weighted totals

| Candidate | Default | Preservation-heavy | Simplicity-heavy |
| --- | ---: | ---: | ---: |
| M1 | 62.987 | 66.688 | 60.425 |
| M2 | 55.025 | 56.337 | 53.763 |
| M3 | 29.438 | 25.863 | 29.275 |

M1 remains first in every profile. Its default margin over M2 is 7.962 points.
Its smallest one-criterion relative plus or minus 20 percent margin is 7.224
points. M2 remains above M3 in every profile. Sensitivity does not cover model,
anchor, or evidence uncertainty.

### Per-criterion scores

Each cell is score/confidence. M1 and M2 ownership use the one shared answer.

| Criterion | M1 | M2 | M3 |
| --- | ---: | ---: | ---: |
| Behavior preservation | 2.92/0.87 | 2.04/0.60 | 0.11/0.91 |
| Implementation simplicity | 2.24/0.63 | 2.12/0.70 | 1.11/0.66 |
| Ownership and failure clarity | 2.79/0.55 | 2.79/0.55 | 1.43/0.47 |
| Build and distribution simplicity | 1.91/0.78 | 1.82/0.75 | 1.80/0.63 |
| Testability and rollback | 2.68/0.43 | 2.15/0.86 | 1.96/0.79 |
| Maintenance cost | 2.29/0.40 | 2.21/0.54 | 1.76/0.35 |

Quality results:

| Quality question | Score | Confidence |
| --- | ---: | ---: |
| Fairness | 2.17 | 0.10 |
| Completeness | 3.28 | 0.64 |
| Overengineering | 3.48 | 0.57 |

The fairness confidence is very low. Human review remains required. The
weighted result supports a provisional staged M1 route. M2 remains credible,
especially if its console route removes a measured maintenance burden without
changing behavior. M3 remains gate-ineligible.

### Arithmetic and provenance checks

The local checker validated 20 answers, finite scores and probabilities, level
keys, probability sums within 0.025, and shared M1/M2 ownership equality. The
maximum score versus probability-weighted level discrepancy was 0.03. The
accepted tolerance is 0.055: 0.05 allows five independently rounded
probabilities and 0.005 allows score rounding. This is a rounding bound, not
model uncertainty.

The final source hash record is
research/rust-migration/final-source-digests.json. Round Two source digests do
not certify this edited document.

## Actions and residual risks

| Weakness or risk | Minimal action | Acceptance evidence | Owner role | Decision effect | Residual risk |
| --- | --- | --- | --- | --- | --- |
| Fairness 2.17/confidence 0.10 | Keep common fields and criterion-specific anchors. Require human comparison. | Parent review of matrix and tool dispositions. | Architecture reviewer | No further model round for score chasing. | Semantic comparison can remain uneven. |
| M1 build score 1.91 | Build sibling outputs in one release and keep shared modules. | Locked offline build and helper/monitor acceptance. | Runtime implementer | M1 remains provisional. | Same-release path wiring remains. |
| M1 testability confidence 0.43 | Port one helper slice at a time with rollback. | Native tests and rollback record per slice. | Runtime reviewer | No broad rewrite. | Native Win32 behavior remains unknown. |
| M1 maintenance confidence 0.40 | Reuse modules and keep tools in a separate phase. | Rust tool ports or explicit retire records. | Tooling owner | Avoid new framework. | Tool scope is large. |
| M2 build score 1.82 | Decide native bootstrap and console-subsystem route before selection. | Direct UI, hidden modes, manual helper, and launcher checks. | Windows-runtime reviewer | M2 remains credible but deferred. | Direct invocation may differ. |
| M3 behavior 0.11 and gate conflict | Keep M3 conditional while external observation is required. | Product scope decision and new tests. | Product owner | Do not select M3 now. | In-process panic and cancellation rules remain. |
| Hermes boundary unknown | Inspect ownership and language before claiming the full workflow is Python-free. | Tool decision and Hermes evidence. | Tooling owner | No claim beyond repository-owned source. | External CLI may remain outside control. |
| Stop order and STOPPED record | Preserve monitor-before-helper kill order and state that STOPPED is not guaranteed. | Future Stop and log tests. | Runtime reviewer | No forced final log promise. | Existing forced kill can skip cleanup. |
| Native acceptance unrun | Run future helper, monitor, launcher, and tool tests only after implementation. | Dated test records and source hashes. | Implementation reviewer | Scores remain planning estimates. | Plan may not match Windows behavior. |

The machine-readable action ledger is
[research/rust-migration/round3-action-ledger.json](../research/rust-migration/round3-action-ledger.json).

## Code-change map and rollback

| Current file or group | Proposed Rust file or action | Behavior and tests | Stage |
| --- | --- | --- | --- |
| src/main.rs | Proposed native sibling launch and bounded ready handling. Remove Python discovery and .py checks. | Preserve startup, helper-ready flush, and failure cleanup tests. | Runtime |
| src/lib.rs | Proposed native argument builders. | Preserve helper, monitor, and log path arguments. | Runtime |
| src/ui.rs | Proposed native labels and owned-child wiring while preserving layout and Stop order. | Preserve monitor-before-helper Stop and UI-crash gap semantics. | Runtime |
| src/output.rs | Reuse unchanged initially. | Preserve bounded log reads and pane behavior. | Runtime |
| Cargo.toml and Cargo.lock | Add native helper and monitor targets, then native launcher target with scoped locked dependencies. | Preserve approved offline build and target paths. | Runtime, then endpoint |
| launch.py | Proposed src/launcher.rs and src/bin/stay-up-launch.rs | Preserve paths, mutex, build, process, window, and JSON tests. | Launcher endpoint |
| scripts/keep-awake.py | Proposed src/power.rs and src/bin/keep-awake.rs | Preserve requests, partial cleanup, ready output, Ctrl+C, and cleanup errors. | Runtime |
| scripts/monitor-helper.py | Proposed src/monitor.rs and src/bin/monitor-helper.rs | Preserve PID wait, timestamp, append, flush, interval, and records. | Runtime |
| scripts/test_launch.py | Proposed tests/launcher.rs | Port launcher validation, mutex, identity, startup, and JSON checks. | Launcher endpoint |
| scripts/verify_output_panes.py | Proposed Rust desktop harness | Port pane, process, log, heartbeat, Stop, resize, and minimize checks. | After runtime parity |
| scripts/windows-state-probe.py | Proposed Rust state probe or retirement record | Preserve required state evidence or record retirement. | Tool phase |
| scripts/terminal-target-probe.py | Proposed Rust terminal probe or retirement record | Preserve required terminal evidence or record retirement. | Tool phase |
| scripts/capture-feasibility-probe.py | Archive or retire | No capture implementation or capture test. | Tool decision |
| scripts/test_feasibility_probes.py | Proposed Rust probe tests or retirement record | Preserve required feasibility checks or record retirement. | Tool phase |
| scripts/task-ranker/rank_tasks.py | Proposed Rust tool crate in existing task-ranker area | Preserve scoring, cache, confidence, and weights. | Tool phase |
| scripts/task-ranker/export_kanban.py | Proposed Rust exporter in the same tool crate | Preserve the documented Hermes list/show interface and its side-effect limits. Do not invent a SQLite replacement. | Tool phase |
| scripts/task-ranker/test_rank_tasks.py | Proposed Rust ranker tests | Preserve score, cache, lock, and input checks. | Tool phase |
| scripts/task-ranker/test_export_kanban.py | Proposed Rust exporter tests | Preserve membership, content, and stale-export checks. | Tool phase |

The Rust fixtures can be reused if sufficient. Roll back each native helper
slice to the previous accepted Python or Rust slice. Roll back launcher work to
launch.py. Do not add an installer, updater, service, scheduler, async runtime,
IPC bus, or Job Object hardening unless a measured failure justifies a separate
tested change.

## Reproducible method and stopping rules

The HTTP endpoint was POST
https://api.typesafe.ai/v1/systemone with model jev-latest. The API key was read
from the process environment and never saved or printed. Each request and
response is stored without credentials. Manifests contain model, UTC, usage,
endpoint, question count, and SHA-256 hashes.

Recalculate offline with the round3 request and response, the fixed weights, the
profiles, and the ordinal-level rule. Do not use a later model response to
change a prior raw artifact. A score change caused by changed state, anchors,
or scope is not a controlled improvement.

Stop after Round Three. Do not run another model round to improve a number.
Reopen only when source evidence, requirements, or implementation code changes,
or when a tool cannot be ported and lacks an explicit retirement decision. A
future round must use a new immutable request and state.

This record makes no implementation, runtime, tool-port, or Windows power
acceptance claim.

## Continuation

The research is paused at the user's request. The implementation remains pending.

Completed evidence:

- Round One used 21 questions. M1 was 69.600, M2 was 52.650, and M3 was
  27.375 under the default profile.
- Round Two used 21 questions with expanded tool scope. M1 was 64.763, M2 was
  59.438, and M3 was 32.763. Its quality input was invalid because the quality
  questions did not contain the full sibling matrix. Its raw request and
  response remain immutable.
- Round Three used 20 questions. It scored shared M1 and M2 ownership once and
  copied that answer to both. M1 was 62.987, M2 was 55.025, and M3 was 29.438.
  Quality fairness was 2.17 with confidence 0.10. This remains uncertain.
- The provisional recommendation is staged M1 with shared modules. M2 remains
  credible after console and direct-invocation evidence. M3 remains ineligible
  while separate observation and current pane meaning remain required.
- Round Three input, response, arithmetic, action, and hash records are under
  research/rust-migration/. The final hash record is
  research/rust-migration/final-source-digests.json.
- The current source commit is d459cbfd6cad7fae0bd3219874f1e3d0de1cd46d.
  Uncommitted documentation paths are README.md,
  docs/rust-only-migration-review.md, and research/rust-migration/.

These are future implementation tasks. They do not start automatically from this paused research record.

Smallest next actions, in order:

1. Decide the native bootstrap sequence and dependency cache under approved
   AppData paths.
2. Port the power helper and monitor with shared Rust modules. Preserve partial
   cleanup, bounded readiness, Ctrl+C handling, timestamps, flush, interval,
   and existing records.
3. Port the launcher and pane tests. Verify the monitor-before-helper Stop
   order and the fact that STOPPED is not guaranteed.
4. Decide and test the M2 console route before selecting M2.
5. Port every retained owned tool and test to Rust, or record an explicit
   retirement or archive decision. Resolve the external Hermes boundary.
6. Reopen M3 only after a product decision accepts changed observation and
   cleanup semantics.

Do not rerun TypeSafe to improve a score. Do not run application, Cargo, helper,
probe, capture, or environment tests for this documentation pause. Reopen the
decision only after source evidence, requirements, or implementation code
changes, or when a tool lacks a port and an explicit retirement decision.
