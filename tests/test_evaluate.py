from src.evaluate import QUERY_SETS, latency_table, measure_queries
from src.query_parser import parse


def test_measure_queries_on_toy_corpus(toy_index):
    sets = {"term": ["stock", "fell"], "and": ["stock AND fell"]}
    res = measure_queries(toy_index, sets, repeats=3)
    assert set(res) == {"term", "and"}
    assert res["term"]["queries"] == 2
    assert res["term"]["avg_matches"] == 2.0     # stock -> 2 docs, fell -> 2 docs
    assert res["and"]["avg_matches"] == 1.0      # only doc 2 has both
    assert res["and"]["mean_ms"] >= 0


def test_latency_table_has_a_row_per_query_type(toy_index):
    res = measure_queries(toy_index, {"term": ["stock"], "phrase": ['"stock market"']}, 2)
    table = latency_table(res)
    assert "| term |" in table and "| phrase |" in table


def test_every_benchmark_query_parses():
    for qtype, queries in QUERY_SETS.items():
        assert len(queries) == 10, qtype
        for q in queries:
            parse(q)            # raises QueryError if the syntax is wrong