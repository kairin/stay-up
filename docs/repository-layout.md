# Repository layout

Use one owned directory for each purpose.
Use lowercase hyphen names for owned directories. Keep framework, vendor, and generated cache names when their format requires them.

| Path | Purpose |
| --- | --- |
| `launch.py` | Supported root command that builds and starts the application. |
| `scripts/` | Application helpers, tests, probes, and task-ranker scripts. |
| `logs/` | The active log, archived logs, and review evidence. |
| `local/` | Generated non-log evidence, caches, and local dependencies. |
| `Cargo.toml`, `Cargo.lock`, `src/` | The Rust Cargo package and its source. |
| `docs/` | Project instructions, plans, and recorded results. |
| `research/` | The unchanged third-party source snapshot. |

Use `python .\launch.py` from the repository root. Use the paths in `scripts/`
for helper and verification commands. Historical records can show former paths.
They describe their original runs. Current commands use the canonical paths.
