import pytest

from src.indexer import build_index
from src.preprocess import Preprocessor

# Toy corpus. Token positions (no stopword removal, no stemming) are written
# out so expected answers can be checked by hand:
#
# doc 0: information0 retrieval1 is2 the3 study4 of5 search6 systems7
# doc 1: a0 retrieval1 system2 for3 information4 about5 stock6 markets7
# doc 2: the0 stock1 market2 fell3 as4 interest5 rates6 rose7
# doc 3: interest0 in1 information2 retrieval3 systems4 is5 growing6
#        information7 retrieval8 is9 fun10
# doc 4: bank0 of1 america2 raised3 interest4 rates5 oil6 prices7 fell8
TOY_DOCS = [
    ("d0", "Information retrieval is the study of search systems."),
    ("d1", "A retrieval system for information about stock markets."),
    ("d2", "The stock market fell as interest rates rose."),
    ("d3", "Interest in information retrieval systems is growing. Information retrieval is fun."),
    ("d4", "Bank of America raised interest rates; oil prices fell."),
]


@pytest.fixture
def toy_index():
    """Plain index: no stemming, no stopword removal."""
    return build_index(TOY_DOCS, Preprocessor())


@pytest.fixture
def toy_index_stopwords():
    return build_index(TOY_DOCS, Preprocessor(remove_stopwords=True))