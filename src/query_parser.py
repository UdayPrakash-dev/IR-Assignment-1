"""Query parser: turns query text into the tree that search.evaluate() runs.

Syntax
    stock                      single term
    stock fell                 adjacent terms are ANDed
    stock AND fell             AND / OR / NOT (must be UPPERCASE)
    "interest rates"           exact phrase
    retrieval NEAR/3 systems   proximity: within 3 positions, either order
    (stock OR market) NOT oil  parentheses group

Precedence, tightest first:  NEAR  >  NOT  >  AND (explicit or implicit)  >  OR

Operators are uppercase-only so that "and", "or", "not" and "near" can still be
searched as ordinary words.

Grammar
    or_expr   := and_expr ( OR and_expr )*
    and_expr  := not_expr ( [AND] not_expr )*
    not_expr  := NOT not_expr | near_expr
    near_expr := primary [ NEAR/k primary ]      (operands must be single words)
    primary   := WORD | "phrase" | ( or_expr )
"""
import re

from src.search import evaluate


class QueryError(ValueError):
    """Raised for malformed queries; the message is safe to show to the user."""


_TOKEN_RE = re.compile(r'"[^"]*"|\(|\)|[^\s()"]+')
_STARTS_OPERAND = {"WORD", "PHRASE", "LP", "NOT"}


def tokenize(query):
    if query.count('"') % 2:
        raise QueryError("unbalanced quotes")
    tokens = []
    for raw in _TOKEN_RE.findall(query):
        if raw[0] == '"':
            tokens.append(("PHRASE", raw[1:-1]))
        elif raw == "(":
            tokens.append(("LP", raw))
        elif raw == ")":
            tokens.append(("RP", raw))
        elif raw in ("AND", "OR", "NOT"):
            tokens.append((raw, raw))
        elif raw == "NEAR":
            raise QueryError("NEAR needs a distance, e.g. NEAR/3")
        elif raw.startswith("NEAR/"):
            if not raw[5:].isdigit():
                raise QueryError(f"bad proximity operator '{raw}' (use NEAR/3)")
            tokens.append(("NEAR", int(raw[5:])))
        else:
            tokens.append(("WORD", raw))
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self):
        return self.toks[self.i][0] if self.i < len(self.toks) else None

    def advance(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def describe_next(self):
        kind, value = self.toks[self.i]
        if kind == "NEAR":
            return f"NEAR/{value}"
        if kind in ("AND", "OR", "NOT", "LP", "RP"):
            return f"'{value}'"
        return f"'{value}'"

    # ---- grammar ----
    def parse(self):
        node = self.or_expr()
        if self.i < len(self.toks):
            if self.peek() == "RP":
                raise QueryError("unmatched ')'")
            raise QueryError(f"unexpected {self.describe_next()}")
        return node

    def or_expr(self):
        left = self.and_expr()
        while self.peek() == "OR":
            self.advance()
            left = ("OR", left, self.and_expr())
        return left

    def and_expr(self):
        left = self.not_expr()
        while True:
            kind = self.peek()
            if kind == "AND":
                self.advance()
                right = self.not_expr()
            elif kind in _STARTS_OPERAND:      # implicit AND
                right = self.not_expr()
            else:
                break
            left = ("AND", left, right)
        return left

    def not_expr(self):
        if self.peek() == "NOT":
            self.advance()
            return ("NOT", self.not_expr())
        return self.near_expr()

    def near_expr(self):
        left = self.primary()
        if self.peek() == "NEAR":
            k = self.advance()[1]
            right = self.primary()
            if left[0] != "TERM" or right[0] != "TERM":
                raise QueryError("NEAR operands must be single words")
            return ("NEAR", left[1], right[1], k)
        return left

    def primary(self):
        kind = self.peek()
        if kind is None:
            raise QueryError("query ended unexpectedly")
        if kind == "WORD":
            return ("TERM", self.advance()[1])
        if kind == "PHRASE":
            return ("PHRASE", self.advance()[1])
        if kind == "LP":
            self.advance()
            node = self.or_expr()
            if self.peek() != "RP":
                raise QueryError("missing ')'")
            self.advance()
            return node
        raise QueryError(f"unexpected {self.describe_next()}")


def parse(query):
    tokens = tokenize(query)
    if not tokens:
        raise QueryError("empty query")
    return _Parser(tokens).parse()


def search_text(index, query):
    """Parse and run a query string. Returns sorted doc_ids."""
    return evaluate(index, parse(query))