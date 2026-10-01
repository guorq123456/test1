/* ext.c: for every odd m in [3, X] compute f(m) = least k>=1 with Jacobi(k,m) != 1,
   i.e. A112046((m-1)/2), straight from the definition (k = 1,2,3,... in turn).
   Records (a) the first m at which each value occurs, (b) every m with f(m)^2 > m.
   Then prints the first-occurrence indices i=(m-1)/2 sorted (= A112051) and checks
   them against 1, 3, 11, (p^2-1)/2 (p prime >= 7, p^2 <= X).
   usage: ./ext X nthreads                                         */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

static int jacobi(uint64_t a, uint64_t m) {   /* m odd >= 1 */
    int s = 1;
    a %= m;
    while (a) {
        int z = __builtin_ctzll(a);
        a >>= z;
        if ((z & 1) && ((m & 7) == 3 || (m & 7) == 5)) s = -s;
        uint64_t t = a; a = m; m = t;          /* swap */
        if ((a & 3) == 3 && (m & 3) == 3) s = -s;
        a %= m;
    }
    return m == 1 ? s : 0;
}

#define MAXV 200000
int main(int argc, char **argv) {
    uint64_t X = strtoull(argv[1], 0, 10);
    int nt = atoi(argv[2]);
    omp_set_num_threads(nt);
    static uint64_t first[MAXV];
    for (int v = 0; v < MAXV; v++) first[v] = UINT64_MAX;
    uint64_t nbad = 0, maxf = 0;
    #pragma omp parallel
    {
        uint64_t *lf = malloc(sizeof(uint64_t) * MAXV);
        for (int v = 0; v < MAXV; v++) lf[v] = UINT64_MAX;
        uint64_t lbad = 0, lmax = 0;
        #pragma omp for schedule(dynamic, 1)
        for (uint64_t blk = 0; blk < (X + (1ULL<<22)) >> 22; blk++) {
            uint64_t lo = blk << 22, hi = lo + (1ULL << 22);
            if (lo < 3) lo = 3;
            if (hi > X + 1) hi = X + 1;
            for (uint64_t m = lo | 1; m < hi; m += 2) {
                uint64_t k = 1;
                while (jacobi(k, m) == 1) k++;
                if (k >= MAXV) { fprintf(stderr, "value too big at m=%llu\n", (unsigned long long)m); exit(1); }
                if (m < lf[k]) lf[k] = m;
                if (k > lmax) lmax = k;
                if (k * k > m) {
                    #pragma omp critical
                    printf("f(m)^2 > m : m=%llu f=%llu\n", (unsigned long long)m, (unsigned long long)k);
                    lbad++;
                }
            }
        }
        #pragma omp critical
        {
            for (int v = 0; v < MAXV; v++) if (lf[v] < first[v]) first[v] = lf[v];
            nbad += lbad; if (lmax > maxf) maxf = lmax;
        }
        free(lf);
    }
    /* values that occur, with first index i = (m-1)/2 */
    int nvals = 0, ok = 1;
    uint64_t prevp = 0;
    FILE *fo = fopen("firstocc.txt", "w");
    for (uint64_t v = 2; v < MAXV; v++) if (first[v] != UINT64_MAX) {
        /* v must be prime */
        for (uint64_t d = 2; d * d <= v; d++) if (v % d == 0) { printf("composite value %llu!\n", (unsigned long long)v); ok = 0; }
        nvals++;
        uint64_t i = (first[v] - 1) / 2;
        fprintf(fo, "%d %llu %llu\n", nvals, (unsigned long long)v, (unsigned long long)i);
        uint64_t expect = (v == 2) ? 1 : (v == 3) ? 3 : (v == 5) ? 11 : (v * v - 1) / 2;
        if (i != expect) { printf("MISMATCH value %llu first index %llu expected %llu\n", (unsigned long long)v, (unsigned long long)i, (unsigned long long)expect); ok = 0; }
        prevp = v;
    }
    fclose(fo);
    /* every prime p with p^2 <= X must occur (it occurs at m = p^2) */
    for (uint64_t p = 2; p * p <= X; p++) {
        int isp = 1; for (uint64_t d = 2; d * d <= p; d++) if (p % d == 0) { isp = 0; break; }
        if (isp && first[p] == UINT64_MAX) { printf("prime %llu missing\n", (unsigned long long)p); ok = 0; }
    }
    printf("X=%llu: m with f(m)^2>m: %llu ; distinct values: %d ; max value %llu ; largest value %llu ; all first occurrences as predicted: %s\n",
           (unsigned long long)X, (unsigned long long)nbad, nvals, (unsigned long long)maxf, (unsigned long long)prevp, ok ? "YES" : "NO");
    return 0;
}
