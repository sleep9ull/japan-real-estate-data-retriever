import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

from japan_real_estate_data_retriever.cli import main


class CliTest(unittest.TestCase):
    def test_json_doctor_reports_setup_without_network(self):
        code, output = _run_cli("--json", "doctor")
        payload = json.loads(output)

        self.assertEqual(code, 0)
        self.assertEqual(payload["tool"], "jreretrieve")
        self.assertFalse(payload["network"]["checked"])
        self.assertIn("auth", payload)

    def test_sources_resolve_alias(self):
        code, output = _run_cli("--json", "sources", "resolve", "lifull")
        payload = json.loads(output)

        self.assertEqual(code, 0)
        self.assertEqual(payload["source"], "homes")

    def test_schema_validate_query_file(self):
        with tempfile.TemporaryDirectory() as directory:
            query_path = Path(directory) / "query.json"
            query_path.write_text(json.dumps({"sources": ["suumo"], "max_results": 1}), encoding="utf-8")

            code, output = _run_cli("--json", "schema", "validate", "--name", "query", "--file", str(query_path))

        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_schema_validate_reports_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            query_path = Path(directory) / "query.json"
            query_path.write_text(json.dumps({"sources": ["missing-source"]}), encoding="utf-8")

            code, output = _run_cli("--json", "schema", "validate", "--name", "query", "--file", str(query_path))

        payload = json.loads(output)
        self.assertEqual(code, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["errors"])

    def test_workflow_show_json_uses_optional_empty_query(self):
        code, output = _run_cli("--json", "workflow", "show", "--site", "suumo")
        payload = json.loads(output)

        self.assertEqual(code, 0)
        self.assertEqual(payload["source"], "suumo")
        self.assertEqual(payload["query"], {})
        self.assertIn("instructions", payload)


def _run_cli(*args):
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(list(args))
    return code, stdout.getvalue()


if __name__ == "__main__":
    unittest.main()
