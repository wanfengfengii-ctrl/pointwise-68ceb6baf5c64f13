"""Timing and memory sanity check at the N=200000 limit."""

from __future__ import annotations

import os
import random
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sharedphrases import profile


def run(label, docs):
    total = sum(len(d) for d in docs)
    n_bound = total + len(docs)
    tracemalloc.start()
    t0 = time.perf_counter()
    result = profile(docs)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{label}: N={n_bound} time={elapsed:.2f}s peak={peak/1e6:.1f}MB "
          f"k=2:{result[0]}")
    assert elapsed < 120
    assert peak < 400e6


def main():
    rng = random.Random(7)
    total = 200000
    # 50 documents of ~4000 random bytes over a small alphabet.
    docs = []
    remaining = total
    for i in range(50):
        size = 4000
        docs.append(bytes(rng.choice(b"acgt") for _ in range(size)))
        remaining -= size
    run("random-dna-50docs", docs)

    # 1000 documents, highly repetitive, at the same total size.
    docs2 = []
    unit = b"abcabcab"
    for i in range(1000):
        docs2.append((unit * 25)[:200])
    remaining = total - sum(len(d) for d in docs2)
    docs2[0] += bytes(rng.choice(b"ab") for _ in range(remaining))
    run("repetitive-1000docs", docs2)

    # One huge document and one small one: maximises document-level overlap
    # work while keeping many nested LCP intervals.
    docs3 = [b"a" * 199000, b"a" * 999]
    run("nested-a-runs", docs3)


if __name__ == "__main__":
    main()
