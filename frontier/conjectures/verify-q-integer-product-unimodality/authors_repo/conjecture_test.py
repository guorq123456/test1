#!/usr/bin/env python3
"""
Computational verification of Conjecture 2.5 (Bergeron-Ceballos-Kustner):
    The q-Fibonomial coefficients [m+n choose n]_F are unimodal for all m, n >= 1.

The unimodality check exploits the known symmetry of [m+n choose n]_F by
verifying only that the first half of the coefficient sequence is non-decreasing.

Coded with the assistance of Claude (Anthropic).

Usage:
    python3 conjecture_test.py [max_sum]   # default max_sum=26
"""

import os
import sys
import time
import multiprocessing as mp
from typing import List, Tuple

from fibonomial_test import make_fibonacci, fibonomial_poly, is_unimodal


def run_grid(max_sum: int, F: List[int]) -> List[Tuple[int, int]]:
    """Test all (m, n) with n >= 1, m >= n, m+n <= max_sum."""
    failures = []
    print(f"Testing [m+n choose n]_F for unimodality, m >= n >= 1, m+n <= {max_sum}")
    print(f"  {'m+n':>4}  {'m':>3}  {'n':>3}  {'deg':>10}  {'t':>7}  result")
    print(f"  {'-'*50}")
    for s in range(2, max_sum + 1):
        for n in range(1, s // 2 + 1):
            m = s - n
            t0 = time.perf_counter()
            poly = fibonomial_poly(m, n, F)
            elapsed = time.perf_counter() - t0
            status = "ok" if is_unimodal(poly) else "FAIL"
            if status == "FAIL":
                failures.append((m, n))
            print(f"  {s:>4}  {m:>3}  {n:>3}  {len(poly)-1:>10,}  {elapsed:>6.3f}s  {status}")
    return failures


def _worker(args: tuple) -> dict:
    m, n, F = args
    t0 = time.perf_counter()
    poly = fibonomial_poly(m, n, F)
    return {"m": m, "n": n, "deg": len(poly) - 1,
            "uni": is_unimodal(poly), "elapsed": time.perf_counter() - t0}


def run_large_pairs(pairs: List[Tuple[int, int]], F: List[int]) -> List[Tuple[int, int]]:
    """Test specific large (m, n) pairs in parallel."""
    failures = []
    print(f"\nTesting large pairs ({os.cpu_count()} workers)")
    print(f"  {'m':>3}  {'n':>3}  {'deg':>12}  {'t':>7}  result")
    print(f"  {'-'*42}")
    with mp.Pool(os.cpu_count()) as pool:
        results = pool.map(_worker, [(m, n, F) for m, n in pairs])
    for r in results:
        status = "ok" if r["uni"] else "FAIL"
        if not r["uni"]:
            failures.append((r["m"], r["n"]))
        print(f"  {r['m']:>3}  {r['n']:>3}  {r['deg']:>12,}  {r['elapsed']:>6.3f}s  {status}")
    return failures


if __name__ == "__main__":
    max_sum = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    F = make_fibonacci(max(max_sum + 3, 40))

    grid_failures = run_grid(max_sum, F)

    # For each diagonal k=11..16, test (k,k), (k+1,k), (k+2,k) to cover
    # both same-parity and off-diagonal cases.
    large_pairs = [
        (11, 11), (12, 11), (13, 11),
        (12, 12), (13, 12), (14, 12),
        (13, 13), (14, 13), (15, 13),
        (14, 14), (15, 14), (16, 14),
        (15, 15), (16, 15), (17, 15),
        (16, 16), (17, 16),
    ]
    large_failures = run_large_pairs(large_pairs, F)

    all_failures = grid_failures + large_failures
    print(f"\nResult: {'ALL OK' if not all_failures else f'{len(all_failures)} FAILURE(S): {all_failures}'}")
