""" 
    Used to save/ load PositionalIndex to disk in pickle file.
"""

import pickle
from pathlib import Path

from src.indexer import PositionalIndex
from src.preprocess import Preprocessor

FORMAT_VERSION = 1

def save_index(index,path):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    payload = {
        "version": FORMAT_VERSION,
        "preprocessor": index.pre.config(),
        "postings":index.postings,
        "doc_names": index.doc_names,
        "doc_lengths": index.doc_lengths,
    }
    with open(path,"wb") as f:
        pickle.dump(payload,f,protocol=pickle.HIGHEST_PROTOCOL)

def load_index(path):

    with open(path,"rb") as f:
        payload = pickle.load(f)

    if payload.get("version") != FORMAT_VERSION:
        raise ValueError(f"Unsupported index format: {payload.get('version')}")
    index = PositionalIndex(Preprocessor.from_config(payload["preprocessor"]))
    index.postings = payload["postings"]
    index.doc_names = payload["doc_names"]
    index.doc_lengths = payload["doc_lengths"]
    return index

if __name__ == "__main__":
    import time
    from src.indexer import build_index,load_reuters

    out = Path(__file__).resolve().parent.parent/"data"/"index.pkl"

    t0 = time.perf_counter()
    idx = build_index(load_reuters())
    t_build = time.perf_counter() - t0

    save_index(idx,out)
    t0 = time.perf_counter()
    loaded = load_index(out)
    t_load = time.perf_counter() - t0

    size_mb = out.stat().st_size/1e6

    print(f"build time = {t_build:.2f}s load_time = {t_load:.2f}s size={size_mb:.1f} MB")
    print("same vocab:", loaded.vocab_size==idx.vocab_size)
    print("same docs:", loaded.num_docs==idx.num_docs)
