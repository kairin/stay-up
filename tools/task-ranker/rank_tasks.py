#!/usr/bin/env python3
"""Rank task records with cached TypeSafe System One dimension scores."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import errno
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

QUESTION_VERSION = "stay-up-ease-v1"
DEFAULT_CONFIDENCE_THRESHOLD = 0.60
DEFAULT_WEIGHTS = {
    "implementation_effort": 0.25,
    "dependency_burden": 0.15,
    "manual_test_burden": 0.20,
    "policy_risk": 0.15,
    "existing_evidence_strength": 0.15,
    "validation_clarity": 0.10,
}
INVERTED_DIMENSIONS = {
    "implementation_effort",
    "dependency_burden",
    "manual_test_burden",
    "policy_risk",
}

DIMENSIONS = {
    "implementation_effort": {
        "instructions": "Rate the implementation effort needed to resolve this task from the supplied current state.",
        "criteria": [
            "Very low: run an existing command or make a trivial isolated change",
            "Low: a small isolated implementation or short check",
            "Moderate: several changes or coordinated components",
            "High: substantial implementation or difficult integration",
            "Very high: major unknowns or a large new subsystem",
        ],
    },
    "dependency_burden": {
        "instructions": "Rate how strongly unresolved prerequisites or external dependencies block this task.",
        "criteria": [
            "None: all prerequisites are satisfied and no external dependency blocks work",
            "Low: one straightforward prerequisite remains",
            "Moderate: multiple prerequisites remain but are understood",
            "High: important prerequisites are unresolved or externally controlled",
            "Very high: the task cannot currently proceed because critical prerequisites are unavailable",
        ],
    },
    "manual_test_burden": {
        "instructions": "Rate the time and coordination burden of the manual validation needed to resolve this task.",
        "criteria": [
            "Very low: an immediate deterministic check",
            "Low: a short focused manual check",
            "Moderate: several manual cases or controlled setup",
            "High: prolonged observation or multiple environmental conditions",
            "Very high: lengthy repeated tests across difficult-to-control conditions",
        ],
    },
    "policy_risk": {
        "instructions": "Rate the risk that permissions, managed-machine policy, or required authorization will block this task.",
        "criteria": [
            "None: ordinary user access is already demonstrated sufficient",
            "Low: no expected policy change and only familiar user permissions are needed",
            "Moderate: permission or policy behavior still needs verification",
            "High: a managed-machine restriction is likely to interfere",
            "Very high: a known restriction blocks the required action or an authorized policy change is required",
        ],
    },
    "existing_evidence_strength": {
        "instructions": "Rate how much fresh, task-specific evidence already supports resolving this task.",
        "criteria": [
            "None: no relevant evidence exists",
            "Weak: indirect, stale, or static evidence only",
            "Moderate: relevant observations exist but important checks are missing",
            "Strong: most required evidence is current and directly relevant",
            "Very strong: current direct evidence nearly or fully satisfies validation",
        ],
    },
    "validation_clarity": {
        "instructions": "Rate how clear and objectively checkable the expected validation is.",
        "criteria": [
            "Unclear: success is not defined",
            "Weak: success is subjective or important outcomes are omitted",
            "Moderate: the main result is defined but edge conditions remain",
            "Clear: concrete expected results and failure conditions are supplied",
            "Very clear: deterministic checks, evidence requirements, and limits are all explicit",
        ],
    },
}

FINGERPRINT_FIELDS = (
    "task_text",
    "prerequisite_state",
    "applicable_constraints",
    "current_observations",
    "expected_validation",
    "evidence_timestamps",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path, help="JSON file containing a task array or a {tasks: [...]} object")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("local/task-ranker-cache.json"),
        help="raw result cache (default: local/task-ranker-cache.json)",
    )
    parser.add_argument("--weights", type=Path, help="optional JSON object overriding dimension weights")
    parser.add_argument("--confidence-threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD)
    parser.add_argument("--cached-only", action="store_true", help="do not call TypeSafe for cache misses")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_tasks(path: Path) -> list[dict[str, Any]]:
    value = read_json(path)
    tasks = value.get("tasks") if isinstance(value, dict) else value
    if not isinstance(tasks, list):
        raise ValueError("task input must be a JSON array or an object with a 'tasks' array")
    seen_ids = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or any(
            not isinstance(task.get(field), str) or not task[field].strip()
            for field in ("id", "task_text")
        ):
            raise ValueError(f"task {index} must contain non-empty 'id' and 'task_text' fields")
        if task["id"] in seen_ids:
            raise ValueError(f"duplicate task id: {task['id']}")
        seen_ids.add(task["id"])
    return tasks


def task_state(task: dict[str, Any]) -> dict[str, Any]:
    state = {field: task.get(field, []) for field in FINGERPRINT_FIELDS}
    if "board_state" in task:
        state["board_state"] = task["board_state"]
    return state


def evidence_fingerprint(task: dict[str, Any]) -> str:
    encoded = json.dumps(task_state(task), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entries": {}}
    value = read_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("entries"), dict):
        raise ValueError(f"invalid cache structure in {path}")
    return value


@contextmanager
def _cache_lock(path: Path, timeout: float):
    """Lock cache I/O across processes on Windows and POSIX.

    Wait at most timeout seconds for the OS lock. Keep the lock file.
    The OS releases the lock when the handle closes or the process exits.
    Do not delete the lock file or make API calls inside this context.
    """
    if os.name == "nt":
        import msvcrt
    else:
        import fcntl
    with path.open("a+b") as stream:
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("Cache lock wait timed out. Try again.") from None
                time.sleep(min(0.05, remaining))
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def save_cache(path: Path, updates: dict[str, Any], *, lock_timeout: float = 5.0) -> None:
    """Merge new entry updates with the latest cache under an OS lock.

    Pass only new entries, not a full cache snapshot. The last writer wins
    for keys in updates["entries"]. Keep all other entries and cache metadata.
    Wait at most lock_timeout seconds for the lock. Lock only cache I/O.
    Write a unique file in the cache directory, then replace the cache atomically.
    Remove only this temporary file on failure. Never delete the lock file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with _cache_lock(path.with_suffix(path.suffix + ".lock"), lock_timeout):
        cache = load_cache(path)
        cache["entries"].update(updates["entries"])
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=path.name + ".", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(json.dumps(cache, indent=2, sort_keys=True) + "\n")
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def cache_key(task: dict[str, Any]) -> str:
    return f"{task['id']}:{QUESTION_VERSION}:{evidence_fingerprint(task)}"


