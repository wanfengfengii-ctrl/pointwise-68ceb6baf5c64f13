"""Find the longest byte string shared by at least k distinct documents.

Public API
----------
``profile(documents)``
    ``documents`` is a list of at least two ``bytes`` objects.  Empty
    documents and documents with identical contents are allowed.

    The result is a list with one item for each ``k`` from 2 through
    ``len(documents)``.  An item is either ``None`` (no non-empty common
    string exists in that many distinct documents) or a dictionary::

        {"length": L, "doc": d, "start": s}

    describing a longest non-empty contiguous byte string found in at
    least ``k`` different documents.  ``d`` and ``s`` are the
    lexicographically smallest ``(document, start-offset)`` pair among
    all occurrences of that string.

Algorithm and resource bounds
-----------------------------
Let N be the total number of input bytes plus the number of documents.
The documents are concatenated with one unique separator per document.
A suffix array and LCP array of that concatenation are built with prefix
doubling.  Maximal LCP intervals (the internal nodes of the generalized
suffix tree) are enumerated once.  For each interval we need:

* the number of *distinct* documents in its suffix-array range, obtained
  with an offline "last occurrence" Fenwick sweep, and
* the minimum (document, offset) occurrence, obtained with an iterative
  segment tree.

Thus no collection of substrings is materialised and the work is not
repeated for each k.  Prefix doubling costs O(N log^2 N); the remaining
steps cost O(N log N).  Time is O(N log^2(N+2)) and extra space is O(N).

Only the Python standard library is used.  The input objects are never
mutated.
"""

from __future__ import annotations

from typing import List, Optional, Sequence


_INF = 10 ** 40


def _suffix_array(seq: List[int]) -> List[int]:
    """Prefix-doubling suffix array for a list of comparable integers."""
    n = len(seq)
    if n == 0:
        return []
    if n == 1:
        return [0]

    sa = list(range(n))
    sa.sort(key=seq.__getitem__)

    rank = [0] * n
    r = 0
    rank[sa[0]] = 0
    for i in range(1, n):
        if seq[sa[i]] != seq[sa[i - 1]]:
            r += 1
        rank[sa[i]] = r

    if r == n - 1:
        return sa

    k = 1
    base = n + 1
    while k < n:
        rk = rank
        kk = k
        nn = n
        bb = base
        # Integer packing is faster than allocating a tuple per suffix.
        sa.sort(
            key=lambda i: (rk[i] + 1) * bb
            + (rk[i + kk] + 1 if i + kk < nn else 0)
        )

        new_rank = [0] * n
        r = 0
        prev = sa[0]
        prev_a = rk[prev]
        prev_b = rk[prev + kk] if prev + kk < nn else -1
        for idx in range(1, n):
            cur = sa[idx]
            cur_a = rk[cur]
            cur_b = rk[cur + kk] if cur + kk < nn else -1
            if cur_a != prev_a or cur_b != prev_b:
                r += 1
                prev_a = cur_a
                prev_b = cur_b
            new_rank[cur] = r
        rank = new_rank
        if r == n - 1:
            break
        k <<= 1

    return sa


def _lcp_array(seq: List[int], sa: List[int]) -> List[int]:
    """Kasai LCP array; lcp[i] = LCP(sa[i-1], sa[i]), lcp[0] = 0."""
    n = len(seq)
    rank = [0] * n
    for i, pos in enumerate(sa):
        rank[pos] = i

    lcp = [0] * n
    h = 0
    for i in range(n):
        ri = rank[i]
        if ri == 0:
            continue
        j = sa[ri - 1]
        while i + h < n and j + h < n and seq[i + h] == seq[j + h]:
            h += 1
        lcp[ri] = h
        if h:
            h -= 1
    return lcp


def _lcp_intervals(lcp: List[int]) -> List[tuple]:
    """Enumerate maximal LCP intervals as (depth, left_sa, right_sa).

    These intervals are exactly the internal nodes of the generalized
    suffix tree (the root at depth zero is omitted).  Intervals can be
    nested but intervals at the same depth are disjoint.
    """
    n = len(lcp)
    intervals: List[tuple] = []
    stack: List[tuple] = []  # (depth, leftmost suffix-array index)

    for i in range(1, n):
        h = lcp[i]
        left = i - 1
        while stack and stack[-1][0] > h:
            depth, old_left = stack.pop()
            intervals.append((depth, old_left, i - 1))
            left = old_left
        if h > 0 and (not stack or stack[-1][0] < h):
            stack.append((h, left))

    while stack:
        depth, left = stack.pop()
        intervals.append((depth, left, n - 1))

    return intervals


