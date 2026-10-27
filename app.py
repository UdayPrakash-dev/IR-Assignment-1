"""Command line interface for the search engine.

Build the index:   python app.py --build [--stem] [--stopwords]
Search (prompt):   python app.py
One-off query:     python app.py --query '"interest rates" NOT oil'
"""
import argparse
import sys
import time
from pathlib import Path

from src.indexer import build_index, load_reuters
from src.preprocess import TOKEN_RE, Preprocessor
from src.query_parser import parse
from src.search import evaluate, phrase_matches, proximity_matches
from src.storage import load_index, save_index

DEFAULT_INDEX = Path(__file__).resolve().parent / "data" / "index.pkl"

HELP = """Query syntax
  stock                       single term
  stock fell                  adjacent terms are ANDed
  stock AND fell | OR | NOT   Boolean operators (UPPERCASE)
  "interest rates"            exact phrase
  retrieval NEAR/3 systems    within 3 words of each other, either order
  (stock OR market) NOT oil   parentheses group
Commands
  :top N    show N results      :stats   index info
  :help     this text           :q       quit"""


# ---- snippets -------------------------------------------------------------
def collect_hits(index, node):
    """Positions that caused a match: {doc_id: [(start_position, length), ...]}.

    Only positive parts of the query contribute (nothing comes from NOT).
    """
    hits = {}

    def add(doc_id, start, length):
        hits.setdefault(doc_id, []).append((start, length))

    op = node[0]
    if op == "TERM":
        for term in index.pre.terms(node[1]):
            for doc_id, positions in index.postings.get(term, {}).items():
                for p in positions:
                    add(doc_id, p, 1)
    elif op == "PHRASE":
        tokens = index.pre.process(node[1])
        if tokens:
            span = tokens[-1][1] - tokens[0][1] + 1
            for doc_id, starts in phrase_matches(index, node[1]).items():
                for p in starts:
                    add(doc_id, p, span)
    elif op == "NEAR":
        for doc_id, starts in proximity_matches(index, node[1], node[2], node[3]).items():
            for p in starts:
                add(doc_id, p, 1)
    elif op in ("AND", "OR"):
        for child in node[1:]:
            for doc_id, found in collect_hits(index, child).items():
                hits.setdefault(doc_id, []).extend(found)

    for found in hits.values():
        found.sort()
    return hits


def make_snippet(text, start, length, window=8):
    """Text around token positions [start, start+length), match marked >>like this<<."""
    spans = [m.span() for m in TOKEN_RE.finditer(text.lower())]
    if start >= len(spans):
        return " ".join(text.split())[:100]
    last = min(start + length, len(spans)) - 1
    lo = max(0, start - window)
    hi = min(len(spans) - 1, last + window)
    ms, me = spans[start][0], spans[last][1]
    body = text[spans[lo][0]:ms] + ">>" + text[ms:me] + "<<" + text[me:spans[hi][1]]
    body = " ".join(body.split())
    return ("... " if lo > 0 else "") + body + (" ..." if hi < len(spans) - 1 else "")


def get_text(name):
    """Raw document text for the snippet (Reuters via NLTK), or None."""
    try:
        from nltk.corpus import reuters
        return reuters.raw(name)
    except Exception:
        return None


# ---- searching and display ---------------------------------------------------
def run_query(index, query, top=10):
    t0 = time.perf_counter()
    try:
        node = parse(query)
        doc_ids = evaluate(index, node)
    except ValueError as e:            # includes QueryError
        print(f"Query error: {e}")
        return
    elapsed_ms = (time.perf_counter() - t0) * 1000

    print(f"{len(doc_ids)} matching document(s) in {elapsed_ms:.1f} ms")
    if not doc_ids:
        return
    hits = collect_hits(index, node)
    for doc_id in doc_ids[:top]:
        name = index.doc_names[doc_id]
        found = hits.get(doc_id)
        if found:
            label = "match" if len(found) == 1 else "matches"
            print(f"  {name}  ({len(found)} {label})")
        else:
            print(f"  {name}")
        text = get_text(name)
        if text:
            if found:
                print("      " + make_snippet(text, *found[0]))
            else:
                print("      " + " ".join(text.split())[:100])
    if len(doc_ids) > top:
        print(f"  ... and {len(doc_ids) - top} more (use :top N to show more)")


def repl(index, top):
    print(f"Index loaded: {index.num_docs} docs, {index.vocab_size} terms. "
          "Type :help for syntax, :q to quit.")
    while True:
        try:
            line = input("search> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in (":q", ":quit"):
            break
        if line == ":help":
            print(HELP)
        elif line == ":stats":
            cfg = index.pre.config()
            print(f"docs={index.num_docs} terms={index.vocab_size} "
                  f"stem={cfg['stem']} stopwords={cfg['remove_stopwords']}")
        elif line.startswith(":top"):
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) > 0:
                top = int(parts[1])
                print(f"Showing up to {top} results")
            else:
                print("Usage: :top N")
        else:
            run_query(index, line, top)


# ---- building ---------------------------------------------------------------
def build(args):
    pre = Preprocessor(stem=args.stem, remove_stopwords=args.stopwords)
    t0 = time.perf_counter()
    index = build_index(load_reuters(), pre)
    t_build = time.perf_counter() - t0
    save_index(index, args.index)
    size_mb = Path(args.index).stat().st_size / 1e6
    print(f"Indexed {index.num_docs} docs, {index.vocab_size} terms in {t_build:.2f}s "
          f"(stem={args.stem}, stopwords={args.stopwords})")
    print(f"Saved to {args.index} ({size_mb:.1f} MB)")


def main():
    ap = argparse.ArgumentParser(description="Positional-index search engine (Reuters-21578)")
    ap.add_argument("--index", default=str(DEFAULT_INDEX), help="index file path")
    ap.add_argument("--build", action="store_true", help="build the index and save it")
    ap.add_argument("--stem", action="store_true", help="(with --build) Porter stemming")
    ap.add_argument("--stopwords", action="store_true", help="(with --build) remove stopwords")
    ap.add_argument("--query", help="run one query and exit")
    ap.add_argument("--top", type=int, default=10, help="results to show (default 10)")
    args = ap.parse_args()

    if (args.stem or args.stopwords) and not args.build:
        ap.error("--stem and --stopwords only apply together with --build")

    if args.build:
        build(args)
        return

    if not Path(args.index).exists():
        print(f"No index found at {args.index}. Build one first:  python app.py --build")
        sys.exit(1)
    index = load_index(args.index)
    if args.query:
        run_query(index, args.query, args.top)
    else:
        repl(index, args.top)


if __name__ == "__main__":
    main()