import re
from functools import lru_cache
from pathlib import Path 

import nltk
from nltk.stem import PorterStemmer

NLTK_DIR  = Path(__file__).resolve().parent.parent/"data"/"nltk_data"
if str(NLTK_DIR) not in nltk.data.path:
    nltk.data.path.append(str(NLTK_DIR))

TOKEN_RE = re.compile(r"[a-z0-9]+")

class Preprocessor:

    def __init__(self,stem=False,remove_stopwords=False):
        self.stem = stem
        self.remove_stopwords = remove_stopwords

        self._stopwords = frozenset()

        if remove_stopwords:
            from nltk.corpus import stopwords
            self._stopwords = frozenset(stopwords.words("english"))

        self._stem = None

        if stem:
            self._stem = lru_cache(maxsize=None)(PorterStemmer().stem)

    def process(self,text):
        """
            Returns a list of (term,position) pairs
            Position here refers to the original postion before stemminmg
         """

        out = []

        for pos,tok in enumerate(TOKEN_RE.findall(text.lower())):
            if tok in self._stopwords:
                continue
            if self._stem is not None:
                tok = self._stem(tok)
            
            out.append((tok,pos))
        
        return out

    def terms(self,text):
        "For boolean queries-> only terms"
        return [t for t,_ in self.process(text)]

    def config(self):
        return {"stem":self.stem,"remove_stopwords":self.remove_stopwords}

    @classmethod
    def from_config(cls,cfg):
        return cls(**cfg)

if __name__=="__main__":
    p = Preprocessor(stem=True,remove_stopwords=True)
    print(p.process("The Stock-prices of SpaceX started falling 2 weeks after their IPO."))