import os
import unittest
from unittest.mock import patch

from japan_real_estate_data_retriever.cloud_client import (
    BrowserUseCloudClient,
    TERMINAL_STATUSES,
    _load_api_key,
    _normalize_backend,
)


class CloudClientTest(unittest.TestCase):
    def test_load_api_key_prefers_environment(self):
        with patch.dict(os.environ, {"BROWSER_USE_API_KEY": "from-env"}):
            self.assertEqual(_load_api_key(), "from-env")

    def test_default_cloud_backend_uses_rest_api(self):
        with patch.dict(os.environ, {"BROWSER_USE_API_KEY": "from-env"}):
            self.assertEqual(BrowserUseCloudClient().backend, "rest")

    def test_cloud_backend_alias_uses_rest_api(self):
        with patch.dict(os.environ, {"BROWSER_USE_API_KEY": "from-env"}):
            self.assertEqual(BrowserUseCloudClient(backend="cloud").backend, "rest")

    def test_normalize_backend_rejects_unknown_backend(self):
        with self.assertRaises(ValueError):
            _normalize_backend("local")

    def test_terminal_statuses_include_v3_idle_completion_state(self):
        self.assertIn("idle", TERMINAL_STATUSES)


if __name__ == "__main__":
    unittest.main()
