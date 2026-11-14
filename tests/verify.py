"""Single executable verification entry point.

Runs, in order:

1. stdlib unit tests (tests/test_profile.py),
2. exhaustive comparison against the brute-force reference
   (tests/exhaustive_compare.py: every short multiset over {a,b} up to
   length 4 with 2-4 documents, plus 2000 randomised cases),
3. structural invariants of the suffix array / LCP / interval layer and of
   the public answers (tests/test_structure.py),
4. the business demo, including its independent re-verification.

Exit status 0 means every check passed.  Run:

    python3 -I tests/verify.py
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "demo"))


def run_unit_tests():
    loader = unittest.TestLoader()
    suite = loader.discover(HERE, pattern="test_profile.py")
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(f"[1/4] unit tests: {result.testsRun} passed")


def run_exhaustive():
    import exhaustive_compare
    checked, failures = exhaustive_compare.run()
    if failures:
        for docs, expected, actual in failures[:5]:
            print("MISMATCH", docs, expected, actual)
        raise SystemExit(1)
    print(f"[2/4] exhaustive comparison: {checked} cases match brute force")


def run_structural():
    import test_structure
    test_structure.main()
    print("[3/4] structural invariants verified")


def run_demo():
    import business_demo
    status = business_demo.main()
    if status not in (0, None):
        raise SystemExit(status)
    print("[4/4] business demo completed and re-verified")


def main():
    run_unit_tests()
    run_exhaustive()
    run_structural()
    run_demo()
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
