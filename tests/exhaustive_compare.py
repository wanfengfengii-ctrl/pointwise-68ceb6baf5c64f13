"""Randomised exhaustive cross-check of sharedphrases.profile.

Every generated case is compared against bruteforce.brute_profile, which
enumerates all substrings.  The generator deliberately mixes tiny alphabets
(many repeats), long identical documents, documents contained in others,
empty documents, non-ASCII bytes and duplicate sources.

Run directly:  python3 -I tests/exhaustive_compare.py
"""

from __future__ import annotations

import itertools
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bruteforce import brute_profile  # noqa: E402
from sharedphrases import profile  # noqa: E402

ALPHABETS = [b"ab", b"abc", b"a", b"abcd", bytes(range(256))]


def fixed_cases():
    yield [b"aba", b"cab", b"ba"]  # the task's worked example
    yield [b"abc", b"abc"]
    yield [b"aaa", b"aa"]
    yield [b"aa", b"aaa", b"aaa"]
    yield [b"", b""]
    yield [b"", b"abc"]
    yield [b"abc", b"", b""]
    yield [b"x", b"y", b"z"]
    yield [b"ab", b"ab", b"ab", b"ab"]
    yield [b"abcabc", b"bcabca", b"cabcab"]
    yield [b"\x00\xff", b"\xff\x00", b"\x00\xff\x00"]
    yield [b"prefix", b"prefixlong", b"longprefix"]
    yield [b"containment", b"contain", b"tainmen"]
    yield [b"aaaab", b"aaab", b"aab", b"ab"]
    yield [b"ababab", b"ab", b"zz"]


def random_case(rng: random.Random):
    alphabet = rng.choice(ALPHABETS)
    count = rng.randint(2, 6)
    docs = []
    for _ in range(count):
        if rng.random() < 0.12:
            docs.append(b"")
            continue
        length = rng.randint(0, 8)
        docs.append(bytes(rng.choice(alphabet) for _ in range(length)))
    return docs


def all_short_cases():
    """Every multiset of short documents over a two-letter alphabet."""
    pieces_by_limit = {}
    for limit in (3, 4):
        pieces = [b""]
        for length in range(1, limit + 1):
            pieces.extend(
                bytes(combo) for combo in itertools.product(b"ab", repeat=length)
            )
        pieces_by_limit[limit] = pieces
    for count, limit in ((2, 4), (3, 4), (4, 4), (5, 3)):
        for docs in itertools.combinations_with_replacement(
                pieces_by_limit[limit], count):
            yield list(docs)


def compare(docs, failures):
    expected = brute_profile(list(docs))
    actual = profile(list(docs))
    if expected != actual:
        failures.append((docs, expected, actual))


def run(random_cases: int = 2000, seed: int = 20261114):
    """Return (cases_checked, failures)."""
    failures = []
    checked = 0

    for docs in fixed_cases():
        compare(docs, failures)
        checked += 1

    for docs in all_short_cases():
        compare(docs, failures)
        checked += 1

    rng = random.Random(seed)
    for _ in range(random_cases):
        compare(random_case(rng), failures)
        checked += 1

    return checked, failures


def main():
    checked, failures = run()
    if failures:
        for docs, expected, actual in failures[:5]:
            print("MISMATCH", docs)
            print("  expected", expected)
            print("  actual  ", actual)
        raise SystemExit(f"{len(failures)} mismatches out of {checked} cases")

    # Input must never be mutated by the API.
    original = [b"aba", b"cab", b"ba"]
    snapshot = list(original)
    profile(original)
    assert original == snapshot, "input was mutated"

    print(f"OK: {checked} cases agree exactly with brute force")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
