import unittest

from japan_real_estate_data_retriever.normalizer import (
    canonical_listing_id,
    canonical_url,
    normalize_listing,
)


class NormalizerTest(unittest.TestCase):
    def test_canonical_listing_id_prefers_source_listing_id(self):
        self.assertEqual(
            canonical_listing_id("suumo", source_listing_id=" 12345 "),
            "suumo:12345",
        )

    def test_canonical_listing_id_uses_source_url_hash(self):
        listing_id = canonical_listing_id(
            "athome",
            source_url="https://www.athome.co.jp/mansion/abc/#detail",
        )
        self.assertTrue(listing_id.startswith("athome:url:"))
        self.assertEqual(len(listing_id), len("athome:url:") + 16)

    def test_canonical_url_removes_fragment_and_normalizes_host(self):
        self.assertEqual(
            canonical_url("HTTPS://Example.COM/path/#section"),
            "https://example.com/path",
        )

    def test_normalize_listing_preserves_raw_and_sets_source_display_name(self):
        listing = normalize_listing(
            "homes",
            {
                "source_listing_id": "B001",
                "source_url": "https://www.homes.co.jp/mansion/b-001/",
                "title": "サンプルマンション",
            },
        )
        self.assertEqual(listing["id"], "homes:B001")
        self.assertEqual(listing["source_site_name"], "LIFULL HOME'S")
        self.assertEqual(listing["raw"]["title"], "サンプルマンション")


if __name__ == "__main__":
    unittest.main()

