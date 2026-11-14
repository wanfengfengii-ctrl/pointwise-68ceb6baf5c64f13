"""Exhaustive brute-force reference used to cross-check sharedphrases.profile.

For small inputs this enumerates every substring of every document, records
the set of distinct documents containing it and the earliest (doc, start)
occurrence, then derives the exact answer described in the task.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def brute_profile(documents: List[bytes]) -> List[Optional[dict]]:
    """Direct exhaustive reference for at least two bytes documents."""
    doc_count = len(documents)
    if doc_count < 2:
        raise ValueError("at least two documents are required")

    occurrences: Dict[bytes, Tuple[int, int]] = {}
    supports: Dict[bytes, set] = {}

    for d, doc in enumerate(documents):
        seen_here: set = set()
        n = len(doc)
        for start in range(n):
            for length in range(1, n - start + 1):
                piece = doc[start:start + length]
                occ = occurrences.get(piece)
                if occ is None or (d, start) < occ:
                    occurrences[piece] = (d, start)
                if piece not in seen_here:
                    seen_here.add(piece)
                    supports.setdefault(piece, set()).add(d)

    winners: Dict[int, Tuple[bytes, Tuple[int, int]]] = {}
    for piece, docs_set in supports.items():
        support = len(docs_set)
        if support < 2:
            continue
        occurrence = occurrences[piece]
        for k in range(2, support + 1):
            current = winners.get(k)
            if current is None:
                winners[k] = (piece, occurrence)
                continue
            cur_piece, cur_occ = current
            better = (
                len(piece) > len(cur_piece)
                or (len(piece) == len(cur_piece) and piece < cur_piece)
                or (piece == cur_piece and occurrence < cur_occ)
            )
            if better:
                winners[k] = (piece, occurrence)

    result: List[Optional[dict]] = [None] * (doc_count - 1)
    for k in range(2, doc_count + 1):
        if k in winners:
            piece, (d, start) = winners[k]
            result[k - 2] = {"length": len(piece), "doc": d, "start": start}
    return result
