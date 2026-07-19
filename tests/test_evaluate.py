"""
Unit tests for evaluate.py's response parsing and context formatting.

These are pure/offline: they exercise the JSON-schema handling and source
formatting WITHOUT calling Ollama, so they run fast and deterministically
(no local model required). The "does evaluate return a valid schema?" roadmap
check is covered by asserting parse_response always yields every expected key.
"""

import json

import pytest

from evaluate import parse_response, format_context, EXPECTED_KEYS


def test_parse_response_clean_json_has_all_expected_keys():
    raw = json.dumps({
        "verdict": "Correct",
        "score": 5,
        "explanation": "Solid answer.",
        "model_answer": "A deadlock is ...",
        "follow_up_question": "What breaks circular wait?",
    })
    result = parse_response(raw)
    for key in EXPECTED_KEYS:
        assert key in result
    assert result["verdict"] == "Correct"
    assert result["score"] == 5


def test_parse_response_coerces_string_score_to_int():
    raw = json.dumps({"verdict": "Partially Correct", "score": "3"})
    result = parse_response(raw)
    assert result["score"] == 3
    assert isinstance(result["score"], int)


def test_parse_response_fills_missing_keys_with_none():
    # Model omitted most fields - parser must still return the full schema.
    raw = json.dumps({"verdict": "Incorrect"})
    result = parse_response(raw)
    for key in EXPECTED_KEYS:
        assert key in result
    assert result["model_answer"] is None
    assert result["follow_up_question"] is None


def test_parse_response_strips_think_block():
    # qwen3 can prepend a <think>...</think> block; it must be ignored.
    raw = "<think>let me reason about this</think>" + json.dumps(
        {"verdict": "Correct", "score": 4}
    )
    result = parse_response(raw)
    assert result["verdict"] == "Correct"
    assert result["score"] == 4


def test_parse_response_extracts_json_wrapped_in_prose():
    raw = 'Here is the grade:\n{"verdict": "Correct", "score": 5}\nHope that helps!'
    result = parse_response(raw)
    assert result["verdict"] == "Correct"


def test_parse_response_raises_when_no_json():
    with pytest.raises(ValueError):
        parse_response("no json object anywhere here")


def test_format_context_includes_page_for_paginated_chunk():
    chunks = [{"text": "an OS passage", "chapter_name": "Deadlocks", "page_number": 383}]
    ctx = format_context(chunks)
    assert "Deadlocks" in ctx
    assert "page 383" in ctx
    assert "an OS passage" in ctx


def test_format_context_omits_page_for_sectioned_chunk():
    # DSA chunks have no page_number - the source label should be name-only.
    chunks = [{"text": "a DSA note", "chapter_name": "Sliding Window"}]
    ctx = format_context(chunks)
    assert "Sliding Window" in ctx
    assert "page" not in ctx.lower()
