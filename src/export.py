"""Export a PositionalIndex as a text file.

Each line is one term:

    information (df=3): <0: 0; 1: 4; 3: 2, 7>

    format: term (document frequency): <doc_id: positions; doc_id: positions; ...>
"""
import argparse
from pathlib import Path

from src.storage import load_index


def format_term_line(term, postings):
    parts = []
    for doc_id, positions in postings.items():   # already in doc_id order
        parts.append(f"{doc_id}: " + ", ".join(map(str, positions)))
    return f"{term} (df={len(postings)}): <" + "; ".join(parts) + ">"


def export_text(index, path, include_doc_map=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cfg = index.pre.config()
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Positional index\n")
        f.write(f"# documents: {index.num_docs}   terms: {index.vocab_size}\n")
        f.write(f"# stemming: {cfg['stem']}   stopword removal: {cfg['remove_stopwords']}\n")
        f.write("# format: term (df=N): <doc_id: positions; doc_id: positions; ...>\n\n")
        for term in sorted(index.postings):
            f.write(format_term_line(term, index.postings[term]) + "\n")
        if include_doc_map:
            f.write("\n# Document map (doc_id -> name, length in indexed tokens)\n")
            for doc_id, name in enumerate(index.doc_names):
                f.write(f"{doc_id}\t{name}\t{index.doc_lengths[doc_id]}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Export a saved index to a text file")
    ap.add_argument("index", help="path to saved index, e.g. data/index.pkl")
    ap.add_argument("output", help="text file to write, e.g. data/index.txt")
    ap.add_argument("--doc-map", action="store_true",
                    help="append a doc_id -> name table at the end")
    args = ap.parse_args()
    export_text(load_index(args.index), args.output, include_doc_map=args.doc_map)
    print(f"Wrote {args.output}")