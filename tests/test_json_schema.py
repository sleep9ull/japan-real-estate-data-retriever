import json
from pathlib import Path
import unittest

from japan_real_estate_data_retriever.normalizer import UNIFIED_LISTING_FIELDS


class JsonSchemaTest(unittest.TestCase):
    def test_root_schema_is_canonical_json_schema(self):
        schema = json.loads(Path("schemas/unified_listing.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "UnifiedJapaneseRealEstateListingResult")
        self.assertIn("items", schema["properties"])

    def test_skill_schema_copy_matches_root_schema(self):
        root = json.loads(Path("schemas/unified_listing.schema.json").read_text(encoding="utf-8"))
        skill = json.loads(
            Path("skills/japan-real-estate-data-retriever/references/unified_listing.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(root, skill)

    def test_skill_query_schema_copy_matches_root_schema(self):
        root = json.loads(Path("schemas/query.schema.json").read_text(encoding="utf-8"))
        skill = json.loads(
            Path("skills/japan-real-estate-data-retriever/references/query.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(root, skill)

    def test_normalizer_fields_match_listing_schema_required_fields(self):
        schema = json.loads(Path("schemas/unified_listing.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(tuple(schema["$defs"]["listing"]["required"]), UNIFIED_LISTING_FIELDS)


if __name__ == "__main__":
    unittest.main()
