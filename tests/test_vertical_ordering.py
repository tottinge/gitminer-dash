import unittest

from algorithms.stacking import SequenceStacker


class MyTestCase(unittest.TestCase):

    def test_first_sequence_returns_1(self):
        stacker = SequenceStacker()
        x = stacker.height_for([1, 2])
        self.assertEqual(x, 1)

    def test_non_overlapping_sequence_returns_1(self):
        stacker = SequenceStacker()
        stacker.height_for([1, 5])
        x = stacker.height_for([7, 10])
        self.assertEqual(x, 1)

    def test_repeated_sequence_returns_2(self):
        stacker = SequenceStacker()
        stacker.height_for([1, 5])
        x = stacker.height_for([1, 5])
        self.assertEqual(x, 2)

    def test_first_overlap_returns_2(self):
        stacker = SequenceStacker()
        stacker.height_for([1, 5])
        x = stacker.height_for([2, 3])
        self.assertEqual(x, 2)

    def repeated_overlaps(self):
        test_cases = [
            ([1, 5], 1),
            ([6, 10], 1),
            ((4, 12), 2),
            ([13, 15], 1),
            ([18, 20], 1),
            ([1, 20], 3),
            ([2, 10], 4),
        ]
        stacked_graph = SequenceStacker()
        for sequence, expected in test_cases:
            self.assertEqual(expected, stacked_graph.height_for(sequence))

    def reversed_sequence_should_be_the_same(self):
        stacked_graph = SequenceStacker()
        disorderly = [
            ([18, 20], 1),
            ((4, 12), 1),
            ([6, 10], 2),
            ([13, 15], 1),
            ([1, 20], 3),
            ([1, 5], 1),
            ([2, 10], 4),
        ]
        for sequence, expected in disorderly:
            self.assertEqual(expected, stacked_graph.height_for(sequence))


if __name__ == "__main__":
    unittest.main()
