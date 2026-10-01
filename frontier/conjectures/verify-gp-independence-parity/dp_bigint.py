# Path DP over columns 0..n-1 with explicit boundary (u_0, v_0..v_{k-1}) and closure check,
# exact arithmetic via Kronecker packing into Python big ints. Gives I(GP(n,k)) for all n in [2k+1, NMAX].
import sys
def run(k, NMAX):
    B = 2*NMAX + 2           # bits per coefficient slot; every coefficient of any partial sum < 2^(2n)
    mask_slot = (1 << B) - 1
    S = 1 << (k+1)           # state bits: bit0 = u_i ; bit (1+j) = v_{i-k+1+j}, j=0..k-1 (bit k = newest v_i)
    totals = {n: 0 for n in range(2*k+1, NMAX+1)}
    # precompute transitions: for state s and choice (u',v') -> new state
    def trans(s, up, vp):
        ui = s & 1
        oldest = (s >> 1) & 1
        if up and ui: return None
        if up and vp: return None
        if vp and oldest: return None
        vs = s >> 1                      # k bits, bit0 = oldest
        vs = (vs >> 1) | (vp << (k-1))   # drop oldest, append newest at top
        return up | (vs << 1)
    for bu in (0, 1):
        for bvm in range(1 << k):
            bv = [(bvm >> j) & 1 for j in range(k)]
            if bu and bv[0]: continue
            # column 0
            s0 = bu | (bv[0] << k)
            cur = {s0: 1 << (B*(bu + bv[0]))}
            for i in range(0, NMAX):       # cur = states after column i
                n = i + 1
                if n >= 2*k+1:
                    # closure: u_{n-1} u_0 and v_{n-k+j} v_j
                    for s, val in cur.items():
                        if (s & 1) and bu: continue
                        if any(((s >> (1+j)) & 1) and bv[j] for j in range(k)): continue
                        totals[n] += val
                if n == NMAX: break
                nxt = {}
                col = i + 1
                for s, val in cur.items():
                    vchoices = (bv[col],) if col < k else (0, 1)
                    for vp in vchoices:
                        for up in (0, 1):
                            t = trans(s, up, vp)
                            if t is None: continue
                            w = up + vp
                            nxt[t] = nxt.get(t, 0) + (val << (B*w))
                cur = nxt
    out = {}
    for n, T in totals.items():
        coeffs = []
        while T:
            coeffs.append(T & mask_slot); T >>= B
        out[n] = coeffs
    return out

if __name__ == '__main__':
    k = int(sys.argv[1]); NMAX = int(sys.argv[2])
    res = run(k, NMAX)
    with open(f'/tmp/claude-0/conj/verify-gp-independence-parity/polys_k{k}.txt', 'w') as f:
        for n in sorted(res):
            f.write(f"{k} {n} " + ",".join(map(str, res[n])) + "\n")
    print('done', k, NMAX)
