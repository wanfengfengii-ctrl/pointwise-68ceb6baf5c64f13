"""Structural tests for the index primitives and the final answers.

These do *not* trust brute force: they check suffix-array ordering, LCP
correctness, maximality of the enumerated LCP intervals and, for the
public API, that each witness really has the reported length, support and
maximality, that ties go to the lexicographically smallest bytes and that
the witness occurrence is the smallest (doc, start) pair.

Run:  python3 -I tests/test_structure.py
"""

from __future__ import annotations

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import sharedphrases as sp  # noqa: E402


def naive_lcp(seq, i, j):
    n = len(seq)
    k = 0
    while i + k < n and j + k < n and seq[i + k] == seq[j + k]:
        k += 1
    return k


def check_index(seq):
    n = len(seq)
    sa = sp._suffix_array(seq)
    assert len(sa) == n and len(set(sa)) == n
    assert sa == sorted(range(n), key=lambda i: seq[i:]), (seq, sa)
    lcp = sp._lcp_array(seq, sa)
    for i in range(1, n):
        assert lcp[i] == naive_lcp(seq, sa[i - 1], sa[i]), (seq, i)

    intervals = sp._lcp_intervals(lcp)
    # Same depth -> disjoint; all intervals are left/right maximal.
    for depth, left, right in intervals:
        assert depth > 0 and left <= right < n
        word = tuple(seq[sa[left]:sa[left] + depth])
        for i in range(left, right + 1):
            assert tuple(seq[sa[i]:sa[i] + depth]) == word
        if left > 0:
            assert tuple(seq[sa[left - 1]:sa[left - 1] + depth]) != word
        if right + 1 < n:
            assert tuple(seq[sa[right + 1]:sa[right + 1] + depth]) != word

    # Maximal LCP intervals form an antichain at each depth and every
    # repeated substring is a prefix of some interval at least as deep.
    depths = sorted({d for d, _, _ in intervals})
    for d in depths:
        ranges = sorted((l, r) for dd, l, r in intervals if dd == d)
        for (_, r1), (l2, _) in zip(ranges, ranges[1:]):
            assert r1 < l2

    if n <= 40:
        repeated = {}
        for i in range(n):
            for length in range(1, n - i + 1):
                repeated.setdefault(tuple(seq[i:i + length]), 0)
                repeated[tuple(seq[i:i + length])] += 1
        for word in repeated:
            if repeated[word] < 2:
                continue
            assert any(
                d >= len(word)
                and tuple(seq[sa[l]:sa[l] + d][:len(word)]) == word
                for d, l, _ in intervals
            ), ("substring without an interval", seq, word)


def check_answer(documents, result):
    for slot, item in enumerate(result):
        k = slot + 2
        if item is None:
            # Verify no length-1..max substring reaches k distinct docs.
            pieces = {doc[s:s + 1] for doc in documents for s in range(len(doc))}
            for piece in pieces:
                assert sum(1 for d in documents if piece in d) < k, (
                    "expected None but found support", documents, k)
            continue

        d, s, length = item["doc"], item["start"], item["length"]
        piece = documents[d][s:s + length]
        assert len(piece) == length and length > 0
        support = sum(1 for doc in documents if piece in doc)
        assert support >= k, (documents, k, item, support)
        assert piece == min(documents[dd][ss:ss + length]
                            for dd, doc in enumerate(documents)
                            for ss in range(len(doc) - length + 1)
                            if sum(1 for x in documents if x.count(
                                documents[dd][ss:ss + length]) > 0) >= k), (
            "not the lexicographically smallest longest piece", documents, k)
        first = min((dd, ss) for dd, doc in enumerate(documents)
                    for ss in range(len(doc) - length + 1)
                    if doc[ss:ss + length] == piece)
        assert first == (d, s), (documents, k, item, first)
        # Nothing one byte longer may still reach k documents.
        for dd, doc in enumerate(documents):
            for ss in range(len(doc) - length):
                longer = doc[ss:ss + length + 1]
                assert sum(1 for x in documents if longer in x) < k, (
                    "not maximal", documents, k, item)


def main():
    rng = random.Random(424242)
    for _ in range(600):
        n = rng.randint(1, 16)
        seq = [rng.choice([0, 1, 2, 3]) for _ in range(n)]
        check_index(seq)
    for _ in range(100):
        n = rng.randint(1, 40)
        seq = [rng.randrange(6) for _ in range(n)]
        check_index(seq)

    cases = [
        [b"aba", b"cab", b"ba"],
        [b"abcabc", b"bcabca", b"cabcab"],
        [b"aabb", b"bbaa"],
        [b"x", b"qabc", b"abc"],
        [b"aaaa", b"aaa"],
        [b"ab", b"ab", b"ab", b"ab"],
        [b"", b"", b"abc"],
        [b"zzzz", b"yy"],
        [b"\x00\xff", b"\xff\x00", b"\x00\xff\x00"],
        [b"ababab", b"ab", b"zz"],
    ]
    for docs in cases:
        check_answer(docs, sp.profile(docs))

    for _ in range(300):
        count = rng.randint(2, 6)
        alphabet = rng.choice([b"ab", b"abc", b"abcd"])
        docs = []
        for _ in range(count):
            length = rng.randint(0, 7)
            docs.append(bytes(rng.choice(alphabet) for _ in range(length)))
        check_answer(docs, sp.profile(docs))

    print("OK: index primitives and answer invariants verified")


if __name__ == "__main__":
    main()
