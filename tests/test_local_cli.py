import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from japan_real_estate_data_retriever.local_cli import resolve_browser_use_cli, run_local_debug


class LocalCliTest(unittest.TestCase):
    def test_resolve_browser_use_cli_prefers_explicit_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "browser-use"
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o755)

            with patch.dict(os.environ, {"BROWSER_USE_CLI": "/missing/browser-use"}):
                self.assertEqual(resolve_browser_use_cli(str(path)), str(path))

    def test_resolve_browser_use_cli_uses_environment_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "browser-use"
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o755)

            with patch.dict(os.environ, {"BROWSER_USE_CLI": str(path)}):
                self.assertEqual(resolve_browser_use_cli(), str(path))

    def test_run_local_debug_no_open_returns_plan_without_cloud(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "browser-use"
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(0o755)

            result = run_local_debug(
                "suumo",
                {"max_results": 1},
                browser_use_cli=str(path),
                open_browser=False,
            )

        self.assertEqual(result["mode"], "local-browser-cli")
        self.assertEqual(result["source"], "suumo")
        self.assertEqual(result["commands"], [])
        self.assertIn("browser-use CLI browser commands", result["notes"][0])


if __name__ == "__main__":
    unittest.main()
