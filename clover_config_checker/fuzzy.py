"""Fuzzy key-name matching for typo suggestions.

Combines difflib similarity with a small Levenshtein implementation so
'KextsToPatc' -> "similar to 'KextsToPatch'".
"""

import difflib


def levenshtein(a: str, b: str) -> int:
    """Classic edit distance, O(len(a)*len(b)) with two rows."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1,      # deletion
                           cur[j - 1] + 1,   # insertion
                           prev[j - 1] + cost))  # substitution
        prev = cur
    return prev[-1]


def similar(candidate: str, valid_names, max_suggestions: int = 3,
            cutoff: float = 0.72):
    """Return up to `max_suggestions` names from `valid_names` that look
    like typos of `candidate`, best first. Empty list if none are close."""
    candidate_l = candidate.lower()
    scored = []
    for name in valid_names:
        name_l = name.lower()
        # difflib ratio (0..1) on lowercase names
        ratio = difflib.SequenceMatcher(None, candidate_l, name_l).ratio()
        # Levenshtein-derived similarity, handles transpositions poorly but
        # catches short-name edits difflib sometimes misses
        dist = levenshtein(candidate_l, name_l)
        lev_ratio = 1.0 - dist / max(len(candidate_l), len(name_l), 1)
        score = max(ratio, lev_ratio)
        # substring bonus: 'kextpatches' vs 'KernelAndKextPatches'
        if len(candidate_l) >= 5 and candidate_l in name_l:
            score = max(score, 0.8)
        if score >= cutoff:
            scored.append((score, name))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [name for _, name in scored[:max_suggestions]]


def format_suggestions(suggestions) -> str:
    if not suggestions:
        return ''
    return ' (similar to ' + ', '.join("'%s'" % s for s in suggestions) + ')'
