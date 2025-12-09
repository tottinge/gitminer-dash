import re
from collections import Counter

# Common words to exclude from analysis
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "will", "with", "this", "but", "they", "have", "had",
    "what", "when", "where", "who", "which", "why", "how", "or", "can",
    "do", "if", "not", "so", "up", "out", "then", "than", "we", "us",
    "you", "your", "their", "them", "been", "more", "all", "just", "into",
    "also", "our", "some", "were", "would", "could", "should", "may", "might"
}


def calculate_word_frequency(
    messages: list[str],
    min_word_length: int = 3,
    exclude_stop_words: bool = True
) -> dict[str, int]:
    """Calculate word frequency from commit messages.

    Args:
        messages: List of commit messages
        min_word_length: Minimum length for words to include (default 3)
        exclude_stop_words: Whether to exclude common stop words (default True)

    Returns:
        Dictionary mapping words to their frequency counts
    """
    word_counts = Counter()

    for message in messages:
        # Convert to lowercase and extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-z]+\b', message.lower())

        for word in words:
            # Filter by length
            if len(word) < min_word_length:
                continue

            # Filter stop words if enabled
            if exclude_stop_words and word in STOP_WORDS:
                continue

            word_counts[word] += 1

    return dict(word_counts)