def _distinct_support(
    sa: List[int],
    doc_at_pos: List[int],
    intervals: List[tuple],
    doc_count: int,
    text_len: int,
) -> List[int]:
    """Distinct document count for every [left, right] suffix range.

    Standard offline sweep: when a document is seen again, only its most
    recent suffix-array position contributes to the Fenwick tree.
    """
    q = len(intervals)
    if q == 0:
        return []

    order = sorted(range(q), key=lambda idx: intervals[idx][2])
    bit = [0] * (text_len + 1)
    last = [-1] * doc_count
    result = [0] * q

    def add(pos: int, delta: int) -> None:
        i = pos + 1
        while i <= text_len:
            bit[i] += delta
            i += i & -i

    def prefix(end: int) -> int:
        # Number of marked positions in [0, end).
        total = 0
        i = end
        while i > 0:
            total += bit[i]
            i -= i & -i
        return total

    qi = 0
    for pos in range(text_len):
        doc = doc_at_pos[sa[pos]]
        if doc >= 0:
            old = last[doc]
            if old >= 0:
                add(old, -1)
            add(pos, 1)
            last[doc] = pos

        while qi < q and intervals[order[qi]][2] == pos:
            _, left, right = intervals[order[qi]]
            result[order[qi]] = prefix(right + 1) - prefix(left)
            qi += 1

    return result


def profile(documents: Sequence[bytes]) -> List[Optional[dict]]:
    """See the module docstring for the exact contract."""
    if not isinstance(documents, (list, tuple)):
        raise TypeError("documents must be a list of bytes")
    doc_count = len(documents)
    if doc_count < 2:
        raise ValueError("at least two documents are required")
    for doc in documents:
        if not isinstance(doc, bytes):
            raise TypeError("every document must be bytes")

    # Concatenate with unique separators and a final sentinel.  The sentinel
    # makes every suffix terminate without a special comparison case.
    text: List[int] = []
    doc_at_pos: List[int] = []
    doc_starts: List[int] = []
    for d, doc in enumerate(documents):
        doc_starts.append(len(text))
        text.extend(doc)
        doc_at_pos.extend([d] * len(doc))
        text.append(256 + d)  # unique separator, outside the byte range
        doc_at_pos.append(-1)
    text.append(-1)  # unique sentinel, below every byte and separator
    doc_at_pos.append(-1)

    n = len(text)
    sa = _suffix_array(text)
    if n == 0:
        return [None] * (doc_count - 1)

    lcp = _lcp_array(text, sa)
    intervals = _lcp_intervals(lcp)
    if not intervals:
        return [None] * (doc_count - 1)

    supports = _distinct_support(sa, doc_at_pos, intervals, doc_count, n)

    # Encode (document, offset) as one integer.  As B is larger than every
    # possible offset, integer order is exactly (document, offset) order.
    max_doc_len = max(len(doc) for doc in documents)
    B = max_doc_len + 1
    size = 1
    while size < n:
        size <<= 1
    seg = [_INF] * (2 * size)

    for rank_pos, pos in enumerate(sa):
        doc = doc_at_pos[pos]
        if doc >= 0:
            seg[size + rank_pos] = doc * B + (pos - doc_starts[doc])
    for i in range(size - 1, 0, -1):
        a = seg[i << 1]
        b = seg[i << 1 | 1]
        seg[i] = a if a < b else b

    def range_min(left: int, right: int) -> int:
        left += size
        right += size
        answer = _INF
        while left <= right:
            if left & 1:
                if seg[left] < answer:
                    answer = seg[left]
                left += 1
            if not (right & 1):
                if seg[right] < answer:
                    answer = seg[right]
                right -= 1
            left >>= 1
            right >>= 1
        return answer

    candidates = []  # (depth, left, right, support, minimum occurrence)
    for idx, (depth, left, right) in enumerate(intervals):
        support = supports[idx]
        if support >= 2:
            candidates.append((depth, left, right, support, range_min(left, right)))

    # Longer intervals are considered first.  For an equal depth, a smaller
    # suffix-array left endpoint is the lexicographically smaller byte string.
    candidates.sort(key=lambda item: (-item[0], item[1]))

    best: List[Optional[dict]] = [None] * (doc_count - 1)
    parent = list(range(doc_count + 2))  # skip-pointer DSU over k values

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != x:
            nxt = parent[x]
            parent[x] = root
            x = nxt
        return root

    for depth, _left, _right, support, occurrence in candidates:
        k = find(2)
        while k <= support:
            best[k - 2] = {
                "length": depth,
                "doc": occurrence // B,
                "start": occurrence % B,
            }
            parent[k] = find(k + 1)
            k = parent[k]

    return best
