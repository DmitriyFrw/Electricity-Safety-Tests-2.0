"""Tests for multi-answer parsing and scoring."""

from app.support.answers import (
    decode_correct_indexes,
    encode_correct_indexes,
    format_answer_labels,
    is_answer_correct,
    is_selected_answer_correct,
    parse_answer_labels,
    set_user_answer_from_raw,
    user_answer_selected_indices,
)
from app.models import UserAnswer


def test_parse_multiple_labels_comma():
    assert parse_answer_labels("A,C", option_count=4) == [0, 2]


def test_parse_multiple_labels_concatenated():
    assert parse_answer_labels("AC", option_count=4) == [0, 2]


def test_parse_single_label():
    assert parse_answer_labels("B", option_count=2) == [1]


def test_encode_decode_roundtrip():
    raw = encode_correct_indexes([0, 2, 3])
    assert decode_correct_indexes(raw) == [0, 2, 3]


def test_format_answer_labels():
    assert format_answer_labels([0, 2]) == "A,C"


def test_is_answer_correct_single():
    assert is_answer_correct([1], [1]) is True
    assert is_answer_correct([0], [1]) is False


def test_is_answer_correct_multiple_exact_match():
    assert is_answer_correct([0, 2], [0, 2]) is True
    assert is_answer_correct([0], [0, 2]) is False
    assert is_answer_correct([0, 1, 2], [0, 2]) is False


def test_is_selected_answer_correct_single_only():
    assert is_selected_answer_correct(1, [1]) is True
    assert is_selected_answer_correct(0, [1]) is False


def test_user_answer_selected_indexes():
    ua = UserAnswer(attempt_id=1, question_id=1, selected_index=0, selected_indexes="0,2")
    assert user_answer_selected_indices(ua) == [0, 2]


def test_set_user_answer_from_raw_multi():
    ua = UserAnswer(attempt_id=1, question_id=1, selected_index=None)
    indices = set_user_answer_from_raw(ua, "A,C", option_count=4)
    assert indices == [0, 2]
    assert ua.selected_index == 0
    assert ua.selected_indexes == "0,2"
