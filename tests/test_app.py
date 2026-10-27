from app import collect_hits, make_snippet, run_query
from src.query_parser import parse


# ---- collect_hits (positions from the comments in conftest.py) ----
def test_hits_for_phrase(toy_index):
    hits = collect_hits(toy_index, parse('"information retrieval"'))
    assert hits == {0: [(0, 2)], 3: [(2, 2), (7, 2)]}


def test_hits_for_term(toy_index):
    assert collect_hits(toy_index, parse("stock")) == {1: [(6, 1)], 2: [(1, 1)]}


def test_hits_merge_through_and(toy_index):
    hits = collect_hits(toy_index, parse("stock AND fell"))
    assert hits[2] == [(1, 1), (3, 1)]


def test_hits_ignore_not(toy_index):
    assert collect_hits(toy_index, parse("NOT stock")) == {}


def test_hits_for_near(toy_index):
    assert collect_hits(toy_index, parse("retrieval NEAR/1 systems")) == {3: [(3, 1)]}


# ---- make_snippet ----
TEXT = "The Stock market fell as interest rates rose sharply today in Tokyo"


def test_snippet_at_start():
    assert make_snippet(TEXT, 1, 2, window=2) == "The >>Stock market<< fell as ..."


def test_snippet_in_middle():
    assert make_snippet(TEXT, 5, 2, window=1) == "... as >>interest rates<< rose ..."


def test_snippet_position_out_of_range_falls_back():
    assert make_snippet("short  text", 999, 1) == "short text"


# ---- run_query output ----
def test_run_query_prints_results(toy_index, capsys):
    run_query(toy_index, '"interest rates" NOT oil', top=10)
    out = capsys.readouterr().out
    assert "1 matching document(s)" in out
    assert "d2" in out and "d4" not in out


def test_run_query_reports_errors_without_crashing(toy_index, capsys):
    run_query(toy_index, "(stock", top=10)
    assert "Query error" in capsys.readouterr().out