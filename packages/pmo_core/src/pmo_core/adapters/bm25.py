"""Offline BM25 sparse encoder for the keyword leg.

Documents get BM25 term-frequency weights; queries get weight 1 per unique term; the index applies IDF
(Qdrant `Modifier.IDF`). Item IDs such as `RSK-014` stay single tokens so exact-ID queries match exactly.
"""

from __future__ import annotations

import re
import zlib
from collections import Counter
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[a-z]{2,4}-\d{2,4}|[a-z0-9]+(?:[.,][0-9]+)*")
K1 = 1.2
B = 0.75
AVG_DOC_TOKENS = 120.0
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "will",
        "with",
        "what",
        "which",
        "who",
        "whom",
        "when",
        "where",
        "why",
        "how",
        "do",
        "does",
        "did",
        "not",
        "no",
        "yes",
        "than",
        "then",
        "there",
        "these",
        "those",
    ]
)


@dataclass(frozen=True)
class SparseVector:
    """Index/value pairs for a sparse vector."""

    indices: list[int]
    values: list[float]


def tokenize(text: str) -> list[str]:
    """Lowercase tokens; item IDs and dates/numbers are kept whole; stopwords dropped."""
    return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS]


def token_index(token: str) -> int:
    """Stable 31-bit index for a token."""
    return zlib.crc32(token.encode("utf-8")) & 0x7FFFFFFF


def _to_sparse(weights: dict[int, float]) -> SparseVector:
    """Sort by index for a canonical representation."""
    ordered = sorted(weights.items())
    return SparseVector([index for index, _ in ordered], [value for _, value in ordered])


def encode_document(text: str) -> SparseVector:
    """BM25 document-side weights (without IDF)."""
    tokens = tokenize(text)
    length_norm = 1 - B + B * len(tokens) / AVG_DOC_TOKENS
    weights: dict[int, float] = {}
    for token, frequency in Counter(tokens).items():
        index = token_index(token)
        weights[index] = weights.get(index, 0.0) + frequency * (K1 + 1) / (frequency + K1 * length_norm)
    return _to_sparse(weights)


def encode_query(text: str) -> SparseVector:
    """Weight 1 for each unique query term."""
    return _to_sparse({token_index(token): 1.0 for token in set(tokenize(text))})
