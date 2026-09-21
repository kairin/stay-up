"""Check task input and cached ranking without API calls."""

import contextlib
import importlib.util
import io
import json
import math
import multiprocessing
import os
import time
from fractions import Fraction
from pathlib import Path
import runpy
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("rank_tasks.py")
SPEC = importlib.util.spec_from_file_location("rank_tasks", PATH)
ranker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ranker)


def cache_writer(path, updates, ready, start, results, replace_ready=None, replace_release=None, lock_timeout=None):
    try:
        ranker.load_cache(Path(path))
        ready.set()
        if not start.wait(10):
            raise RuntimeError("Test start timed out.")
        original_replace = Path.replace

        def delayed_replace(source, target):
            replace_ready.set()
            if not replace_release.wait(10):
                raise RuntimeError("Test release timed out.")
            return original_replace(source, target)

        replacement = patch.object(Path, "replace", delayed_replace) if replace_ready else contextlib.nullcontext()
        options = {} if lock_timeout is None else {"lock_timeout": lock_timeout}
        with replacement:
            ranker.save_cache(Path(path), updates, **options)
        results.put(("ok", ""))
    except Exception as error:
        results.put((type(error).__name__, str(error)))


class RankerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.task = {"id": "task-a", "task_text": "Check a local file."}

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def raw(self):
        return {
            "task_id": self.task["id"],
            "question_version": ranker.QUESTION_VERSION,
            "evidence_fingerprint": ranker.evidence_fingerprint(self.task),
            "model": "test-fixture",
            "evaluated_at": "2026-09-20T00:00:00+00:00",
            "dimensions": {
                name: {"score": 2.0, "confidence": 0.8}
                for name in ranker.DIMENSIONS
            },
        }

    def test_duplicate_ids_fail(self):
        path = self.save("tasks.json", [self.task, self.task])
        with self.assertRaises(ValueError):
            ranker.load_tasks(path)

    def test_all_evidence_fields_change_the_cache_key(self):
        for field in ranker.FINGERPRINT_FIELDS:
            with self.subTest(field=field):
                changed = dict(self.task, **{field: "Changed evidence."})
                self.assertNotEqual(ranker.cache_key(self.task), ranker.cache_key(changed))

    def test_weights_do_not_change_raw_cache_keys(self):
        key = ranker.cache_key(self.task)
        ranker.load_weights(self.save("weights.json", {"policy_risk": 0.9}))
        self.assertEqual(key, ranker.cache_key(self.task))

    def test_score_midpoint_and_confidence_boundary(self):
        raw = self.raw()
        raw["dimensions"]["policy_risk"]["confidence"] = 0.60
        result = ranker.compose_result(self.task, raw, ranker.DEFAULT_WEIGHTS, 0.60)
        self.assertEqual(result["ease_score"], 50.0)
        self.assertFalse(result["review_required"])
        raw["dimensions"]["policy_risk"]["confidence"] = 0.59
        self.assertTrue(ranker.compose_result(self.task, raw, ranker.DEFAULT_WEIGHTS, 0.60)["review_required"])

    def test_extreme_weights_keep_finite_scores(self):
        names = list(ranker.DIMENSIONS)
        cases = [
            ([1e307, 0, 0, 0, 0, 0], [0, 2, 2, 2, 2, 2]),
            ([5e-324, 0, 0, 0, 0, 0], [2, 2, 2, 2, 2, 2]),
            ([1e307] * 6, [0, 1, 2, 3, 4, 1]),
            ([5e-324] * 6, [0, 1, 2, 3, 4, 1]),
            ([1e307, 5e-324, 3e306, 0, 2e306, 0], [0, 1, 2, 3, 4, 1]),
            ([5e-324, 1e-323, 1.5e-323, 0, 2e-323, 0], [0, 1, 2, 3, 4, 1]),
            (list(ranker.DEFAULT_WEIGHTS.values()), [0, 1, 2, 3, 4, 1]),
        ]
        key = ranker.cache_key(self.task)
        for values, scores in cases:
            with self.subTest(weights=values):
                weights = ranker.load_weights(self.save("weights.json", dict(zip(names, values))))
                raw = self.raw()
                total = Fraction(0)
                for name, score in zip(names, scores):
                    raw["dimensions"][name]["score"] = score
                    component = Fraction(score, 4)
                    if name in ranker.INVERTED_DIMENSIONS:
                        component = 1 - component
                    total += Fraction(weights[name]) * component
                expected = round(float(100 * total / sum(map(Fraction, weights.values()))), 2)
                before = json.dumps(raw, sort_keys=True)
                result = ranker.compose_result(self.task, raw, weights, 0.6)
                self.assertTrue(math.isfinite(result["ease_score"]))
                self.assertGreaterEqual(result["ease_score"], 0)
                self.assertLessEqual(result["ease_score"], 100)
                self.assertEqual(result["ease_score"], expected)
                self.assertEqual(json.dumps(raw, sort_keys=True), before)
                self.assertEqual(ranker.cache_key(self.task), key)

    def test_weights_reject_non_finite_values(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ranker.load_weights(self.save("weights.json", {"policy_risk": value}))

    def test_task_identifiers_and_text_require_nonempty_strings(self):
        for field in ("id", "task_text"):
            for value in (12, ["invalid"], "   "):
                with self.subTest(field=field, value=value):
                    task = dict(self.task, **{field: value})
                    with self.assertRaises(ValueError):
                        ranker.load_tasks(self.save("tasks.json", [task]))

    def test_bad_raw_scores_fail(self):
        for field, values in (("score", [-1, 5, float("nan")]), ("confidence", [-1, 2, float("inf")])):
            for value in values:
                with self.subTest(field=field, value=value):
                    raw = self.raw()
                    raw["dimensions"]["policy_risk"][field] = value
                    with self.assertRaises(ValueError):
                        ranker.compose_result(self.task, raw, ranker.DEFAULT_WEIGHTS, 0.6)

    def test_cache_identity_must_match(self):
        for field in ("task_id", "question_version", "evidence_fingerprint"):
            with self.subTest(field=field):
                raw = self.raw()
                raw[field] = "wrong"
                with self.assertRaises(ValueError):
                    ranker.compose_result(self.task, raw, ranker.DEFAULT_WEIGHTS, 0.6)


    def test_board_changes_invalidate_scores(self):
        blocked = dict(self.task, board_state={"board": "stay-up", "status": "blocked", "parents": []})
        ready = dict(self.task, board_state={"board": "stay-up", "status": "ready", "parents": []})
        self.assertNotEqual(ranker.cache_key(blocked), ranker.cache_key(ready))

    def test_readiness_is_independent_of_ease(self):
        for status, parent_status, expected in (
            ("blocked", "done", False), ("todo", "done", False),
            ("ready", "blocked", False), ("ready", "done", True),
            ("done", "done", False),
        ):
            with self.subTest(status=status, parent_status=parent_status):
                task = dict(self.task, board_state={"board": "stay-up", "status": status,
                    "parents": [{"id": "t_11111111", "status": parent_status}]})
                raw = self.raw()
                raw["evidence_fingerprint"] = ranker.evidence_fingerprint(task)
                result = ranker.compose_result(task, raw, ranker.DEFAULT_WEIGHTS, 0.6)
                self.assertEqual(result.get("ready_in_snapshot"), expected)

    def test_seed_data_never_claims_live_readiness(self):
        result = ranker.compose_result(self.task, self.raw(), ranker.DEFAULT_WEIGHTS, 0.6)
        self.assertIs(result.get("ready_in_snapshot"), False)


    def test_cache_only_miss_never_calls_the_api(self):
        tasks = self.save("tasks.json", [self.task])
        args = [str(PATH), str(tasks), "--cache", str(self.root / "missing.json"), "--cached-only"]
        with patch("sys.argv", args), patch.object(ranker, "evaluate") as evaluate:
            with self.assertRaisesRegex(RuntimeError, "cache misses"):
                ranker.main()
            evaluate.assert_not_called()

    def test_cache_reuse_and_weight_change_need_no_api(self):
        tasks = self.save("tasks.json", [self.task])
        cache = self.save("cache.json", {"entries": {ranker.cache_key(self.task): self.raw()}})
        weights = self.save("weights.json", {"policy_risk": 0.8})
        args = [str(PATH), str(tasks), "--cache", str(cache), "--weights", str(weights), "--cached-only", "--json"]
        output = io.StringIO()
        with patch("sys.argv", args), patch.object(ranker, "evaluate") as evaluate, contextlib.redirect_stdout(output):
            self.assertEqual(ranker.main(), 0)
            evaluate.assert_not_called()
        self.assertEqual(len(json.loads(output.getvalue())["results"]), 1)

    def start_cache_writer(self, cache, updates, **options):
        context = multiprocessing.get_context("spawn")
        ready, start = context.Event(), context.Event()
        results = context.Queue()
        process = context.Process(target=cache_writer, args=(str(cache), updates, ready, start, results), kwargs=options)

        def cleanup():
            if process.is_alive():
                process.terminate()
            process.join(10)
            results.close()
            results.join_thread()

        process.start()
        self.addCleanup(cleanup)
        self.assertTrue(ready.wait(10))
        return process, start, results

    def finish_cache_writer(self, worker):
        process, _, results = worker
        result = results.get(timeout=10)
        process.join(10)
        self.assertFalse(process.is_alive())
        self.assertEqual(process.exitcode, 0)
        return result

    def test_process_writers_merge_cache_entries(self):
        cache = self.save("cache.json", {"entries": {"old": {"value": "Keep"}}, "metadata": "Keep"})
        workers = [self.start_cache_writer(cache, {"entries": {str(index): {"value": index}}}) for index in range(4)]
        for _, start, _ in workers:
            start.set()
        for worker in workers:
            self.assertEqual(self.finish_cache_writer(worker), ("ok", ""))
        expected = {"old": {"value": "Keep"}, **{str(index): {"value": index} for index in range(4)}}
        self.assertEqual(ranker.load_cache(cache), {"entries": expected, "metadata": "Keep"})

    def test_process_lock_timeout_preserves_active_writer(self):
        cache = self.save("cache.json", {"entries": {"old": 1}})
        shared_temp = cache.with_suffix(".json.tmp")
        shared_temp.write_text("KEEP_SHARED_TEMP", encoding="utf-8")
        context = multiprocessing.get_context("spawn")
        replace_ready, replace_release = context.Event(), context.Event()
        holder = self.start_cache_writer(cache, {"entries": {"holder": 2}},
                                         replace_ready=replace_ready, replace_release=replace_release)
        holder[1].set()
        self.assertTrue(replace_ready.wait(10))
        try:
            contender = self.start_cache_writer(cache, {"entries": {"contender": 3}}, lock_timeout=0.2)
            started = time.monotonic()
            contender[1].set()
            error_type, message = self.finish_cache_writer(contender)
            self.assertEqual(error_type, "RuntimeError")
            self.assertIn("lock", message.lower())
            self.assertGreaterEqual(time.monotonic() - started, 0.15)
            self.assertLess(time.monotonic() - started, 5)
            self.assertEqual(ranker.load_cache(cache), {"entries": {"old": 1}})
            self.assertTrue(cache.with_suffix(".json.lock").exists())
            self.assertEqual(shared_temp.read_text(encoding="utf-8"), "KEEP_SHARED_TEMP")
        finally:
            replace_release.set()
        self.assertEqual(self.finish_cache_writer(holder), ("ok", ""))
        ranker.save_cache(cache, {"entries": {"after": 4}})
        self.assertEqual(ranker.load_cache(cache), {"entries": {"old": 1, "holder": 2, "after": 4}})
        self.assertTrue(cache.with_suffix(".json.lock").exists())
        self.assertEqual(list(self.root.glob("cache.json.*.tmp")), [])

    def test_main_saves_only_new_entries_from_a_stale_cache(self):
        tasks = self.save("tasks.json", [self.task, dict(self.task, id="task-b")])
        key = ranker.cache_key(self.task)
        cache = self.save("cache.json", {"entries": {key: self.raw()}})
        newer = dict(self.raw(), model="newer-fixture")

        def evaluate(task):
            worker = self.start_cache_writer(cache, {"entries": {key: newer}})
            worker[1].set()
            self.assertEqual(self.finish_cache_writer(worker), ("ok", ""))
            return dict(self.raw(), task_id=task["id"])

        args = [str(PATH), str(tasks), "--cache", str(cache), "--json"]
        with patch("sys.argv", args), patch.object(ranker, "evaluate", side_effect=evaluate), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ranker.main(), 0)
        final = ranker.load_cache(cache)["entries"]
        self.assertEqual(final[key], newer)
        self.assertIn(ranker.cache_key(dict(self.task, id="task-b")), final)

    def test_failed_cache_replace_preserves_old_file(self):
        cache = self.save("cache.json", {"entries": {"old": 1}})
        with patch.object(Path, "replace", side_effect=OSError("TEST_REPLACE_FAILURE")):
            with self.assertRaises(OSError):
                ranker.save_cache(cache, {"entries": {"new": 2}})
        self.assertEqual(ranker.load_cache(cache), {"entries": {"old": 1}})
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def response(self):
        return SimpleNamespace(model="test-fixture", scores={
            name: SimpleNamespace(
                score=2.0, confidence=0.8,
                probabilities={str(index): 0.2 for index in range(5)},
                legend={str(index): text for index, text in enumerate(definition["criteria"])},
            ) for name, definition in ranker.DIMENSIONS.items()
        })

    def malformed_responses(self):
        for field in ("scores", "model"):
            response = self.response()
            delattr(response, field)
            yield "missing_" + field, response
        for scores in ({}, None, "TEST_SECRET_MARKER"):
            yield "bad_scores", SimpleNamespace(model="test-fixture", scores=scores)
        for field in ("score", "confidence", "probabilities", "legend"):
            response = self.response()
            delattr(response.scores["policy_risk"], field)
            yield "missing_" + field, response
        for field, values in (
            ("score", [True, "TEST_SECRET_MARKER", None, -1, 5, float("nan"), float("inf"), 10 ** 400]),
            ("confidence", [False, "TEST_SECRET_MARKER", None, -1, 2, float("nan"), float("inf")]),
            ("probabilities", [None, [], {"0": "TEST_SECRET_MARKER"}, {"0": True}, {"0": -0.1}, {"0": 2},
                               {"0": float("nan")}, {"0": float("inf")}]),
            ("legend", [None, "TEST_SECRET_MARKER", {"0": object()}]),
        ):
            for value in values:
                response = self.response()
                setattr(response.scores["policy_risk"], field, value)
                yield "bad_" + field, response
        response = self.response()
        response.model = object()
        yield "bad_model", response

        class BrokenScores(dict):
            def __getitem__(self, key):
                raise KeyError("TEST_SECRET_MARKER")

        response = self.response()
        response.scores = BrokenScores(response.scores)
        yield "answer_read_error", response

    def fake_sdk(self, response):
        sdk = ModuleType("typesafe_sdk")
        sdk.Score = lambda **kwargs: kwargs
        sdk.TypeSafeClient = lambda: contextlib.nullcontext(SimpleNamespace(system_one=lambda **kwargs: response))
        return sdk

    def test_malformed_responses_raise_safe_runtime_errors(self):
        for label, response in self.malformed_responses():
            with self.subTest(case=label):
                sdk = self.fake_sdk(response)
                with patch.dict(os.environ, {"TYPESAFE_API_KEY": "TEST_ONLY"}), patch.object(
                    ranker, "import_sdk", return_value=(sdk.Score, sdk.TypeSafeClient)
                ):
                    with self.assertRaises(RuntimeError) as caught:
                        ranker.evaluate(self.task)
                self.assertNotIn("TEST_SECRET_MARKER", str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)

    def test_malformed_responses_leave_cache_unchanged_at_cli(self):
        tasks = self.save("tasks.json", [self.task])
        cache = self.save("cache.json", {"entries": {"old": {"value": "Keep"}}})
        before = cache.read_bytes()
        args = [str(PATH), str(tasks), "--cache", str(cache), "--json"]
        for label, response in self.malformed_responses():
            with self.subTest(case=label):
                cache.write_bytes(before)
                output, errors = io.StringIO(), io.StringIO()
                with patch("sys.argv", args), patch.dict(os.environ, {"TYPESAFE_API_KEY": "TEST_ONLY"}), patch.dict(
                    "sys.modules", {"typesafe_sdk": self.fake_sdk(response)}
                ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    with self.assertRaises(SystemExit) as caught:
                        runpy.run_path(str(PATH), run_name="__main__")
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(output.getvalue(), "")
                self.assertNotIn("TEST_SECRET_MARKER", errors.getvalue())
                self.assertNotIn("Traceback", errors.getvalue())
                self.assertEqual(cache.read_bytes(), before)

    def test_valid_response_preserves_raw_data(self):
        response = self.response()
        sdk = self.fake_sdk(response)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "TEST_ONLY"}), patch.object(
            ranker, "import_sdk", return_value=(sdk.Score, sdk.TypeSafeClient)
        ):
            raw = ranker.evaluate(self.task)
        ranker.validate_raw(self.task, raw)
        self.assertEqual(raw["model"], response.model)
        self.assertEqual(raw["dimensions"]["policy_risk"], vars(response.scores["policy_risk"]))

    def test_sdk_integer_rubric_keys_are_valid(self):
        response = self.response()
        for answer in response.scores.values():
            answer.probabilities = {int(key): value for key, value in answer.probabilities.items()}
            answer.legend = {int(key): value for key, value in answer.legend.items()}
        sdk = self.fake_sdk(response)
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "TEST_ONLY"}), patch.object(
            ranker, "import_sdk", return_value=(sdk.Score, sdk.TypeSafeClient)
        ):
            raw = ranker.evaluate(self.task)
        self.assertEqual(raw["dimensions"]["policy_risk"]["probabilities"], response.scores["policy_risk"].probabilities)

    def test_api_errors_do_not_echo_credentials(self):
        def client():
            raise RuntimeError("TEST_SECRET_MARKER")
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "TEST_ONLY"}), patch.object(ranker, "import_sdk", return_value=(lambda **kw: kw, client)):
            with self.assertRaises(RuntimeError) as caught:
                ranker.evaluate(self.task)
        self.assertNotIn("TEST_SECRET_MARKER", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
