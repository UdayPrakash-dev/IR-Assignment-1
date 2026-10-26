
def test_counts(toy_index):
    assert toy_index.num_docs == 5
    assert toy_index.doc_names == ["d0", "d1", "d2", "d3", "d4"]
    assert toy_index.all_doc_ids() == [0, 1, 2, 3, 4]


def test_positions_match_hand_computed(toy_index):
    assert toy_index.postings["information"] == {0: [0], 1: [4], 3: [2, 7]}
    assert toy_index.postings["retrieval"] == {0: [1], 1: [1], 3: [3, 8]}
    assert toy_index.postings["fell"] == {2: [3], 4: [8]}


def test_df_and_tf(toy_index):
    assert toy_index.df("interest") == 3          # docs 2, 3, 4
    assert toy_index.tf("information", 3) == 2
    assert toy_index.tf("information", 2) == 0    # term absent from doc
    assert toy_index.df("zebra") == 0


def test_docs_for_is_sorted(toy_index):
    assert toy_index.docs_for("stock") == [1, 2]
    assert toy_index.docs_for("interest") == [2, 3, 4]
    assert toy_index.docs_for("zebra") == []


def test_doc_lengths(toy_index):
    assert toy_index.doc_lengths == [8, 8, 8, 11, 9]


def test_stopword_removal_keeps_gaps(toy_index_stopwords):
    # "Bank of America": 'of' removed, but america stays at position 2
    assert toy_index_stopwords.postings["bank"] == {4: [0]}
    assert toy_index_stopwords.postings["america"] == {4: [2]}
    assert "of" not in toy_index_stopwords.postings