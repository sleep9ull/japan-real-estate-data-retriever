import unittest

from japan_real_estate_data_retriever.prompt_builder import build_session_payload


class PromptBuilderTest(unittest.TestCase):
    def test_build_session_payload_contains_schema_and_japan_proxy(self):
        payload = build_session_payload(
            "suumo",
            {"area": {"prefecture": "東京都"}, "max_results": 3},
            model="bu-mini",
            max_cost_usd=1.0,
        )
        self.assertEqual(payload["model"], "bu-mini")
        self.assertEqual(payload["proxyCountryCode"], "jp")
        self.assertIn("outputSchema", payload)
        self.assertIn("SUUMO", payload["task"])
        self.assertIn("Search Filter Capabilities", payload["task"])


if __name__ == "__main__":
    unittest.main()
