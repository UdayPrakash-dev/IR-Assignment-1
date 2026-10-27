from src.search import difference, evaluate, intersect, union


def T(w):
    return ("TERM", w)


# ---- merge functions ----
def test_intersect():
    assert intersect([1, 3, 5, 7], [3, 4, 5, 8]) == [3, 5]
    assert intersect([], [1, 2]) == []


def test_union():
    assert union([1, 3, 5], [2, 3, 6]) == [1, 2, 3, 5, 6]
    assert union([], [4]) == [4]


def test_difference():
    assert difference([0, 1, 2, 3, 4], [1, 3]) == [0, 2, 4]
    assert difference([1, 2], []) == [1, 2]


# ---- queries on the toy corpus (expected answers worked out by hand) ----
def test_single_term(toy_index):
    assert evaluate(toy_index, T("stock")) == [1, 2]
    assert evaluate(toy_index, T("Stock")) == [1, 2]     # case-insensitive
    assert evaluate(toy_index, T("zebra")) == []


def test_and(toy_index):
    assert evaluate(toy_index, ("AND", T("stock"), T("fell"))) == [2]
    assert evaluate(toy_index, ("AND", T("information"), T("retrieval"))) == [0, 1, 3]


def test_or(toy_index):
    assert evaluate(toy_index, ("OR", T("stock"), T("fell"))) == [1, 2, 4]


def test_not(toy_index):
    assert evaluate(toy_index, ("NOT", T("stock"))) == [0, 3, 4]
    assert evaluate(toy_index, ("NOT", T("zebra"))) == [0, 1, 2, 3, 4]


def test_and_not(toy_index):
    # interest is in docs 2,3,4; rates is in 2,4  ->  only doc 3 is left
    q = ("AND", T("interest"), ("NOT", T("rates")))
    assert evaluate(toy_index, q) == [3]


def test_hyphenated_word_needs_all_parts(toy_index):
    # "stock-market" -> stock AND market -> only doc 2 has both
    assert evaluate(toy_index, T("stock-market")) == [2]


def test_stopword_term_matches_nothing(toy_index_stopwords):
    assert evaluate(toy_index_stopwords, T("the")) == []