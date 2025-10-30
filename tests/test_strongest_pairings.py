import unittest
from unittest.mock import patch
from box import Box


def commit_with(*files):
    return Box({"stats": {"files": files}})


def parse_record(result):
    affinity_calculated = float(result["Affinity"])
    files = result["Pairing"].split()
    return (affinity_calculated, files)


class MyTestCase(unittest.TestCase):

    def setUp(self):
        with patch("dash.register_page"):
            from pages.strongest_pairings import create_affinity_list

            self.create_affinity_list = create_affinity_list

    def test_empty_inputs(self):
        self.assertEqual([], self.create_affinity_list([]))

    def test_single_pairing(self):
        result = self.create_affinity_list([commit_with("a", "b")])
        self.assertEqual(1, len(result))
        (affinity_calculated, files) = parse_record(result[0])
        self.assertEqual(0.5, affinity_calculated)
        self.assertSequenceEqual(files, ["a", "b"])

    def test_one_common_two_leaf_nodes(self):
        result = self.create_affinity_list(
            [commit_with("a", "b"), commit_with("a", "c")]
        )
        self.assertEqual(2, len(result))
        for record in result:
            with self.subTest(record):
                (affinity_calculated, files) = parse_record(record)
                self.assertEqual(affinity_calculated, 0.5)
                self.assertIn("a", files)

    def test_with_three_files_per_commit(self):
        result = self.create_affinity_list(
            [
                commit_with("a", "b", "c"),
                commit_with("a", "d", "e"),
                commit_with("a", "f", "g"),
            ]
        )
        self.assertEqual(9, len(result))


if __name__ == "__main__":
    unittest.main()
