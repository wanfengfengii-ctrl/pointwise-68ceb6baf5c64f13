"""Resource-bound checks at the N = 200000 limit.

Asserts the implementation stays within the intended time/space envelope.
Run:  python3 -I tests/test_performance.py
"""

from __future__ import annotations

import os
import random
import sys
import time
import tracemalloc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sharedphrases import profile  # noqa: E402

TIME_LIMIT = 60.0          # seconds per case (generous on shared hardware)
PEAK_LIMIT = 250 * 1024 * 1024  # bytes


def measure(label, docs):
    n_bound = sum(len(d) for d in docs) + len(docs)
    assert n_bound <= 200000, (label, n_bound)
    start = time.perf_counter()
    result = profile(docs)
    elapsed = time.perf_counter() - start
    # Measure the peak separately: tracemalloc's bookkeeping slows execution
    # down by roughly an order of magnitude on this workload.
    tracemalloc.start()
    profile(docs)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"{label}: N={n_bound} time={elapsed:.2f}s peak={peak / 2**20:.1f}MiB "
          f"k=2 -> {result[0]}")
    assert elapsed < TIME_LIMIT, (label, elapsed)
    assert peak < PEAK_LIMIT, (label, peak)
    return result


def payload(total):
    """Build documents whose byte count plus document count is exactly total."""
    rng = random.Random(7)
    docs = []
    size = 4000
    while sum(len(d) for d in docs) + size + (len(docs) + 1) <= total:
        docs.append(bytes(rng.choice(b"acgt") for _ in range(size)))
    rest = total - sum(len(d) for d in docs) - len(docs)
    if rest > 0:
        # Adding a new document also raises the document count by one.
        docs.append(bytes(rng.choice(b"acgt") for _ in range(max(rest - 1, 0))))
    return docs


def main():
    measure("random-50-docs", payload(200000))

    unit = b"abcabcab"
    repeated = [(unit * 25)[:200] for _ in range(900)]
    budget = 200000 - sum(len(d) for d in repeated) - 900
    repeated[0] += b"a" * budget
    assert sum(len(d) for d in repeated) + 900 == 200000
    measure("repetitive-900-docs", repeated)

    measure("nested-a-runs", [b"a" * 198000, b"a" * 999])
    measure("two-large-random",
            [bytes(random.Random(1).randrange(256) for _ in range(99900)),
             bytes(random.Random(2).randrange(256) for _ in range(99900))])

    many_docs = [bytes([i % 256]) * 9 for i in range(19000)]
    assert sum(len(d) for d in many_docs) + len(many_docs) == 190000
    measure("many-small-docs", many_docs)

    empty = [b""] * 60000 + [b"abc", b"abd"]
    measure("many-empty-docs", empty)

    print("OK: all resource checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
