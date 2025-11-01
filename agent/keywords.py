"""
TicketGlass Agent - Sentiment Keywords & Constants

Centralized repository for:
- Sentiment detection keywords
- Heuristic thresholds
- Configuration constants

Enables easy iteration on sentiment detection without changing agent logic.
"""

from typing import Set, Dict, List
from enum import Enum


# ============================================================================
# SENTIMENT KEYWORDS
# ============================================================================

# Frustrated/angry indicators
FRUSTRATED_KEYWORDS: Set[str] = {
    "frustrat",
    "angry",
    "mad",
    "upset",
    "ugh",
    "argh",
    "annoyed",
    "tired",
    "exasperat",
    "fed up",
    "enough",
    "seriously",
    "ridiculous",
    "unbelievable",
    "impossible",
    "broken",
    "doesn't work",
    "still not working",
    "been trying all",
}

# Satisfied/happy indicators
SATISFIED_KEYWORDS: Set[str] = {
    "thanks",
    "thank you",
    "awesome",
    "great",
    "excellent",
    "perfect",
    "worked",
    "fixed",
    "solved",
    "finally",
    "yes",
    "yay",
    "fantastic",
    "amazing",
    "appreciated",
    "helpful",
    "exactly",
}

# Confused/unclear indicators
CONFUSED_KEYWORDS: Set[str] = {
    "confus",
    "don't understand",
    "what",
    "huh",
    "mean",
    "unclear",
    "lost",
    "explain",
    "again",
    "sorry",
    "confused",
    "not sure",
    "didn't catch",
    "lost you",
    "slow down",
}

# Sentiment keyword mapping
SENTIMENT_KEYWORDS_MAP: Dict[str, Set[str]] = {
    "frustrated": FRUSTRATED_KEYWORDS,
    "satisfied": SATISFIED_KEYWORDS,
    "confused": CONFUSED_KEYWORDS,
}


# ============================================================================
# HEURISTIC THRESHOLDS & CONSTANTS
# ============================================================================

class HeuristicThresholds:
    """Configuration for sentiment and repetition detection heuristics."""

    # Sentiment detection
    # Minimum word overlap ratio to count as high sentiment match
    SENTIMENT_MATCH_THRESHOLD: float = 0.1

    # Repetition detection
    # Keyword overlap ratio above this = likely repetition
    REPETITION_OVERLAP_THRESHOLD: float = 0.6

    # Context history
    # Maximum number of context entries to keep (before truncation)
    CONTEXT_HISTORY_MAX_SIZE: int = 20
    # Size to truncate to if exceeded
    CONTEXT_HISTORY_TRUNCATE_TO: int = 15

    # Token limits
    # Max tokens for Bedrock inference response
    CLAUDE_MAX_TOKENS: int = 1024
    # Max context history size to avoid token bloat
    MAX_CONTEXT_SIZE_CHARS: int = 5000

    # Output validation
    # Max length for agent summary (chars)
    SUMMARY_MAX_LENGTH: int = 500
    # Min length for summary (must have content)
    SUMMARY_MIN_LENGTH: int = 1
    # Max length for reasoning note
    REASONING_MAX_LENGTH: int = 300
    # Max length for next step
    NEXT_STEP_MAX_LENGTH: int = 300
    # Max length for learning tip
    LEARNING_TIP_MAX_LENGTH: int = 250


# ============================================================================
# SENTIMENT DETECTION KEYWORDS (By Category)
# ============================================================================

class SentimentKeywordCategory:
    """Organized sentiment keywords by category for easy updates."""

    # Negative/Frustrated
    NEGATIVE_INTENSITY = {
        "level_1": {"annoyed", "slightly", "hmm"},
        "level_2": {"frustrated", "upset", "confused"},
        "level_3": {"angry", "furious", "enraged"},
    }

    # Positive/Satisfied
    POSITIVE_INTENSITY = {
        "level_1": {"ok", "fine", "good"},
        "level_2": {"great", "awesome", "thanks"},
        "level_3": {"fantastic", "amazing", "brilliant"},
    }

    # Neutral/Seeking Clarification
    NEUTRAL_INTENT = {
        "clarification": {"what", "how", "explain", "mean"},
        "confirmation": {"correct", "right", "yes", "sure"},
        "repetition": {"again", "one more time", "repeat"},
    }


# ============================================================================
# UTILITY FUNCTIONS FOR KEYWORD MANAGEMENT
# ============================================================================


def get_sentiment_keywords(sentiment: str) -> Set[str]:
    """
    Get keyword set for a specific sentiment.

    Args:
        sentiment: Sentiment category (frustrated, satisfied, confused)

    Returns:
        Set of keywords for that sentiment

    Raises:
        ValueError: If sentiment not recognized

    Example:
        >>> keywords = get_sentiment_keywords("frustrated")
        >>> "angry" in keywords
        True
    """
    if sentiment not in SENTIMENT_KEYWORDS_MAP:
        raise ValueError(
            f"Unknown sentiment: {sentiment}. "
            f"Available: {list(SENTIMENT_KEYWORDS_MAP.keys())}"
        )
    return SENTIMENT_KEYWORDS_MAP[sentiment]


def add_sentiment_keyword(sentiment: str, keyword: str) -> None:
    """
    Add a keyword to a sentiment category (for runtime tuning).

    Args:
        sentiment: Sentiment category
        keyword: Keyword to add

    Raises:
        ValueError: If sentiment not recognized

    Example:
        >>> add_sentiment_keyword("frustrated", "annoying")
    """
    if sentiment not in SENTIMENT_KEYWORDS_MAP:
        raise ValueError(f"Unknown sentiment: {sentiment}")
    SENTIMENT_KEYWORDS_MAP[sentiment].add(keyword.lower())


def remove_sentiment_keyword(sentiment: str, keyword: str) -> None:
    """
    Remove a keyword from a sentiment category.

    Args:
        sentiment: Sentiment category
        keyword: Keyword to remove

    Raises:
        ValueError: If sentiment not recognized
    """
    if sentiment not in SENTIMENT_KEYWORDS_MAP:
        raise ValueError(f"Unknown sentiment: {sentiment}")
    SENTIMENT_KEYWORDS_MAP[sentiment].discard(keyword.lower())


def get_all_sentiment_keywords() -> Set[str]:
    """
    Get all keywords across all sentiments.

    Useful for validation or logging.

    Returns:
        Set of all sentiment keywords
    """
    all_keywords = set()
    for keywords in SENTIMENT_KEYWORDS_MAP.values():
        all_keywords.update(keywords)
    return all_keywords


if __name__ == "__main__":
    # Example usage
    print("Sentiment Keywords Loaded:")
    for sentiment, keywords in SENTIMENT_KEYWORDS_MAP.items():
        print(f"  {sentiment}: {len(keywords)} keywords")

    print("\nHeuristic Thresholds:")
    for attr in dir(HeuristicThresholds):
        if not attr.startswith("_"):
            val = getattr(HeuristicThresholds, attr)
            if not callable(val):
                print(f"  {attr}: {val}")