"""
Positional Index: term -> {doc_id: [positions]}

tf(term,doc) = len(postions)
df(term) = len(postings[term])

docid -> assigned as int in the order inserted.
so every postings dict is already in increasing doc_id
"""

from pathlib import Path 
import nltk
from src.preprocess import Preprocessor

NLTK_DIR = Path(__file__).resolve().parent.parent/"data"/"nltk_data"
if str(NLTK_DIR) not in nltk.data.path:
    nltk.data.path.append(str(NLTK_DIR))

class PositionalIndex:
    def __init__(self,preprocessor=None):
        self.pre = preprocessor or Preprocessor()
        self.postings = {} #term->{doc_id:[postings]}
        self.doc_names = []  #stores the doc name, also used for calcualting doc_id using length
        self.doc_lengths = [] #no of indexed tokens ?

    def add_document(self,name,text):
        doc_id = len(self.doc_names)
        self.doc_names.append(name)
        tokens = self.pre.process(text)
        self.doc_lengths.append(len(tokens))

        for term,pos in tokens:
            self.postings.setdefault(term,{}).setdefault(doc_id,[]).append(pos)

        return doc_id

    @property
    def num_docs(self):
        return len(self.doc_names)

    @property
    def vocab_size(self):
        return len(self.postings)

    def all_doc_ids(self):
        "universal set, required for not"
        return list(range(self.num_docs))

    def docs_for(self,term):
        "Sorted list of doc_ids containig term"
        return list(self.postings.get(term,{}))

    def positions(self,term,doc_id):
        return self.postings.get(term,{}).get(doc_id,[])

    def df(self,term):
        return len(self.postings.get(term,{}))

    def tf(self,term,doc_id):
        return len(self.positions(term,doc_id))


def build_index(corpus,preprocessor=None):
    index = PositionalIndex(preprocessor)
    for name,text in corpus:
        index.add_document(name,text)
    return index

def load_reuters():
    from nltk.corpus import reuters
    for fileid in sorted(reuters.fileids()):
        yield fileid, reuters.raw(fileid)

    
if __name__=="__main__":
    import time
    t0 = time.perf_counter()
    idx = build_index(load_reuters())
    dt = time.perf_counter() - t0
    print(f"DOCS={idx.num_docs} vocab={idx.vocab_size} build={dt:.2f}s")
    print("df('stock)=", idx.df('stock')," | df('market) = ",idx.df('market'))
        