def import_sdk() -> tuple[Any, Any]:
    try:
        from typesafe_sdk import Score, TypeSafeClient
    except ImportError:
        local_sdk = Path(__file__).resolve().parents[2] / "local" / "typesafe-python"
        if local_sdk.is_dir():
            sys.path.insert(0, str(local_sdk))
            from typesafe_sdk import Score, TypeSafeClient
        else:
            raise RuntimeError(
                "typesafe-sdk is unavailable; install it with 'python -m pip install typesafe-sdk'"
            ) from None
    return Score, TypeSafeClient


def evaluate(task: dict[str, Any]) -> dict[str, Any]:
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("TYPESAFE_API_KEY is not set")
    Score, TypeSafeClient = import_sdk()
    questions = {
        name: Score(instructions=definition["instructions"], criteria=definition["criteria"])
        for name, definition in DIMENSIONS.items()
    }
    try:
        with TypeSafeClient() as client:
            response = client.system_one(state=task_state(task), questions=questions)
    except Exception as error:
        raise RuntimeError(f"TypeSafe request failed ({type(error).__name__}). Check service access.") from None
    try:
        dimensions = {}
        scores = response.scores
        for name in DIMENSIONS:
            answer = scores[name]
            dimensions[name] = {
                "score": answer.score,
                "confidence": answer.confidence,
                "probabilities": answer.probabilities,
                "legend": answer.legend,
            }
            probabilities = dimensions[name]["probabilities"]
            if not isinstance(probabilities, dict) or any(
                not isinstance(key, (str, int)) or isinstance(key, bool) or isinstance(value, bool)
                or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not 0 <= value <= 1
                for key, value in probabilities.items()
            ):
                raise ValueError("Invalid score probabilities.")
            legend = dimensions[name]["legend"]
            if not isinstance(legend, dict) or any(
                not isinstance(key, (str, int)) or isinstance(key, bool) or not isinstance(value, (str, dict, list))
                for key, value in legend.items()
            ):
                raise ValueError("Invalid score legend.")
        raw = {
            "task_id": task["id"],
            "question_version": QUESTION_VERSION,
            "evidence_fingerprint": evidence_fingerprint(task),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "model": response.model,
            "dimensions": dimensions,
        }
        validate_raw(task, raw)
        json.dumps(raw, allow_nan=False, sort_keys=True)
    except Exception:
        raise RuntimeError("TypeSafe response is invalid. Check service access.") from None
    return raw


def load_weights(path: Path | None) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    if path:
        overrides = read_json(path)
        if not isinstance(overrides, dict):
            raise ValueError("weights must be a JSON object")
        unknown = set(overrides) - set(DIMENSIONS)
        if unknown:
            raise ValueError(f"unknown weight dimensions: {', '.join(sorted(unknown))}")
        weights.update({name: float(value) for name, value in overrides.items()})
    if any(not math.isfinite(value) or value < 0 for value in weights.values()):
        raise ValueError("weights must be finite and non-negative")
    if not math.isfinite(sum(weights.values())) or sum(weights.values()) <= 0:
        raise ValueError("the weight sum must be finite and positive")
    return weights


