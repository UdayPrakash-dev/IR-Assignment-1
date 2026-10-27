from src.export import export_text, format_term_line


def test_format_term_line():
    assert format_term_line("information", {0: [0], 1: [4], 3: [2, 7]}) == \
        "information (df=3): <0: 0; 1: 4; 3: 2, 7>"


def test_export_toy_index(toy_index, tmp_path):
    out = tmp_path / "index.txt"
    export_text(toy_index, out, include_doc_map=True)
    text = out.read_text(encoding="utf-8")
    lines = text.splitlines()

    assert "# documents: 5" in text
    assert "information (df=3): <0: 0; 1: 4; 3: 2, 7>" in lines
    assert "retrieval (df=3): <0: 1; 1: 1; 3: 3, 8>" in lines
    assert "fell (df=2): <2: 3; 4: 8>" in lines
    assert "3\td3\t11" in lines                     # document map row

    # terms appear in alphabetical order
    terms = [l.split(" (df=")[0] for l in lines if " (df=" in l]
    assert terms == sorted(terms)