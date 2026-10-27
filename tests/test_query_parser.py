import pytest

from src.query_parser import QueryError, parse, search_text


def T(w):
    return ("TERM", w)


# ---- parse structure ----
def test_single_term_and_phrase():
    assert parse("stock") == T("stock")
    assert parse('"interest rates"') == ("PHRASE", "interest rates")


def test_and_explicit_and_implicit():
    assert parse("stock AND fell") == ("AND", T("stock"), T("fell"))
    assert parse("stock fell") == parse("stock AND fell")


def test_precedence_and_over_or():
    assert parse("stock OR fell AND oil") == \
        ("OR", T("stock"), ("AND", T("fell"), T("oil")))


def test_not_binds_tighter_than_and():
    assert parse("NOT stock AND fell") == ("AND", ("NOT", T("stock")), T("fell"))


def test_parentheses():
    assert parse("(stock OR fell) AND oil") == \
        ("AND", ("OR", T("stock"), T("fell")), T("oil"))


def test_near():
    assert parse("retrieval NEAR/3 systems") == ("NEAR", "retrieval", "systems", 3)


def test_the_plan_example():
    q = '(stock OR market) AND "interest rate" NOT oil'
    assert parse(q) == (
        "AND",
        ("AND", ("OR", T("stock"), T("market")), ("PHRASE", "interest rate")),
        ("NOT", T("oil")),
    )


def test_lowercase_operators_are_ordinary_words():
    assert parse("stock and fell") == \
        ("AND", ("AND", T("stock"), T("and")), T("fell"))


# ---- errors ----
@pytest.mark.parametrize("bad", [
    "", "   ", "(stock", "stock)", "stock AND", "AND stock", "stock OR",
    'stock "unclosed', "NEAR/3 stock", "stock NEAR/x", "stock NEAR fell",
    '"a b" NEAR/2 c', "stock NEAR/2 (a OR b)", "a NEAR/2 b NEAR/3 c",
])
def test_malformed_queries_raise(bad):
    with pytest.raises(QueryError):
        parse(bad)


# ---- parse + run on the toy corpus (answers worked out by hand) ----
@pytest.mark.parametrize("query, expected", [
    ("Stock", [1, 2]),
    ("stock AND fell", [2]),
    ('(stock OR fell) AND "interest rates"', [2, 4]),
    ('"interest rates" NOT oil', [2]),
    ("information retrieval NOT stock", [0, 3]),
    ("retrieval NEAR/3 systems OR stock", [1, 2, 3]),
    ("NOT (stock OR fell)", [0, 3]),
])
def test_search_text(toy_index, query, expected):
    assert search_text(toy_index, query) == expected