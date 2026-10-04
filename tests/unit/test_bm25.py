"""Offline BM25 encoder."""

from __future__ import annotations

from pmo_core.adapters.bm25 import encode_document, encode_query, token_index, tokenize


def test_item_ids_stay_whole() -> None:
    """`RSK-014` is one token, so exact-ID queries match exactly."""
    assert "rsk-014" in tokenize("Mitigation for RSK-014?")
    assert "rsk" not in tokenize("Mitigation for RSK-014?")


def test_numbers_and_dates_kept() -> None:
    """Figures and dates survive tokenization; stopwords do not."""
    tokens = tokenize("The budget is $5,345,000 as of 2026-03-31.")
    assert "5,345,000" in tokens
    assert "the" not in tokens


def test_query_weights_are_one_and_sorted() -> None:
    """Query vectors weight each unique term once, with sorted indices."""
    vector = encode_query("risk risk owner")
    assert vector.values == [1.0, 1.0]
    assert vector.indices == sorted(vector.indices)


def test_document_tf_saturates() -> None:
    """Repeated terms gain weight sub-linearly."""
    once = encode_document("connector")
    many = encode_document("connector " * 10)
    index = token_index("connector")
    weight_once = dict(zip(once.indices, once.values, strict=True))[index]
    weight_many = dict(zip(many.indices, many.values, strict=True))[index]
    assert weight_once < weight_many < 10 * weight_once


def test_empty_query() -> None:
    """A query of stopwords has no terms."""
    assert encode_query("what is the").indices == []
