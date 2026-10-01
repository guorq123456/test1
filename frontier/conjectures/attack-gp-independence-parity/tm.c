// Transfer-matrix computation of I(GP(m,k),x) for all 2k+1 <= m <= N, modulo several moduli.
// State after column j: bits: bit0 = u_j, bit1 = v_j, bit(1+i) = v_{j-i}, i=1..k-1  (k+1 bits total).
// Transition A(j-1) -> B(j): B.v_{j-i} = A.v_{j-i} for i=1..k-1 ; constraints: not(u_j & u_{j-1}), not(u_j & v_j), not(v_j & v_{j-k}).
// weight x^{u_j+v_j}.  I(GP(m,k)) = Tr(T^m) for m >= 2k+1.
// Moduli: 2^64 (wraparound) and NP primes near 2^62. Output: for each m, coefficient residues.
// Parallelized over start states with OpenMP.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint64_t u64;
#define NP 7
static const u64 P[NP] = {4611686018427387847ULL, 4611686018427387817ULL, 4611686018427387787ULL, 4611686018427387761ULL, 4611686018427387751ULL, 4611686018427387737ULL, 4611686018427387733ULL};
// NOTE: primality of these is checked externally; CRT uses whatever is printed.
#define NM (NP+1)
static inline u64 addm(u64 a, u64 b, u64 p){ u64 c=a+b; return c>=p? c-p : c; }

int main(int argc, char**argv){
  int k = atoi(argv[1]); int N = atoi(argv[2]);
  int nb = k+1; int S = 1<<nb;
  // successor list
  int *nsucc = calloc(S,sizeof(int)); int (*succ)[4] = malloc(S*sizeof(*succ)); int (*sw)[4]=malloc(S*sizeof(*sw));
  int *valid = calloc(S,sizeof(int));
  for(int a=0;a<S;a++){ valid[a] = !((a&1)&&((a>>1)&1)); }
  for(int a=0;a<S;a++){
    if(!valid[a]) continue;
    int uprev = a&1; int vold = (a>>k)&1; // v_{j-k} is A's bit (1+(k-1)) = bit k  (A has v_{j-1} at bit1 ... v_{j-1-(k-1)}=v_{j-k} at bit k)
    // B history: B.bit(1+i) = v_{j-i} = A.bit(1+(i-1)) = A.bit(i) for i=1..k-1  => B bits 2..k from A bits 1..k-1
    int hist = 0; for(int i=1;i<=k-1;i++){ hist |= ((a>>i)&1) << (i+1); }
    for(int uj=0;uj<2;uj++) for(int vj=0;vj<2;vj++){
      if(uj && uprev) continue; if(uj&&vj) continue; if(vj && vold) continue;
      int b = hist | uj | (vj<<1);
      succ[a][nsucc[a]] = b; sw[a][nsucc[a]] = uj+vj; nsucc[a]++;
    }
  }
  int D = N+2; // degree bound
  // result[m][d][mod]
  u64 *res = calloc((size_t)(N+1)*D*NM, sizeof(u64));
  #pragma omp parallel
  {
    u64 *cur = malloc((size_t)S*D*NM*sizeof(u64));
    u64 *nxt = malloc((size_t)S*D*NM*sizeof(u64));
    u64 *loc = calloc((size_t)(N+1)*D*NM, sizeof(u64));
    #pragma omp for schedule(dynamic,1)
    for(int a=0;a<S;a++){
      if(!valid[a]) continue;
      memset(cur,0,(size_t)S*D*NM*sizeof(u64));
      // initial: state a at "column -1"... we start with vector e_a and weight 1; after m steps, entry a gives (T^m)_{aa}
      cur[(size_t)a*D*NM + 0] = 1; for(int q=1;q<NM;q++) cur[(size_t)a*D*NM+q]=1;
      for(int m=1;m<=N;m++){
        int dmax = m; if(dmax>D-1) dmax=D-1;
        memset(nxt,0,(size_t)S*D*NM*sizeof(u64));
        for(int s=0;s<S;s++){
          if(!valid[s]) continue;
          u64 *src = cur + (size_t)s*D*NM;
          // check nonzero quickly: skip
          for(int t=0;t<nsucc[s];t++){
            int b=succ[s][t], w=sw[s][t];
            u64 *dst = nxt + (size_t)b*D*NM + (size_t)w*NM;
            for(int d=0; d+w<=dmax; d++){
              u64 *sp = src + (size_t)d*NM; u64 *dp = dst + (size_t)d*NM;
              dp[0] += sp[0];
              for(int q=0;q<NP;q++) dp[q+1] = addm(dp[q+1], sp[q+1], P[q]);
            }
          }
        }
        u64 *tmp=cur; cur=nxt; nxt=tmp;
        // record diagonal
        u64 *src = cur + (size_t)a*D*NM; u64 *dst = loc + (size_t)m*D*NM;
        for(int d=0; d<=dmax; d++){ dst[d*NM] += src[d*NM]; for(int q=0;q<NP;q++) dst[d*NM+q+1]=addm(dst[d*NM+q+1],src[d*NM+q+1],P[q]); }
      }
    }
    #pragma omp critical
    {
      for(size_t i=0;i<(size_t)(N+1)*D;i++){ res[i*NM]+=loc[i*NM]; for(int q=0;q<NP;q++) res[i*NM+q+1]=addm(res[i*NM+q+1],loc[i*NM+q+1],P[q]); }
    }
    free(cur); free(nxt); free(loc);
  }
  // output
  for(int m=2*k+1;m<=N;m++){
    int dmax = m; if(dmax>D-1) dmax=D-1;
    // find top nonzero degree
    int top=0; for(int d=0;d<=dmax;d++){ int nz=0; for(int q=0;q<NM;q++) if(res[((size_t)m*D+d)*NM+q]) nz=1; if(nz) top=d; }
    printf("%d %d %d", k, m, top);
    for(int d=0;d<=top;d++){ printf(" "); for(int q=0;q<NM;q++) printf("%s%llu", q?",":"", (unsigned long long)res[((size_t)m*D+d)*NM+q]); }
    printf("\n");
  }
  return 0;
}
