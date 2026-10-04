"""Lexical helpers shared by intent rules, the ranker and conflict rules, and exact token counts."""
from __future__ import annotations

import re
from functools import lru_cache

import tiktoken

WORD = re.compile(r"[A-Za-z0-9]+")
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
PARENTHETICAL = re.compile(r"\([^)]*\)")
STOPWORDS = frozenset("""
a about after all allow allowed also an and any are as at be been before but by can could did do
does done for from had has have how i if in into is it its last many may me more most much my no not
of on or our over same should so some than that the their them then there these they this to under
up use used uses using was we were what when where which while who why will with would you your
service services s new get got""".split())


def words(text: str) -> list[str]:
    """Lower-case word tokens; CamelCase and snake_case split (MAX_RETRIES, maxRetries -> max retries)."""
    return [token.lower() for token in WORD.findall(CAMEL.sub(" ", text or ""))]


def stem(token: str) -> str:
    """A crude suffix stripper, enough to align retries/retry and limits/limit."""
    for suffix, replacement in (("ization", ""), ("ation", ""), ("ize", ""), ("ies", "y"), ("ied", "y"), ("ing", ""),
                                ("es", ""), ("ed", ""), ("s", "")):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: len(token) - len(suffix)] + replacement
    return token


# Words that describe the question or name kinds of sources, versions or environments rather
# than its subject. They do not count toward relevance; they still go to the hubs as typed.
META_TERMS = frozenset(stem(term) for term in """
true false claim include includes say says said given apply applies applied skill skills code
doc docs page pages wiki disagree disagreement agree environment branch release production prod
experiment experimental version""".split())


def inflections(token: str) -> list[str]:
    """Surface forms a literal (unstemmed) hub index needs to match: retry/retries, limit/limits."""
    forms = [token]
    if token.endswith("ies") and len(token) > 4:
        forms.append(token[:-3] + "y")
    elif token.endswith("y") and len(token) > 3:
        forms.append(token[:-1] + "ies")
    elif token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        forms.append(token[:-1])
    elif len(token) > 2 and not token.isdigit():
        forms.append(token + "s")
    return forms


def content_terms(text: str) -> list[str]:
    """Distinct stemmed non-stopword terms, first occurrence order."""
    return list(dict.fromkeys(stem(token) for token in words(text)
                              if token not in STOPWORDS and not token.isdigit()))


def subject_terms(query: str, excluded: set[str] = frozenset()) -> list[str]:
    """Content terms of the query's subject: parenthetical asides, meta words and `excluded`
    (release names, which are filters) removed."""
    return [term for term in content_terms(PARENTHETICAL.sub(" ", query))
            if term not in META_TERMS and term not in excluded]


def search_query(query: str) -> str:
    """The query as typed, plus inflections of its content words for a literal index."""
    extra = [form for token in words(query) if token not in STOPWORDS and token.isalpha()
             for form in inflections(token)[1:]]
    added = [form for form in dict.fromkeys(extra) if form not in set(words(query))]
    expanded = query if not added else f"{query} {' '.join(added)}"
    # The lab hub search contract accepts at most 64 distinct word tokens and
    # 4,000 characters. Long planning prompts plus inflections can exceed that
    # limit. Preserve original content words before spending space on variants.
    if len(set(words(expanded))) <= 64 and len(expanded) <= 4000:
        return expanded
    original = list(dict.fromkeys(words(query)))
    ordered = [w for w in original if w not in STOPWORDS] + [w for w in original if w in STOPWORDS] + added
    selected = []
    for token in dict.fromkeys(ordered):
        if len(selected) == 64 or len(' '.join([*selected, token])) > 4000:
            break
        selected.append(token)
    return ' '.join(selected)


def term_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in words(text):
        term = stem(token)
        counts[term] = counts.get(term, 0) + 1
    return counts


@lru_cache(maxsize=4)
def encoding(tokenizer_id: str):
    return tiktoken.get_encoding(tokenizer_id)


def token_count(text: str, tokenizer_id: str) -> int:
    return len(encoding(tokenizer_id).encode(text, disallowed_special=()))
