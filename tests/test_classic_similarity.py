import unittest

from src.classic_similarity import (
    build_tfidf_vectors,
    cosine_similarity_sparse,
    jaccard_similarity,
    levenshtein_distance,
    needleman_wunsch_similarity,
)


class ClassicSimilarityTests(unittest.TestCase):
    def test_levenshtein_builds_expected_token_matrix(self):
        distance, matrix = levenshtein_distance(["ai", "education"], ["ai", "research"])
        self.assertEqual(distance, 1)
        self.assertEqual(matrix[-1][-1], 1)

    def test_jaccard_uses_intersection_over_union(self):
        result = jaccard_similarity("AI in education", "AI research in education")
        self.assertAlmostEqual(result["score"], 2 / 3)

    def test_needleman_identical_text_has_full_similarity(self):
        result = needleman_wunsch_similarity("AI supports education", "AI supports education")
        self.assertEqual(result["score"], 1.0)

    def test_tfidf_vectors_and_cosine(self):
        vectors, _ = build_tfidf_vectors(["ai education", "ai education", "research"])
        self.assertAlmostEqual(cosine_similarity_sparse(vectors[0], vectors[1]), 1.0)
        self.assertEqual(cosine_similarity_sparse(vectors[0], vectors[2]), 0.0)


if __name__ == "__main__":
    unittest.main()
