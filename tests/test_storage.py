from src.indexer import build_index
from src.preprocess import Preprocessor
from src.storage import load_index, save_index
from conftest import TOY_DOCS


def test_roundtrip_plain(toy_index, tmp_path):
    path = tmp_path / "idx.pkl"
    save_index(toy_index, path)
    loaded = load_index(path)
    assert loaded.postings == toy_index.postings
    assert loaded.doc_names == toy_index.doc_names
    assert loaded.doc_lengths == toy_index.doc_lengths


def test_roundtrip_keeps_preprocessing_settings(tmp_path):
    idx = build_index(TOY_DOCS, Preprocessor(stem=True, remove_stopwords=True))
    path = tmp_path / "nested" / "idx.pkl"   # also checks folder creation
    save_index(idx, path)
    loaded = load_index(path)
    assert loaded.pre.config() == {"stem": True, "remove_stopwords": True}
    assert loaded.postings == idx.postings
    # queries on the loaded index go through the same pipeline
    assert loaded.pre.terms("Markets") == idx.pre.terms("Markets")