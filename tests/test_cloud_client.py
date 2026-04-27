import os
import unittest
from unittest.mock import patch

from japan_real_estate_data_retriever.cloud_client import (
    BrowserUseCloudClient,
    BrowserUseCloudError,
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

    def test_create_session_uses_agent_sessions_endpoint(self):
        client = BrowserUseCloudClient(api_key="test-key")
        response = {"id": "session-id", "status": "created"}
        with patch.object(client, "_request", return_value=response) as request:
            self.assertEqual(client.create_session({"task": "find listings"}), response)

        request.assert_called_once_with("POST", "/sessions", {"task": "find listings"})

    def test_run_task_polls_until_terminal_status(self):
        client = BrowserUseCloudClient(api_key="test-key", poll_interval=0, timeout_seconds=1)
        responses = [
            {"id": "session-id", "status": "created"},
            {"id": "session-id", "status": "running"},
            {"id": "session-id", "status": "stopped", "output": {"items": []}},
        ]
        with patch.object(client, "_request", side_effect=responses) as request:
            self.assertEqual(client.run_task({"task": "find listings"}), responses[-1])

        self.assertEqual(request.call_count, 3)

    def test_stop_session_uses_v3_stop_endpoint(self):
        client = BrowserUseCloudClient(api_key="test-key")
        response = {"id": "session-id", "status": "stopped"}
        with patch.object(client, "_request", return_value=response) as request:
            self.assertEqual(client.stop_session("session-id"), response)

        request.assert_called_once_with("POST", "/sessions/session-id/stop", {"strategy": "session"})

    def test_terminal_statuses_include_v3_completion_states(self):
        self.assertIn("idle", TERMINAL_STATUSES)
        self.assertIn("stopped", TERMINAL_STATUSES)

    def test_create_browser_uses_standalone_browsers_endpoint(self):
        client = BrowserUseCloudClient(api_key="test-key")
        response = {
            "id": "browser-id",
            "status": "active",
            "cdpUrl": "wss://example.browser/cdp",
            "liveUrl": "https://live.browser-use.com/session",
        }
        with patch.object(client, "_request", return_value=response) as request:
            self.assertEqual(client.create_browser({"proxyCountryCode": "jp"}), response)

        request.assert_called_once_with("POST", "/browsers", {"proxyCountryCode": "jp"})

    def test_create_browser_requires_cdp_url(self):
        client = BrowserUseCloudClient(api_key="test-key")
        with patch.object(client, "_request", return_value={"id": "browser-id"}):
            with self.assertRaises(BrowserUseCloudError):
                client.create_browser({"proxyCountryCode": "jp"})

    def test_stop_browser_uses_patch_stop_action(self):
        client = BrowserUseCloudClient(api_key="test-key")
        response = {"id": "browser-id", "status": "stopped"}
        with patch.object(client, "_request", return_value=response) as request:
            self.assertEqual(client.stop_browser("browser-id"), response)

        request.assert_called_once_with("PATCH", "/browsers/browser-id", {"action": "stop"})


if __name__ == "__main__":
    unittest.main()