def validate_raw(task: dict[str, Any], raw: dict[str, Any]) -> None:
    if not isinstance(raw, dict) or any(
        raw.get(field) != expected
        for field, expected in (
            ("task_id", task["id"]),
            ("question_version", QUESTION_VERSION),
            ("evidence_fingerprint", evidence_fingerprint(task)),
        )
    ):
        raise ValueError("cached result identity does not match the task")
    if not isinstance(raw.get("model"), str) or not isinstance(raw.get("evaluated_at"), str):
        raise ValueError("result metadata is missing")
    dimensions = raw.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ValueError("result dimensions do not match the questions")
    for name, dimension in dimensions.items():
        if not isinstance(dimension, dict):
            raise ValueError("invalid result dimension")
        for field, upper in (("score", len(DIMENSIONS[name]["criteria"]) - 1), ("confidence", 1)):
            value = dimension.get(field)
            if isinstance(value, bool) or not isinstance(value, (float, int)):
                raise ValueError(f"{name} {field} must be a number")
            if not math.isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f"{name} {field} is outside the permitted range")


def snapshot_readiness(task: dict[str, Any]) -> dict[str, Any]:
    state = task.get("board_state")
    if state is None:
        return {"board_status": "unverified", "ready_in_snapshot": False, "open_parents": []}
    if not isinstance(state, dict) or not isinstance(state.get("parents"), list):
        raise ValueError("invalid board snapshot")
    statuses = {"triage", "todo", "scheduled", "ready", "running", "blocked", "review", "done", "archived"}
    if state.get("status") not in statuses or not isinstance(state.get("board"), str):
        raise ValueError("invalid board status or identifier")
    open_parents = []
    for parent in state["parents"]:
        if not isinstance(parent, dict) or parent.get("status") not in statuses or not isinstance(parent.get("id"), str):
            raise ValueError("invalid parent state")
        if parent["status"] not in {"done", "archived"}:
            open_parents.append(parent["id"])
    return {
        "board_status": state["status"],
        "ready_in_snapshot": state["status"] == "ready" and not open_parents,
        "open_parents": open_parents,
    }


def compose_result(
    task: dict[str, Any], raw: dict[str, Any], weights: dict[str, float], confidence_threshold: float
) -> dict[str, Any]:
    validate_raw(task, raw)
    weighted_total = 0.0
    scale = max(weights.values())
    scaled_weights = {name: weight / scale for name, weight in weights.items()}
    total_weight = sum(scaled_weights.values())
    reviews = []
    for name, weight in scaled_weights.items():
        dimension = raw["dimensions"][name]
        normalized = float(dimension["score"]) / (len(DIMENSIONS[name]["criteria"]) - 1)
        ease_component = 1.0 - normalized if name in INVERTED_DIMENSIONS else normalized
        weighted_total += weight * ease_component
        if float(dimension["confidence"]) < confidence_threshold:
            reviews.append({"dimension": name, "confidence": dimension["confidence"]})
    ease_score = 100.0 * (weighted_total / total_weight)
    if not math.isfinite(ease_score):
        raise ValueError("Ease score must be finite.")
    ease_score = round(min(100.0, max(0.0, ease_score)), 2)
    return {
        "id": task["id"],
        "task_text": task["task_text"],
        "ease_score": ease_score,
        "review_required": bool(reviews),
        "low_confidence_dimensions": reviews,
        "model": raw["model"],
        "evaluated_at": raw["evaluated_at"],
        "evidence_fingerprint": raw["evidence_fingerprint"],
        "dimensions": raw["dimensions"],
        **snapshot_readiness(task),
    }


def main() -> int:
    args = parse_args()
    if not 0 <= args.confidence_threshold <= 1:
        raise ValueError("confidence threshold must be between 0 and 1")
    tasks = load_tasks(args.tasks)
    for task in tasks:
        snapshot_readiness(task)
    cache = load_cache(args.cache)
    weights = load_weights(args.weights)
    misses = []
    raw_results = {}
    for task in tasks:
        key = cache_key(task)
        if key in cache["entries"]:
            raw_results[task["id"]] = cache["entries"][key]
        elif args.cached_only:
            misses.append(task["id"])
        else:
            raw = evaluate(task)
            validate_raw(task, raw)
            cache["entries"][key] = raw
            raw_results[task["id"]] = raw
            save_cache(args.cache, {"entries": {key: raw}})
    if misses:
        raise RuntimeError(f"cache misses in --cached-only mode: {', '.join(misses)}")
    results = [compose_result(task, raw_results[task["id"]], weights, args.confidence_threshold) for task in tasks]
    results.sort(key=lambda result: result["ease_score"], reverse=True)
    if args.json:
        print(json.dumps({"question_version": QUESTION_VERSION, "weights": weights, "results": results}, indent=2))
    else:
        print(f"{'EASE':>6}  {'REVIEW':<6}  {'STATUS':<10}  {'READY':<5}  {'TASK ID':<24}  TASK")
        for result in results:
            review = "yes" if result["review_required"] else "no"
            ready = "yes" if result["ready_in_snapshot"] else "no"
            title = result["task_text"].splitlines()[0]
            print(f"{result['ease_score']:6.2f}  {review:<6}  {result['board_status']:<10}  {ready:<5}  {result['id']:<24}  {title}")
        print("\nHigher EASE is easier. REVIEW=yes means at least one dimension is below the confidence threshold.")
        print("READY describes the exported snapshot only. Recheck the board and test approval before work.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
