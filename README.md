# Positional Index Search Engine

A small information-retrieval system written from scratch in Python. It builds an
inverted / positional index over the Reuters-21578 news corpus and answers
Boolean, phrase and proximity queries from a command-line interface.

No search library is used for indexing or retrieval. The point of the project is
to implement the data structures and algorithms directly.

## Features

- **Preprocessing:** lowercasing, regex tokenization, optional stopword removal and
  Porter stemming. Token positions are preserved across stopword removal.
- **Positional index:** `term -> {doc_id: [positions]}`. One structure serves as both
  the inverted index (document frequency, postings) and the positional index.
- **Queries:** Boolean (`AND`, `OR`, `NOT`), exact phrases, proximity (`NEAR/k`),
  and parentheses, with a hand-written recursive-descent parser.
- **Persistence:** save and load the index to disk (pickle) together with its
  preprocessing settings.
- **Text export:** write the index as a human-readable `.txt` file.
- **CLI:** interactive prompt or one-off queries, with result snippets.
- **Measurements:** indexing time, index size, and query latency per query type.

## Project structure

```
Inverted_Index/
├── app.py                # command-line interface
├── src/
│   ├── __init__.py
│   ├── preprocess.py     # tokenizer, stopwords, stemmer
│   ├── indexer.py        # PositionalIndex, build_index, Reuters loader
│   ├── storage.py        # save / load index (pickle)
│   ├── export.py         # export index as readable text
│   ├── search.py         # merges, Boolean / phrase / proximity retrieval
│   ├── query_parser.py   # query text -> query tree
│   └── evaluate.py       # timing and size measurements
├── tests/                # unit tests on a 5-document toy corpus
├── data/                 # NLTK data, saved indexes, exports
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.9+.

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import nltk; nltk.download('reuters', download_dir='data/nltk_data'); nltk.download('stopwords', download_dir='data/nltk_data')"
```

## Usage

Run all commands from the project root.

**1. Build the index** (once):

```bash
python app.py --build                        # plain index
python app.py --build --stem --stopwords     # with stemming and stopword removal
```

**2. Search:**

```bash
python app.py                                # interactive prompt
python app.py --query '"interest rates" NOT oil' --top 5
```

Prompt commands: `:help`, `:top N`, `:stats`, `:q`.

**3. Export the index as text:**

```bash
python -m src.export data/index.pkl data/index.txt --doc-map
```

Each line has the form `term (df=N): <doc_id: positions; doc_id: positions; ...>`, e.g.

```
information (df=3): <0: 0; 1: 4; 3: 2, 7>
```

**4. Run the tests:**

```bash
python -m pytest tests -v
```

**5. Run the measurements:**

```bash
python -m src.evaluate --all-configs --out results.md
```

## Query syntax

| Query | Meaning |
|---|---|
| `oil` | documents containing the term |
| `oil opec` | adjacent terms are ANDed |
| `oil AND opec`, `oil OR gas`, `oil NOT opec` | Boolean operators (**uppercase only**) |
| `"interest rates"` | exact phrase: words adjacent and in order |
| `bank NEAR/3 england` | both words within 3 positions, in either order |
| `(gold OR silver) AND "price rise"` | parentheses group sub-queries |

Precedence, tightest first: `NEAR`, `NOT`, `AND`, `OR`.

## Design decisions

- **One index for everything.** Term frequency is `len(positions)` and document
  frequency is `len(postings[term])`, so no second inverted index is needed. Doc IDs
  are assigned in insertion order, so every postings list is already sorted.
- **Sorted-list merging.** AND, OR and NOT are single-pass two-pointer merges over
  sorted doc-ID lists. `NOT x` is the set difference between all documents and `x`.
- **Phrase queries.** Documents containing every word are found first by
  intersection. Then, for each occurrence of the first word at position `p`, the
  remaining words must sit at `p + offset`.
- **Stopwords keep their positions.** With stopword removal on, `"bank of america"`
  is indexed as `bank@0, america@2`, and the query keeps the same gap. A phrase
  therefore never matches across a removed word.
- **Proximity semantics.** `A NEAR/k B` matches when `|posA - posB| <= k`, so order
  does not matter and `NEAR/1` means adjacent. A word is never near itself, so
  `x NEAR/5 x` needs two different occurrences. Both operands must be single words.
  The window is found with binary search (`bisect`) on B's sorted positions.
- **Same pipeline for documents and queries.** The preprocessing settings are saved
  inside the index file and restored on load, so queries are always processed the
  way the documents were.
