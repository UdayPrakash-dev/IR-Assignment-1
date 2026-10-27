"""Measurements for the report: indexing time, index size, query latency.

    python -m src.evaluate                          # default (plain) configuration
    python -m src.evaluate --all-configs            # also stemming / stopwords variants
    python -m src.evaluate --all-configs --out results.md

Run from the project root. Latency covers parsing + matching only (no snippets),
averaged over repeated runs after one warm-up run.
"""
import argparse
import platform
import time
from pathlib import Path

from src.indexer import build_index, load_reuters
from src.preprocess import Preprocessor
from src.query_parser import search_text
from src.storage import load_index, save_index

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "eval"

CONFIGS = {
    "plain": dict(stem=False, remove_stopwords=False),
    "stopwords": dict(stem=False, remove_stopwords=True),
    "stem": dict(stem=True, remove_stopwords=False),
    "stem+stopwords": dict(stem=True, remove_stopwords=True),
}

# 10 queries per type, chosen for the Reuters newswire corpus.
QUERY_SETS = {
    "single term": [
        "oil", "bank", "dollar", "trade", "japan",
        "wheat", "gold", "shares", "government", "exchange",
    ],
    "AND": [
        "oil AND opec", "bank AND rates", "dollar AND yen", "trade AND deficit",
        "japan AND exports", "wheat AND tonnes", "gold AND silver",
        "shares AND market", "government AND budget", "exchange AND rate",
    ],
    "OR": [
        "oil OR gas", "gold OR silver", "wheat OR corn", "dollar OR yen",
        "bank OR loan", "trade OR tariff", "japan OR china", "coffee OR cocoa",
        "profit OR loss", "merger OR acquisition",
    ],
    "AND NOT": [
        "oil NOT opec", "bank NOT rates", "trade NOT japan", "dollar NOT yen",
        "gold NOT silver", "wheat NOT tonnes", "market NOT stock",
        "japan NOT trade", "government NOT budget", "exchange NOT rate",
    ],
    "phrase": [
        '"interest rates"', '"stock market"', '"oil prices"', '"trade deficit"',
        '"central bank"', '"united states"', '"money supply"', '"exchange rate"',
        '"bank of japan"', '"balance of payments"',
    ],
    "proximity": [
        "bank NEAR/3 england", "oil NEAR/5 prices", "interest NEAR/2 rates",
        "trade NEAR/4 deficit", "stock NEAR/3 market", "money NEAR/3 supply",
        "central NEAR/2 bank", "dollar NEAR/5 yen", "gold NEAR/5 price",
        "wheat NEAR/5 export",
    ],
    "complex": [
        "(oil OR gas) AND prices",
        '(bank OR central) AND "interest rates"',
        '"stock market" NOT crash',
        "trade AND (japan OR china) NOT deficit",
        '(gold OR silver) AND "price rise"',
        "oil AND opec NOT iran",
        '"money supply" AND (fed OR bank)',
        "(wheat OR corn) AND export NEAR/3 subsidies",
        "NOT (oil OR trade OR bank)",
        '(dollar OR yen) AND "exchange rate" NOT japan',
    ],
}


def measure_queries(index, query_sets, repeats=20):
    """Per query type: number of queries, mean/slowest latency (ms), avg matches."""
    results = {}
    for qtype, queries in query_sets.items():
        means, sizes = [], []
        for q in queries:
            sizes.append(len(search_text(index, q)))        # warm-up + result size
            t0 = time.perf_counter()
            for _ in range(repeats):
                search_text(index, q)
            means.append((time.perf_counter() - t0) / repeats * 1000)
        results[qtype] = {
            "queries": len(queries),
            "mean_ms": sum(means) / len(means),
            "max_ms": max(means),
            "avg_matches": sum(sizes) / len(sizes),
        }
    return results


def build_and_measure(corpus, name, cfg):
    """Build an index, save it, reload it. Returns (index, stats)."""
    pre = Preprocessor(**cfg)
    t0 = time.perf_counter()
    index = build_index(corpus, pre)
    build_s = time.perf_counter() - t0

    path = EVAL_DIR / f"index_{name.replace('+', '_')}.pkl"
    save_index(index, path)
    size_mb = path.stat().st_size / 1e6

    t0 = time.perf_counter()
    load_index(path)
    load_s = time.perf_counter() - t0

    return index, {
        "name": name, "docs": index.num_docs, "terms": index.vocab_size,
        "build_s": build_s, "load_s": load_s, "size_mb": size_mb,
    }


def index_table(rows):
    lines = [
        "| Configuration | Documents | Terms | Build (s) | Load (s) | Size on disk (MB) |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['name']} | {r['docs']} | {r['terms']} | "
                     f"{r['build_s']:.2f} | {r['load_s']:.2f} | {r['size_mb']:.1f} |")
    return "\n".join(lines)


def latency_table(results):
    lines = [
        "| Query type | Queries | Mean latency (ms) | Slowest query (ms) | Avg matches |",
        "|---|---|---|---|---|",
    ]
    for qtype, r in results.items():
        lines.append(f"| {qtype} | {r['queries']} | {r['mean_ms']:.3f} | "
                     f"{r['max_ms']:.3f} | {r['avg_matches']:.0f} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Measure indexing and query performance")
    ap.add_argument("--repeats", type=int, default=20, help="runs per query (default 20)")
    ap.add_argument("--all-configs", action="store_true",
                    help="also measure stemming / stopword variants")
    ap.add_argument("--out", help="also write the report to this markdown file")
    args = ap.parse_args()

    names = list(CONFIGS) if args.all_configs else ["plain"]
    print("Loading corpus into memory...")
    corpus = list(load_reuters())     # so build time excludes disk reads of the corpus

    index_rows, latency_sections = [], []
    for name in names:
        print(f"Measuring configuration: {name}")
        index, stats = build_and_measure(corpus, name, CONFIGS[name])
        index_rows.append(stats)
        latency = measure_queries(index, QUERY_SETS, args.repeats)
        latency_sections.append(f"### Query latency: {name}\n\n{latency_table(latency)}")

    report = "\n\n".join([
        f"_Measured with Python {platform.python_version()} on "
        f"{platform.system()} {platform.machine()}; "
        f"each query run {args.repeats} times, mean reported. "
        "Indexing time excludes reading the corpus from disk._",
        "### Index build\n\n" + index_table(index_rows),
        *latency_sections,
    ])
    print("\n" + report)
    if args.out:
        Path(args.out).write_text(report + "\n", encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()