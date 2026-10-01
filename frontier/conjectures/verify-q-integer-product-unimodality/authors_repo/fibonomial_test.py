#!/usr/bin/env python3
"""
Core utilities for q-Fibonomial coefficient computation.

    F_0=0, F_1=1, F_k = F_{k-1} + F_{k-2}
    [r]_q = 1 + q + ... + q^{r-1}
    [m+n choose n]_F = prod_{i=1}^n [F_{m+i}]_q / prod_{i=1}^n [F_i]_q

Coded with the assistance of Claude (Anthropic).
"""

import numpy as np
from typing import List


def make_fibonacci(max_idx: int) -> List[int]:
    F = [0] * (max_idx + 1)
    if max_idx >= 1:
        F[1] = 1
    for i in range(2, max_idx + 1):
        F[i] = F[i - 1] + F[i - 2]
    return F


def poly_mul_all_ones(P: List[int], r: int) -> List[int]:
    """Multiply P by [r]_q = 1 + q + ... + q^{r-1} via sliding-window prefix sum."""
    n = len(P)
    result_len = n + r - 1
    expected_sum = sum(P) * r

    try:
        P64 = np.array(P, dtype=np.int64)
        prefix64 = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(P64, out=prefix64[1:])
        j = np.arange(result_len, dtype=np.int64)
        hi = np.minimum(j + 1, n).astype(np.intp)
        lo = np.maximum(j - r + 1, 0).astype(np.intp)
        result64 = prefix64[hi] - prefix64[lo]
        result_list = result64.tolist()
        if sum(result_list) == expected_sum:
            return result_list
    except (OverflowError, ValueError):
        pass

    # Python bigint fallback
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + P[i]
    result = [0] * result_len
    for j in range(result_len):
        result[j] = prefix[min(j + 1, n)] - prefix[max(j - r + 1, 0)]
    return result


def poly_div_geometric(P: List[int], k: int) -> List[int]:
    """Exact division of P by [k]_q = 1 + q + ... + q^{k-1}."""
    if k == 1:
        return list(P)
    n = len(P)
    deg_Q = n - k
    if deg_Q < 0:
        raise ValueError(f"Degree of divisor {k-1} exceeds degree of P {n-1}")
    R = [0] * (n + 1)
    R[0] = -P[0]
    for j in range(1, n):
        R[j] = P[j - 1] - P[j]
    R[n] = P[n - 1]
    Q = [0] * (deg_Q + 1)
    for m in range(deg_Q + 1):
        Q[m] = (Q[m - k] if m >= k else 0) - R[m]
    return Q


def fibonomial_poly(m: int, n: int, F: List[int]) -> List[int]:
    """Compute [m+n choose n]_F via interleaved multiply-divide."""
    P = [1]
    for i in range(1, n + 1):
        P = poly_mul_all_ones(P, F[m + i])
        fi = F[i]
        if fi > 1:
            P = poly_div_geometric(P, fi)
    return P


def is_unimodal(coeffs: List[int]) -> bool:
    """Check unimodality, assuming the polynomial is symmetric."""
    mid = (len(coeffs) - 1) // 2
    for i in range(mid):
        if coeffs[i] > coeffs[i + 1]:
            return False
    return True
