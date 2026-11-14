"""Fictional supplier-contract text generator (ASCII, deterministic)."""

from __future__ import annotations

CLAUSE_DELIVERY = (
    "4. Delivery and Inspection. All deliveries shall conform to the "
    "specifications set out in Schedule 1 and shall be inspected within five "
    "(5) business days of receipt. The Buyer may reject any delivery that "
    "fails to conform to the said specifications."
)

CLAUSE_CONFIDENTIALITY = (
    "5. Confidentiality. The Supplier shall keep confidential all technical, "
    "commercial and financial information disclosed by the Buyer and shall "
    "use such information solely for the purposes of this Agreement. This "
    "obligation survives termination for a period of five (5) years."
)

CLAUSE_TERMINATION = (
    "9. Termination. Either party may terminate this Agreement for material "
    "breach upon thirty (30) days written notice if the breach remains "
    "uncured at the expiry of that period. Termination shall not affect any "
    "accrued rights or remedies of either party."
)

GOVERNING_LAW = {
    "delaware": (
        " This Agreement is governed by the laws of the State of Delaware, "
        "without regard to its conflict of law principles."
    ),
    "england": (
        " This Agreement is governed by the laws of England and Wales, "
        "without regard to its conflict of law principles."
    ),
    "singapore": (
        " This Agreement is governed by the laws of the Republic of Singapore "
        "and the courts of Singapore have exclusive jurisdiction."
    ),
}

REGIONS = ["delaware", "england", "singapore"]


def build_contract_texts():
    texts = []
    for i in range(60):
        region = REGIONS[i % 3]
        parts = [
            "SUPPLY AGREEMENT between Supplier "
            f"{i:02d} Ltd. (the Supplier) and Buyer {1000 + i} Holdings plc "
            "(the Buyer).",
            "1. Scope. The Supplier shall supply the goods described in each "
            "purchase order accepted by the Supplier.",
            CLAUSE_DELIVERY,
            CLAUSE_CONFIDENTIALITY,
        ]
        if i % 2 == 0:
            parts.append(CLAUSE_TERMINATION)
        if i % 5 == 0:
            # Boilerplate repeated inside one contract: still one source.
            parts.append("  Reaffirmation: " + CLAUSE_CONFIDENTIALITY)
        parts.append(GOVERNING_LAW[region])
        parts.append(
            " Purchase order reference PO-"
            f"{9000 + i:05d} covers quantities and unit prices agreed in "
            "writing."
        )
        texts.append("".join(parts))
    # Byte-identical copy from a second regional office: two distinct sources.
    texts.append(texts[0])
    return texts
