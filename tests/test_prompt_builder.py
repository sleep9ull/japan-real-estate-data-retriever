import unittest

from japan_real_estate_data_retriever.prompt_builder import (
    build_agent_session_payload,
    build_browser_only_execution_policy,
    build_browser_session_payload,
    build_browser_workflow_payload,
    build_local_agent_context,
    build_multi_source_browser_workflow_payload,
)


class PromptBuilderTest(unittest.TestCase):
    def test_build_agent_session_payload_contains_schema_task_and_japan_proxy(self):
        payload = build_agent_session_payload(
            "suumo",
            {"area": {"prefecture": "東京都"}, "max_results": 3},
            model="claude-sonnet-4.6",
            max_cost_usd=5.0,
            keep_alive=True,
            profile_id="3c90c3cc-0d44-4b50-8888-8dd25736052a",
            workspace_id="3c90c3cc-0d44-4b50-8888-8dd25736052b",
            enable_recording=True,
            skills=False,
            agentmail=True,
            cache_script=True,
        )
        self.assertEqual(payload["model"], "claude-sonnet-4.6")
        self.assertEqual(payload["maxCostUsd"], 5.0)
        self.assertEqual(payload["proxyCountryCode"], "jp")
        self.assertTrue(payload["keepAlive"])
        self.assertTrue(payload["enableRecording"])
        self.assertFalse(payload["skills"])
        self.assertTrue(payload["agentmail"])
        self.assertTrue(payload["cacheScript"])
        self.assertEqual(payload["profileId"], "3c90c3cc-0d44-4b50-8888-8dd25736052a")
        self.assertEqual(payload["workspaceId"], "3c90c3cc-0d44-4b50-8888-8dd25736052b")
        self.assertIn("outputSchema", payload)
        self.assertIn("SUUMO", payload["task"])
        self.assertIn("Search Filter Capabilities", payload["task"])

    def test_build_browser_session_payload_uses_standalone_cloud_browser_shape(self):
        payload = build_browser_session_payload(
            timeout_minutes=45,
            profile_id="3c90c3cc-0d44-4b50-8888-8dd25736052a",
            enable_recording=True,
            browser_screen_width=1280,
            browser_screen_height=720,
            allow_resizing=True,
        )
        self.assertEqual(payload["proxyCountryCode"], "jp")
        self.assertEqual(payload["timeout"], 45)
        self.assertEqual(payload["profileId"], "3c90c3cc-0d44-4b50-8888-8dd25736052a")
        self.assertTrue(payload["enableRecording"])
        self.assertEqual(payload["browserScreenWidth"], 1280)
        self.assertEqual(payload["browserScreenHeight"], 720)
        self.assertTrue(payload["allowResizing"])
        self.assertNotIn("task", payload)
        self.assertNotIn("model", payload)
        self.assertNotIn("outputSchema", payload)

    def test_build_browser_workflow_payload_combines_browser_and_local_workflow(self):
        payload = build_browser_workflow_payload(
            "suumo",
            {"area": {"station": "渋谷駅"}, "max_results": 10},
            timeout_minutes=30,
        )
        self.assertEqual(payload["executionMode"], "browser_only_primary")
        self.assertEqual(payload["browserPayload"]["proxyCountryCode"], "jp")
        self.assertEqual(payload["browserPayload"]["timeout"], 30)
        self.assertEqual(payload["workflow"]["source"], "suumo")
        self.assertIn("instructions", payload["workflow"])
        self.assertIn("outputSchema", payload["workflow"])
        self.assertEqual(payload["executionPolicy"]["sessionIsolation"], "one_cloud_browser_per_source")
        self.assertIn("navigate_or_reuse_loaded_page", payload["executionPolicy"]["phases"])
        self.assertIn("browserOnlyExecutionPolicy", payload["workflow"])
        self.assertNotIn("task", payload["browserPayload"])
        self.assertEqual(payload["sessionIsolation"]["strategy"], "one_cloud_browser_per_source")

    def test_build_local_agent_context_keeps_workflow_and_schema_outside_cloud_payload(self):
        context = build_local_agent_context(
            "suumo",
            {"area": {"prefecture": "東京都"}, "max_results": 3},
        )
        self.assertEqual(context["source"], "suumo")
        self.assertEqual(context["site"]["displayName"], "SUUMO")
        self.assertIn("outputSchema", context)
        self.assertEqual(context["browserOnlyExecutionPolicy"]["source"], "suumo")
        self.assertIn("TargetClosedError", " ".join(context["browserOnlyExecutionPolicy"]["retryRules"]))
        self.assertIn("SUUMO", context["instructions"])
        self.assertIn("Search Filter Capabilities", context["instructions"])

    def test_build_browser_only_execution_policy_documents_reconnect_and_cleanup(self):
        policy = build_browser_only_execution_policy("athome")
        retry_text = " ".join(policy["retryRules"])
        completion_text = " ".join(policy["completionRules"])

        self.assertEqual(policy["source"], "athome")
        self.assertEqual(policy["mode"], "browser_only_primary")
        self.assertEqual(policy["sessionIsolation"], "one_cloud_browser_per_source")
        self.assertGreaterEqual(policy["maxReconnectAttemptsPerSource"], 1)
        self.assertIn("same cdpUrl", retry_text)
        self.assertIn("loaded DOM", retry_text)
        self.assertIn("Stop every Cloud Browser session", completion_text)

    def test_build_multi_source_browser_workflow_payload_forces_per_source_sessions(self):
        payload = build_multi_source_browser_workflow_payload(
            ["suumo", "homes"],
            {"sources": ["suumo", "homes"], "max_results_per_source": 10},
            timeout_minutes=20,
        )
        self.assertEqual(payload["executionMode"], "browser_only_primary")
        self.assertEqual(payload["sessionIsolation"]["strategy"], "one_cloud_browser_per_source")
        self.assertEqual(payload["sessionIsolation"]["sources"], ["suumo", "homes"])
        self.assertEqual(payload["executionPolicy"]["sessionIsolation"], "one_cloud_browser_per_source")
        self.assertEqual(set(payload["sources"].keys()), {"suumo", "homes"})
        self.assertEqual(payload["sources"]["suumo"]["browserPayload"]["timeout"], 20)
        self.assertEqual(payload["sources"]["homes"]["browserPayload"]["timeout"], 20)
        self.assertEqual(payload["sources"]["suumo"]["executionPolicy"]["source"], "suumo")
        self.assertEqual(payload["sources"]["suumo"]["workflow"]["source"], "suumo")
        self.assertEqual(payload["sources"]["homes"]["workflow"]["source"], "homes")


if __name__ == "__main__":
    unittest.main()
