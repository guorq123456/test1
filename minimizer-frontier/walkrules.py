"""Rules based on the +-1 walk of the alternating-flipped window f (bits of the lift U)."""
import sys, numpy as np
from pnu import excess, alt_vec

def walk(v):
    y = [0]
    for b in v: y.append(y[-1] + (2 * b - 1))
    return y

def mk(rule, nu):
    h = np.zeros(1 << nu, dtype=np.int64)
    for W in range(1 << nu):
        v = alt_vec(W, nu); y = walk(v)
        M, mn, end = max(y), min(y), y[-1]
        iM = y.index(M); imn = y.index(mn)          # first occurrences
        iM2 = len(y) - 1 - y[::-1].index(M); imn2 = len(y) - 1 - y[::-1].index(mn)  # last occurrences
        q = M + mn - end
        if rule == 'q>0': r = q > 0
        elif rule == 'q>=0': r = q >= 0
        elif rule == 'q>0|first': r = q > 0 or (q == 0 and iM < imn)
        elif rule == 'q>0|firstrev': r = q > 0 or (q == 0 and iM > imn)
        elif rule == 'q>0|last': r = q > 0 or (q == 0 and iM2 < imn2)
        elif rule == 'q>0|lastrev': r = q > 0 or (q == 0 and iM2 > imn2)
        elif rule == 'q>-1': r = q > -1
        elif rule == 'q>1': r = q > 1
        elif rule == 'maj': r = end > 0
        elif rule == 'M>-mn': r = M > -mn
        elif rule == 'M>=-mn': r = M >= -mn
        elif rule == 'M>-mn|first': r = M > -mn or (M == -mn and iM < imn)
        elif rule == 'M>-mn|firstrev': r = M > -mn or (M == -mn and iM > imn)
        elif rule == 'M>-mn|last': r = M > -mn or (M == -mn and iM2 < imn2)
        elif rule == 'M>-mn|lastrev': r = M > -mn or (M == -mn and iM2 > imn2)
        elif rule == 'argmax<argmin': r = iM < imn
        elif rule == 'argmax>argmin': r = iM > imn
        elif rule == 'argmax2<argmin2': r = iM2 < imn2
        elif rule == 'argmax2>argmin2': r = iM2 > imn2
        elif rule == 'M-end > -mn': r = (M - end) > (-mn)        # max above end vs min below start
        elif rule == 'M-end >= -mn': r = (M - end) >= (-mn)
        elif rule == 'M > end-mn': r = M > end - mn
        elif rule == 'M >= end-mn': r = M >= end - mn
        h[W] = 1 if r else 0
    return h

if __name__ == '__main__':
    rules = ['maj', 'q>0', 'q>=0', 'q>0|first', 'q>0|firstrev', 'q>0|last', 'q>0|lastrev', 'q>-1', 'q>1',
             'M>-mn', 'M>=-mn', 'M>-mn|first', 'M>-mn|firstrev', 'M>-mn|last', 'M>-mn|lastrev',
             'argmax<argmin', 'argmax>argmin', 'argmax2<argmin2', 'argmax2>argmin2',
             'M-end > -mn', 'M-end >= -mn', 'M > end-mn', 'M >= end-mn']
    nus = [1, 3, 5, 7, 9, 11]
    for rule in rules:
        res = [excess(mk(rule, nu), nu) for nu in nus]
        print(f"{rule:18s} excess nu={nus}: {res}")
