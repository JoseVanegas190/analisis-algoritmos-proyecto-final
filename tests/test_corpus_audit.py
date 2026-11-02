import unittest

from src.corpus_audit import audit_abstract, audit_records
from src.text_processing import tokenize


class CorpusAuditTests(unittest.TestCase):
    def test_flags_short_abstract_and_filtered_marker(self):
        issues = audit_abstract("Short abstract. Keywords Artificial Intelligence")
        self.assertTrue(any("corto" in issue for issue in issues))
        self.assertTrue(any("marcador" in issue for issue in issues))

    def test_accepts_a_normal_abstract(self):
        text = "Artificial intelligence supports educational assessment and teacher development. " * 8
        self.assertEqual(audit_abstract(text), [])

    def test_tokenization_removes_common_non_contextual_words(self):
        tokens = tokenize("We were using artificial intelligence in education and have results.")
        self.assertEqual(tokens, ["artificial", "intelligence", "education", "results"])

    def test_record_summary_counts_items_to_review(self):
        result = audit_records([
            {"file_name": "correct.pdf", "abstract": "Educational artificial intelligence improves assessment. " * 10},
            {"file_name": "short.pdf", "abstract": "Too short."},
        ])
        self.assertEqual(result["valid_records"], 1)
        self.assertEqual(result["records_to_review"], 1)
