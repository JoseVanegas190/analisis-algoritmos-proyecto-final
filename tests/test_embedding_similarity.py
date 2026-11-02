import unittest

from src.embedding_similarity import cosine_similarity_dense


class EmbeddingSimilarityTests(unittest.TestCase):
    def test_dense_cosine_is_calculated_without_a_library(self):
        self.assertAlmostEqual(cosine_similarity_dense([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity_dense([1.0, 0.0], [0.0, 2.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
