"""
VADER-based sentiment analysis for call transcripts.

Uses NLTK's VADER (Valence Aware Dictionary and sEntiment Reasoner),
a lexicon trained on 7500+ human-rated items for conversational text.
Replaces Claude-generated sentiment with deterministic, data-driven scores.
"""

import logging

import nltk

logger = logging.getLogger(__name__)

_analyzer = None


def _get_analyzer():
    """Lazy-init VADER analyzer — downloads lexicon only on first actual use."""
    global _analyzer
    if _analyzer is None:
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            logger.info("VADER lexicon not found locally — downloading (should be pre-installed via Procfile)")
            nltk.download("vader_lexicon", quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def analyze_sentiment(text: str | None) -> dict:
    """
    Analyze sentiment of text using VADER.

    Returns:
        {"sentiment": "positive"|"neutral"|"negative"|"mixed",
         "sentiment_score": float between 0.0 and 1.0}
    """
    if not text or not text.strip():
        return {"sentiment": "neutral", "sentiment_score": 0.5}

    # VADER works best on shorter text; for long transcripts, analyze in chunks
    # and average the scores for more stable results
    chunks = _split_text(text, max_chars=4000)
    analyzer = _get_analyzer()
    scores_list = [analyzer.polarity_scores(chunk) for chunk in chunks]

    # Average the scores across chunks
    avg_compound = sum(s["compound"] for s in scores_list) / len(scores_list)
    avg_pos = sum(s["pos"] for s in scores_list) / len(scores_list)
    avg_neg = sum(s["neg"] for s in scores_list) / len(scores_list)

    # Classify sentiment
    if avg_pos > 0.2 and avg_neg > 0.2:
        sentiment = "mixed"
    elif avg_compound >= 0.05:
        sentiment = "positive"
    elif avg_compound <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Normalize compound from [-1, 1] to [0, 1]
    sentiment_score = round((avg_compound + 1) / 2, 4)

    return {"sentiment": sentiment, "sentiment_score": sentiment_score}


def _split_text(text: str, max_chars: int = 4000) -> list[str]:
    """Split text into chunks on sentence boundaries for accurate VADER scoring."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    # Split on sentence-ending punctuation followed by whitespace
    for sentence in text.replace("\n", " ").split(". "):
        candidate = (current + ". " + sentence) if current else sentence
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]
