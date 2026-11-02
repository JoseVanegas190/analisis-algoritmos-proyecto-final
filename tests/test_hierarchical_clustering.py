import unittest

from src.clustering_evaluation import silhouette_score_manual
from src.hierarchical_clustering import average_linkage, clusters_at_count, complete_linkage, single_linkage


class HierarchicalClusteringTests(unittest.TestCase):
    def setUp(self):
        self.distances = [
            [0.0, 0.1, 0.9, 0.9],
            [0.1, 0.0, 0.8, 0.9],
            [0.9, 0.8, 0.0, 0.2],
            [0.9, 0.9, 0.2, 0.0],
        ]

    def test_each_linkage_first_merges_nearest_pair(self):
        for algorithm in (single_linkage, complete_linkage, average_linkage):
            history = algorithm(self.distances)
            self.assertEqual({history[0].left, history[0].right}, {0, 1})
            self.assertEqual(len(history), 3)

    def test_cut_and_silhouette(self):
        groups = clusters_at_count(average_linkage(self.distances), 4, 2)
        self.assertEqual({frozenset(group) for group in groups}, {frozenset({0, 1}), frozenset({2, 3})})
        self.assertGreater(silhouette_score_manual(self.distances, groups), 0.7)


if __name__ == "__main__":
    unittest.main()
