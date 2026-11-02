import json
import tempfile
import unittest
from pathlib import Path

from src.requirement_one import compare_selected_articles


class RequirementOneTests(unittest.TestCase):
    def test_three_selected_articles_produce_three_pairwise_comparisons(self):
        records = [
            {"title": "A", "abstract": "artificial intelligence education"},
            {"title": "B", "abstract": "artificial intelligence research"},
            {"title": "C", "abstract": "education research"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "abstracts.json"
            source.write_text(json.dumps(records), encoding="utf-8")
            results = compare_selected_articles(source, ["0", "1", "2"], include_embeddings=False)
        self.assertEqual(len(results), 3)
        self.assertTrue(all("classic" in result for result in results))


if __name__ == "__main__":
    unittest.main()
