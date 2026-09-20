"""Check the local Kanban export with explicit test fixtures."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("export_kanban.py")


class ExportTests(unittest.TestCase):
    def module(self):
        self.assertTrue(PATH.is_file(), "The read-only Kanban exporter is missing.")
        spec = importlib.util.spec_from_file_location("export_kanban", PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_export_retains_status_and_parent_constraints(self):
        exporter = self.module()
        details = [
            {"task": {"id": "t_11111111", "title": "Gate", "body": "## Current state\nChecks remain open.", "status": "blocked"}, "parents": [], "children": ["t_22222222"]},
            {"task": {"id": "t_22222222", "title": "Build", "body": "## Acceptance\nRun tests.", "status": "todo"}, "parents": ["t_11111111"], "children": []},
        ]
        result = exporter.build_export("stay-up", details)
        self.assertEqual(len(result["tasks"]), 2)
        child = result["tasks"][1]
        self.assertEqual(child["id"], "t_22222222")
        self.assertEqual(child["board_state"]["status"], "todo")
        self.assertEqual(child["board_state"]["parents"], [{"id": "t_11111111", "status": "blocked"}])
        self.assertIn("Run tests.", child["expected_validation"][0])
        self.assertNotIn("comments", child)


    def test_missing_parent_fails(self):
        exporter = self.module()
        details = [{"task": {"id": "t_11111111", "title": "Child", "body": "", "status": "todo"},
                    "parents": ["t_22222222"], "children": []}]
        with self.assertRaises(ValueError):
            exporter.build_export("stay-up", details)

    def test_export_time_does_not_become_evidence_time(self):
        exporter = self.module()
        detail = {"task": {"id": "t_11111111", "title": "Task", "body": "", "status": "blocked"},
                  "parents": [], "children": [], "comments": [{"body": "TEST_PRIVATE_COMMENT"}]}
        result = exporter.build_export("stay-up", [detail])
        self.assertEqual(result["tasks"][0]["evidence_timestamps"], [])
        self.assertNotIn("TEST_PRIVATE_COMMENT", str(result))

    def test_status_change_during_export_fails(self):
        exporter = self.module()
        first = {"task": {"id": "t_11111111", "title": "Task", "body": "", "status": "blocked"},
                 "parents": [], "children": []}
        second = {"task": dict(first["task"], status="ready"), "parents": [], "children": []}
        with patch.object(exporter, "read_board", side_effect=[[first["task"]], first, second, [second["task"]]]) as read:
            with self.assertRaises(RuntimeError):
                exporter.export_board("stay-up")
        self.assertTrue(all(call.args[0] == "stay-up" for call in read.call_args_list))
        self.assertTrue(all(call.args[1] in {"list", "show"} for call in read.call_args_list))

    def test_final_list_field_changes_fail_before_output_write(self):
        exporter = self.module()
        detail = {"task": {"id": "t_11111111", "title": "Task", "body": "", "status": "ready"},
                  "parents": [], "children": []}
        for field, value in (("status", "blocked"), ("title", "Changed task"), ("body", "Run tests.")):
            with self.subTest(field=field), tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
                output = Path(directory) / "export.json"
                output.write_text("KEEP_EXISTING_EXPORT", encoding="utf-8")
                final = dict(detail["task"], **{field: value})
                replies = [[detail["task"]], detail, detail, [final]]
                args = [str(PATH), "--board", "stay-up", "--output", str(output)]
                with patch("sys.argv", args), patch.object(exporter, "read_board", side_effect=replies):
                    with self.assertRaisesRegex(RuntimeError, "Board content changed"):
                        exporter.main()
                self.assertEqual(output.read_text(encoding="utf-8"), "KEEP_EXISTING_EXPORT")
                self.assertFalse(output.with_suffix(".json.tmp").exists())

    def test_parent_change_during_export_fails(self):
        exporter = self.module()
        parent = {"task": {"id": "t_11111111", "title": "Parent", "body": "", "status": "blocked"},
                  "parents": [], "children": []}
        child = {"task": {"id": "t_22222222", "title": "Child", "body": "", "status": "ready"},
                 "parents": [], "children": []}
        changed = dict(child, parents=[parent["task"]["id"]])
        listing = [child["task"], parent["task"]]
        replies = [listing, child, parent, changed, parent, list(reversed(listing))]
        with patch.object(exporter, "read_board", side_effect=replies):
            with self.assertRaisesRegex(RuntimeError, "Board content changed"):
                exporter.export_board("stay-up")

    def test_unchanged_final_list_allows_export(self):
        exporter = self.module()
        detail = {"task": {"id": "t_11111111", "title": "Task", "body": "", "status": "ready"},
                  "parents": [], "children": []}
        replies = [[detail["task"]], detail, detail, [dict(detail["task"], updated_at="Later")]]
        with patch.object(exporter, "read_board", side_effect=replies):
            result = exporter.export_board("stay-up")
        self.assertEqual(result["tasks"][0]["board_state"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
