# sharedphrases

Find the longest original byte run shared by at least *k* **distinct**
documents, for every *k* from 2 to the number of documents — in one pass
over a suffix-array index, using only the Python standard library.

```python
from sharedphrases import profile

profile([b"aba", b"cab", b"ba"])
# [{'length': 2, 'doc': 0, 'start': 0},   # k = 2 -> longest shared run
#  {'length': 1, 'doc': 0, 'start': 0}]   # k = 3 -> longest run in all three
```

## Contract

* `documents`: a list of at least two `bytes` objects. Empty documents and
  documents with identical contents are allowed.
* `N = total bytes + number of documents`, with `N <= 200000`.
* Returns a list with `len(documents) - 1` items, one per `k = 2..len(documents)`.
  Each item is `None` (no non-empty byte run occurs in `k` distinct documents)
  or `{"length": L, "doc": d, "start": s}`.
* A run is a contiguous slice **inside one document**; it never crosses a
  document boundary.
* Support counts **distinct documents**. The same piece occurring many times
  inside one document adds support 1 for that document.
* Ties on length are resolved by the smallest byte string in lexicographic
  (`bytes`) order. The witness `(d, s)` is the smallest `(doc, start)`
  lexicographic pair among all occurrences of the chosen string.
* The input is never mutated.

## Example of the tricky cases

| input | k=2 | k=3 |
|---|---|---|
| `[b"aba", b"cab", b"ba"]` | `b"ab"` @ (0,0) | `b"a"` @ (0,0) |
| `[b"abc", b"abc"]` | `b"abc"` @ (0,0) | – |
| `[b"", b""]` | `None` | – |
| `[b"ababab", b"ab", b"zz"]` | `b"ab"` @ (0,0) | `None` (repeat ≠ extra source) |
| `[b"aaaa", b"aaa"]` | `b"aaa"` @ (0,0) (containment) | – |

## Algorithm

1. Concatenate the documents with one unique separator each (byte value
   `256 + d`) and a final sentinel (−1), so suffixes never run past the end
   and no substring can cross a boundary.
2. Build a suffix array by prefix doubling and the LCP array with Kasai.
3. Enumerate all **maximal LCP intervals** (internal nodes of the generalized
   suffix tree) once. Every repeated substring is a prefix of the string
   represented by some interval, so no substring set is stored.
4. For each interval compute, in a single offline sweep, the number of
   *distinct documents* in its suffix-array range (last-occurrence
   Fenwick tree), and the minimum `(doc, start)` occurrence
   (iterative segment tree).
5. Resolve all `k` at once: sort candidates by decreasing length and
   increasing left suffix-array index (= lexicographic order), then fill
   each not-yet-answered `k` up to the candidate's support with a
   skip-pointer disjoint-set. Each `k` is answered exactly once.

Complexity: O(N log²(N+2)) time and O(N) extra space; the index is built
once, not per `k`.

## Layout

```
sharedphrases.py            analysis core (public API + index primitives)
bruteforce.py               exhaustive O(sum |doc|²) reference
tests/verify.py             one-command verification (all of the below)
tests/exhaustive_compare.py all short multisets + randomised differential test
tests/test_structure.py     suffix array / LCP / interval invariants
tests/test_profile.py       stdlib unit tests for the contract
tests/test_performance.py   N = 200000 time and peak-memory checks
demo/business_demo.py       business demo over a JSONL contract corpus
demo/contract_text.py       deterministic corpus text generator
demo/make_corpus.py         writes data/supplier_contracts.jsonl
data/supplier_contracts.jsonl  61 fictional supplier contracts
.pointwise-runtime.json     machine-readable runnable entry points
```

## Running

```bash
python3 -I tests/verify.py           # everything, exits 0 on success
python3 -I demo/business_demo.py     # business demo only
python3 -I tests/exhaustive_compare.py
python3 -I tests/test_performance.py
```

The entry points are also declared in `.pointwise-runtime.json`.
