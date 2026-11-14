"""Generate the fictional supplier-contract corpus used by the demo.

Output: data/supplier_contracts.jsonl with one {"id", "text"} object per line.
The corpus is deterministic; re-running regenerates identical bytes.

Run:  python3 -I demo/make_corpus.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contract_text import build_contract_texts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "supplier_contracts.jsonl")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    texts = build_contract_texts()
    with open(OUT, "w", encoding="ascii", newline="\n") as handle:
        for index, text in enumerate(texts):
            handle.write(json.dumps({"id": f"contract-{index:03d}",
                                     "text": text},
                                    ensure_ascii=True) + "\n")
    total = sum(len(t.encode("ascii")) for t in texts)
    print(f"wrote {len(texts)} contracts / {total} bytes to {OUT}")


if __name__ == "__main__":
    main()
