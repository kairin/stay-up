#!/usr/bin/env python3
"""Export local Hermes tasks through CLI list and show commands."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


STATUSES = {"triage", "todo", "scheduled", "ready", "running", "blocked", "review", "done", "archived"}


def read_board(board: str, *args: str) -> Any:
    result = subprocess.run(
        ["hermes", "kanban", "--board", board, *args, "--json"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if result.returncode:
        raise RuntimeError("Hermes board read failed. Check the board and CLI access.")
    return json.loads(result.stdout)


def section(body: str, name: str) -> list[str]:
    match = re.search(r"^## " + re.escape(name) + r"\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return [match.group(1).strip()] if match else []


def build_export(board: str, details: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = {}
    for detail in details:
        task = detail["task"]
        task_id = task["id"]
        if not isinstance(task_id, str) or not re.fullmatch(r"t_[0-9a-f]{8}", task_id):
            raise ValueError("Invalid Hermes task ID.")
        if task_id in tasks:
            raise ValueError("Duplicate Hermes task ID.")
        if task["status"] not in STATUSES or not isinstance(task["title"], str):
            raise ValueError("Invalid Hermes task state.")
        tasks[task_id] = task
    exported = []
    for detail in sorted(details, key=lambda item: item["task"]["id"]):
        task = detail["task"]
        body = task.get("body") or ""
        if not isinstance(body, str):
            raise ValueError("Task body must be text.")
        parents = []
        for parent_id in sorted(detail["parents"]):
            if parent_id not in tasks:
                raise ValueError("A parent is absent from the export. Do not infer its state.")
            parents.append({"id": parent_id, "status": tasks[parent_id]["status"]})
        exported.append({
            "id": task["id"],
            "task_text": task["title"] + ("\n\n" + body if body else ""),
            "prerequisite_state": parents,
            "applicable_constraints": [
                "Task status and parent dependencies are hard constraints.",
                "A score cannot authorize execution or override test approval.",
                "Do not infer completed work from an advisory score.",
            ],
            "current_observations": section(body, "Current state"),
            "expected_validation": section(body, "Acceptance"),
            "evidence_timestamps": sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", body))),
            "board_state": {"board": board, "status": task["status"], "parents": parents},
        })
    return {
        "source": "Local Hermes Kanban. This is not GitHub Project data.",
        "board": board,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tasks": exported,
    }


def export_board(board: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", board):
        raise ValueError("Invalid board identifier.")
    initial = read_board(board, "list", "--archived")
    ids = [task["id"] for task in initial]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate board task IDs.")
    details = [read_board(board, "show", task_id) for task_id in ids]
    for task_id, detail in zip(ids, details):
        if detail["task"]["id"] != task_id:
            raise ValueError("Task identity changed during export.")
    result = build_export(board, details)
    repeated = [read_board(board, "show", task_id) for task_id in ids]
    final = read_board(board, "list", "--archived")
    if len(final) != len(ids) or {task["id"] for task in final} != set(ids):
        raise RuntimeError("Board membership changed during export. Export again.")
    if build_export(board, repeated)["tasks"] != result["tasks"]:
        raise RuntimeError("Board content changed during export. Export again.")
    final_tasks = {task["id"]: task for task in final}
    final_details = [dict(detail, task=final_tasks[detail["task"]["id"]]) for detail in repeated]
    if build_export(board, final_details)["tasks"] != result["tasks"]:
        raise RuntimeError("Board content changed during export. Export again.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = export_board(args.board)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Exported {len(result['tasks'])} tasks from {args.board} to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"Export failed ({type(error).__name__}). Check the board schema and CLI access.", file=sys.stderr)
        raise SystemExit(2)
