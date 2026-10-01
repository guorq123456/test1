"""Battery of window-intrinsic anchor rules: c(W) = (anchor position in W) mod 2 (and variants)."""
import sys, numpy as np
from w2 import charged_count, bound_charged

def W_bits(W, n): return format(W, f'0{n}b')

def rules():
    R = {}
    def rots(s): return [s[i:] + s[:i] for i in range(len(s))]
    R['minrot']  = lambda s: min(range(len(s)), key=lambda i: s[i:] + s[:i])
    R['maxrot']  = lambda s: max(range(len(s)), key=lambda i: s[i:] + s[:i])
    R['minrot_last'] = lambda s: max(i for i in range(len(s)) if s[i:] + s[:i] == min(rots(s)))
    R['minsuf']  = lambda s: min(range(len(s)), key=lambda i: s[i:])
    R['maxsuf']  = lambda s: max(range(len(s)), key=lambda i: s[i:])
    R['minsuf_pad1'] = lambda s: min(range(len(s)), key=lambda i: s[i:] + '1' * len(s))
    R['minpre_colex'] = lambda s: min(range(len(s)), key=lambda i: s[:i + 1][::-1])
    R['maxpre_colex'] = lambda s: max(range(len(s)), key=lambda i: s[:i + 1][::-1])
    R['first0'] = lambda s: s.find('0') if '0' in s else 0
    R['last0']  = lambda s: s.rfind('0') if '0' in s else 0
    R['first1'] = lambda s: s.find('1') if '1' in s else 0
    R['last1']  = lambda s: s.rfind('1') if '1' in s else 0
    R['first01'] = lambda s: s.find('01') if '01' in s else 0
    R['first10'] = lambda s: s.find('10') if '10' in s else 0
    R['last01'] = lambda s: s.rfind('01') if '01' in s else 0
    R['last10'] = lambda s: s.rfind('10') if '10' in s else 0
    def longest0(s, left=True):
        best, bi, i = -1, 0, 0
        while i < len(s):
            if s[i] == '0':
                j = i
                while j < len(s) and s[j] == '0': j += 1
                if (j - i > best) or (j - i == best and not left): best, bi = j - i, i
                i = j
            else: i += 1
        return bi
    R['longest0_left'] = lambda s: longest0(s, True)
    R['longest0_right'] = lambda s: longest0(s, False)
    R['minrot_alt'] = lambda s: min(range(len(s)), key=lambda i: ''.join(str(int(ch) ^ (t & 1)) for t, ch in enumerate(s[i:] + s[:i])))
    return R

if __name__ == '__main__':
    ns = [2, 4, 6, 8, 10, 12]
    R = rules()
    for name, rule in R.items():
        for variant in ['par', 'par^1', 'par^x0', 'par^xlast']:
            res = []
            for n in ns:
                c = np.zeros(1 << n, dtype=np.int64)
                for W in range(1 << n):
                    s = W_bits(W, n); a = rule(s)
                    v = a & 1
                    if variant == 'par^1': v ^= 1
                    elif variant == 'par^x0': v ^= int(s[0])
                    elif variant == 'par^xlast': v ^= int(s[-1])
                    c[W] = v
                res.append('Y' if charged_count(c, n) == bound_charged(n) else '.')
            if 'Y' in res: print(f"{name:16s} {variant:10s} n={ns}: {' '.join(res)}")
    print("done (only rules with at least one Y printed)")
