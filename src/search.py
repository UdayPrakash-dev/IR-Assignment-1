"""
Boolean retrieval over a PositionalIndex

format for Queries:
    ("TERM","stock")
    ("AND",left,right)
    ("OR",left,right)
    ("NOT",child)
    ("PHRASE","infomatoin retrieval")
    ("NEAR","retrieval","information",3)
"""

from bisect import bisect_left

def intersect(a,b):
    """
    Both docs in a and b,
    a and b are posting list of 2 distinct terms
    """
    i = j = 0
    res = []
    while i<len(a) and j<len(b):
        if a[i] == b[j]:
            res.append(a[i])
            i+=1
            j+=1
        elif a[i]<b[j]:
            i+=1
        else:
            j+=1

    return res

def union(a,b):
    """
    Docs in a or b or both.
    a and b are posting list of 2 distinct terms
    """
    i = j = 0
    res = []
    while i<len(a) and j<len(b):
        if a[i] == b[j]:
            res.append(a[i])
            i+=1
            j+=1
        elif a[i]<b[j]:
            res.append(a[i])
            i+=1
        else:
            res.append(b[j])
            j+=1
    
    res.extend(a[i:])
    res.extend(b[j:])
    return res

def difference(a,b):
    """
        Docs in a but not in b
    """
    i = j = 0
    res = []

    while i<len(a) and j<len(b):
        if a[i] == b[j]:
            i+=1
            j+=1
        elif a[i]<b[j]:
            res.append(a[i])
            i+=1
        else:
            j+=1
    res.extend(a[i:])
    return res

def term_docs(index,word):
    """ 
        Docs matching a raw query word, runs through the same index pipeline as the docs(stemming etc.)

        For a phrasal query or split word , all of the words must match in order for the search to be successful
    """

    terms = index.pre.terms(word)
    if not terms:
        return []
    result = index.docs_for(terms[0])
    for t in terms[1:]:
        result = intersect(result,index.docs_for(t))
    return result


def phrase_matches(index,phrase):

    tokens = index.pre.process(phrase)
    if not tokens:
        return {}
    base = tokens[0][1]
    parts = [(term, pos - base) for term,pos in tokens ]

    candidates = index.docs_for(parts[0][0])
    for term,_ in parts[1:]:
        candidates = intersect(candidates, index.docs_for(term))

    matches = {}
    for doc_id in candidates:
        first_term = parts[0][0]
        pos_sets = {t:set(index.positions(t,doc_id)) for t,_ in parts}
        starts = [
            p for p in index.positions(first_term,doc_id)
            if all((p+off) in pos_sets[t] for t, off in parts)
        ]
        if starts:
            matches[doc_id] = starts

    return matches

def phrase_docs(index,phrase):
    #returns the docs ids that contains the phrase in sorted id
    return sorted(phrase_matches(index,phrase))

def proximity_matches(index,word_a,word_b,k):
    terms_a = index.pre.terms(word_a)
    terms_b = index.pre.terms(word_b)

    if len(terms_a)>1 or len(terms>b):
        raise ValueError("Operands must be single terms")

    if not terms_a or not terms_b:
        return {}

    #first calculate intersection set, as in the others there is no point in searching
    inter = intersect(index.docs_for(a),index.docs_for(b))

    matches = {}
    for doc in inter:
        pos_b = index.position(b,doc_id)
        hits = []
        for p in index.positions(a,doc_id):
            #find the least position in the windows which matches the word b, and traverse till p+k, to find occurences.
            i = bisect_left(pos_b,p-k)
            while i<len(pos_b) and pos_b[i]<=p+k:
                if pos_b[i]!=p:
                    hits.append(p)
                    break
                i+=1

        if hits:
            matches[doc_id] = hits

    return matches

def proximity_docs(index, word_a, word_b, k):
    return sorted(proximity_matches(index, word_a, word_b, k))


def evaluate(index,node):
    op = node[0]
    if op == "TERM":
        return term_docs(index,node[1])
    elif op == "PHRASE":
        return phrase_docs(index,node[1])
    elif op == "NEAR":
        return proximity_docs(index,node[1],node[2],node[3])
    elif op == "AND":
        return intersect(evaluate(index,node[1]),evaluate(index,node[2]))
    elif op == "OR":
        return union(evaluate(index,node[1]),evaluate(index,node[2]))
    elif op == "NOT":
        return difference(index.all_doc_ids(),evaluate(index,node[1]))
    raise ValueError(f"Unknown Operator: {op}")

