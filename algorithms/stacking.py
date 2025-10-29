from collections import defaultdict


def is_disjoint(seq1, seq2):
    return seq1[0] > seq2[1] or seq2[0] > seq1[1]


class SequenceStacker:
    def __init__(self):
        self.level_assignments = defaultdict(list)

    def height_for(self, sequence):
        assignment = 1
        for level, neighbors in sorted(self.level_assignments.items()):
            neighbors = self.level_assignments[level]
            if all(is_disjoint(sequence, existing) for existing in neighbors):
                assignment = level
                break
            assignment = level + 1
        self.level_assignments[assignment].append(sequence)
        return assignment
