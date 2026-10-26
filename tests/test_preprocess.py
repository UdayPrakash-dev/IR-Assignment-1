from src.preprocess import Preprocessor


def test_basic_tokenization_and_positions():
    p = Preprocessor()
    assert p.process("The Stock-market fell") == [
        ("the", 0), ("stock", 1), ("market", 2), ("fell", 3)
    ]


def test_stopwords_keep_original_positions():
    p = Preprocessor(remove_stopwords=True)
    assert p.process("bank of america") == [("bank", 0), ("america", 2)]


def test_stemming():
    p = Preprocessor(stem=True)
    assert p.terms("running markets") == ["run", "market"]


def test_empty_and_punctuation_only():
    p = Preprocessor()
    assert p.process("") == []
    assert p.process("!!! ... ???") == []


def test_numbers_are_kept():
    assert Preprocessor().terms("Q3 profit 2.5 pct") == ["q3", "profit", "2", "5", "pct"]


def test_config_roundtrip():
    p = Preprocessor(stem=True, remove_stopwords=True)
    q = Preprocessor.from_config(p.config())
    text = "The markets were rising"
    assert p.process(text) == q.process(text)