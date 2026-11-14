"""Unit tests for sharedphrases.profile using only the standard library.

Run:  python3 -I -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bruteforce import brute_profile
from sharedphrases import profile


class ContractTests(unittest.TestCase):
    def test_documented_example(self):
        self.assertEqual(
            profile([b"aba", b"cab", b"ba"]),
            [
                {"length": 2, "doc": 0, "start": 0},
                {"length": 1, "doc": 0, "start": 0},
            ],
        )

    def test_result_length_matches_document_count(self):
        self.assertEqual(len(profile([b"a", b"b"])), 1)
        self.assertEqual(len(profile([b"a"] * 7)), 6)

    def test_empty_documents(self):
        self.assertEqual(profile([b"", b""]), [None])
        self.assertEqual(profile([b"", b"", b"abc"]), [None, None])
        self.assertEqual(
            profile([b"xy", b"", b"xy"]),
            [{"length": 2, "doc": 0, "start": 0}, None],
        )

    def test_identical_sources(self):
        self.assertEqual(
            profile([b"abc", b"abc", b"abc"]),
            [{"length": 3, "doc": 0, "start": 0}] * 2,
        )

    def test_containment(self):
        # "aaa" occurs in both; the longer b"aaaa" only in doc 0.
        self.assertEqual(
            profile([b"aaaa", b"aaa"]),
            [{"length": 3, "doc": 0, "start": 0}],
        )
        # A document fully contained in another gives that whole document.
        self.assertEqual(
            profile([b"bcd", b"abcdef"]),
            [{"length": 3, "doc": 0, "start": 0}],
        )

    def test_repeats_inside_one_document_give_one_support(self):
        # b"ab" appears three times in doc 0 and once in doc 1 -> support 2,
        # not 4, so only k=2 has an answer.
        self.assertEqual(
            profile([b"ababab", b"ab"]),
            [{"length": 2, "doc": 0, "start": 0}],
        )
        # Support must not be inflatable by repetition: with three documents
        # the repeated string still reaches only two of them.
        self.assertEqual(
            profile([b"ababab", b"ab", b"zz"]),
            [{"length": 2, "doc": 0, "start": 0}, None],
        )
        # Same string twice in one doc must not fabricate any support when the
        # other document lacks it.
        self.assertEqual(
            profile([b"zzzz", b"yy"]),
            [None],
        )

    def test_tie_break_is_smallest_bytes_then_earliest_witness(self):
        # b"aa" and b"bb" both have support 2 and length 2; b"aa" wins.
        self.assertEqual(
            profile([b"aabb", b"bbaa"]),
            [{"length": 2, "doc": 0, "start": 0}],
        )
        # Equal string chosen; witness is the lexicographically smallest
        # (doc, start) pair, skipping a document whose occurrence is later.
        self.assertEqual(
            profile([b"x", b"qabc", b"abc"]),
            [{"length": 3, "doc": 1, "start": 1}, None],
        )

    def test_no_common_bytes(self):
        self.assertEqual(profile([b"abc", b"def"]), [None])
        self.assertEqual(profile([b"a", b"b", b"c"]), [None, None])

    def test_input_not_mutated(self):
        docs = [bytearray(b"ab") if False else b"aba", b"cab", b"ba"]
        snapshot = list(docs)
        profile(docs)
        self.assertEqual(docs, snapshot)

    def test_non_bytes_rejected(self):
        with self.assertRaises(TypeError):
            profile(["ab", "cd"])
        with self.assertRaises(TypeError):
            profile(b"ab")
        with self.assertRaises(ValueError):
            profile([b"only"])

    def test_full_byte_range(self):
        docs = [bytes(range(256)), bytes(range(256)), b"\x00\xff"]
        self.assertEqual(
            profile(docs),
            [
                {"length": 256, "doc": 0, "start": 0},
                {"length": 1, "doc": 0, "start": 0},
            ],
        )


class BruteForceParityTests(unittest.TestCase):
    def test_fixed_suite(self):
        cases = [
            [b"aba", b"cab", b"ba"],
            [b"abcabc", b"bcabca", b"cabcab"],
            [b"prefix", b"prefixlong", b"longprefix"],
            [b"aab", b"aaab", b"aabb", b"b"],
            [b"\x00\xff", b"\xff\x00", b"\x00\xff\x00"],
            [b"abc", b"abc", b"abc", b"abc"],
            [b"", b"", b"", b""],
        ]
        for case in cases:
            self.assertEqual(profile(case), brute_profile(case), case)


if __name__ == "__main__":
    unittest.main()
