"""Passing these checks does not establish units, meaning or completeness."""
from numguard import Fact, FactSet, evaluate


def test_known_gap_unit_swap_still_passes():
    assert evaluate("19% reported an event.", FactSet([Fact("count", 19, "participants")])).passed


def test_known_gap_spelled_out_number_is_outside_numeric_grammar():
    assert evaluate("Nineteen participants had an event.", FactSet([Fact("n", 24)])).passed


def test_known_gap_banned_phrase_paraphrase_is_not_a_semantic_check():
    assert evaluate("An encouraging tolerability profile.", FactSet(), banned_phrases=["well tolerated"]).passed