- **Operators are uppercase.** `and`, `or`, `not` and `near` remain searchable as
  ordinary words.
- **Persistence uses pickle.** Fast and simple. Only load index files you built
  yourself, because unpickling untrusted files can execute code.

## Testing

Correctness is checked with unit tests on a five-document toy corpus
(`tests/conftest.py`) whose token positions are written out by hand, so every
expected answer can be verified without running the code. Tests cover
preprocessing, index construction, persistence round-trips, text export, Boolean
merges, phrase and proximity matching, the query parser (structure, precedence and
error handling), snippets, and the CLI output.

## Results

_Measured with Python 3.14.8 on Linux x86_64; each query run 20 times, mean reported. Indexing time excludes reading the corpus from disk._

### Index build

| Configuration | Documents | Terms | Build (s) | Load (s) | Size on disk (MB) |
|---|---|---|---|---|---|
| plain | 10788 | 30952 | 1.06 | 0.33 | 9.0 |
| stopwords | 10788 | 30806 | 1.19 | 0.25 | 6.9 |
| stem | 10788 | 23387 | 1.71 | 0.31 | 8.7 |
| stem+stopwords | 10788 | 23287 | 1.54 | 0.24 | 6.6 |

### Query latency: plain

| Query type | Queries | Mean latency (ms) | Slowest query (ms) | Avg matches |
|---|---|---|---|---|
| single term | 10 | 0.006 | 0.009 | 845 |
| AND | 10 | 0.174 | 0.380 | 175 |
| OR | 10 | 0.138 | 0.290 | 887 |
| AND NOT | 10 | 3.160 | 3.258 | 657 |
| phrase | 10 | 1.100 | 2.198 | 187 |
| proximity | 10 | 0.404 | 0.686 | 158 |
| complex | 10 | 2.103 | 3.993 | 882 |

### Query latency: stopwords

| Query type | Queries | Mean latency (ms) | Slowest query (ms) | Avg matches |
|---|---|---|---|---|
| single term | 10 | 0.006 | 0.008 | 845 |
| AND | 10 | 0.169 | 0.361 | 175 |
| OR | 10 | 0.137 | 0.288 | 887 |
| AND NOT | 10 | 3.186 | 3.312 | 657 |
| phrase | 10 | 0.851 | 1.428 | 187 |
| proximity | 10 | 0.397 | 0.672 | 158 |
| complex | 10 | 2.124 | 4.076 | 882 |

### Query latency: stem

| Query type | Queries | Mean latency (ms) | Slowest query (ms) | Avg matches |
|---|---|---|---|---|
| single term | 10 | 0.007 | 0.013 | 1042 |
| AND | 10 | 0.222 | 0.592 | 244 |
| OR | 10 | 0.158 | 0.343 | 1006 |
| AND NOT | 10 | 3.141 | 3.246 | 724 |
| phrase | 10 | 1.309 | 2.384 | 209 |
| proximity | 10 | 0.515 | 0.893 | 180 |
| complex | 10 | 2.359 | 4.347 | 866 |

### Query latency: stem+stopwords

| Query type | Queries | Mean latency (ms) | Slowest query (ms) | Avg matches |
|---|---|---|---|---|
| single term | 10 | 0.007 | 0.014 | 1042 |
| AND | 10 | 0.224 | 0.598 | 244 |
| OR | 10 | 0.160 | 0.347 | 1006 |
| AND NOT | 10 | 3.201 | 3.314 | 724 |
| phrase | 10 | 1.060 | 1.827 | 209 |
| proximity | 10 | 0.500 | 0.864 | 180 |
| complex | 10 | 2.351 | 4.357 | 866 |


## Limitations

- Results are listed in document-ID order. There is no relevance ranking yet.
- No relevance judgments are used, so there are no precision/recall metrics.
  Correctness is established through unit tests; the measurements cover performance only.
- Snippets are read from the Reuters corpus through NLTK, and the index does not
  store the original text.
- A query word that is a stopword matches nothing when the index was built with
  stopword removal.
- The index is held entirely in memory, with no compression or skip pointers.

## Future work (v2)

- TF-IDF and BM25 ranked retrieval.
- Evaluation on a collection with relevance judgments (e.g. Cranfield) using
  Precision@k, MAP and nDCG.
- Postings compression (gap encoding with variable-byte), skip pointers for AND.
- Wildcard queries and spelling correction.
- Optional web interface.

## Dataset

Reuters-21578 (ModApte split, 10,788 documents), loaded through
`nltk.corpus.reuters`.