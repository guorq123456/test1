// Half-grid DP for rook placements on permutation grids.
// half_vectors(n, h, set_mask, colidx, K, out, seqs):
//   enumerates all orderings (lexicographic) of the h elements of set_mask as
//   rows 0..h-1 of an n x n permutation grid, runs the row DP, and for each
//   ordering writes the DP vector (state = for each column, whether the down
//   word currently crossing below row h-1 already holds a rook) into
//   out[leaf*K + colidx[mask]] (masks with colidx<0 must have zero value,
//   otherwise an error is flagged). seqs[leaf*h + r] = column of row r.
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
typedef unsigned long long u64;
static int N, H, KK; static const int *CI; static double *OUT; static int *SEQ;
static u64 *dp[20]; static int *lst[20]; static int len[20];
static int seq[20]; static long leaf; static int err;
static void step(int i, int c0){
  u64 *src=dp[i], *dst=dp[i+1]; int *L=lst[i+1];
  for(int t=0;t<len[i+1];t++) dst[L[t]]=0;
  int nl=0;
  for(int t=0;t<len[i];t++){ int m=lst[i][t]; u64 v=src[m];
    int mm=m;
    if(i>0){ if(!((mm>>c0)&1)) continue; }
    if(i<N-1) mm&=~(1<<c0); else mm|=(1<<c0);
    if(c0>0){
      for(int a=0;a<c0;a++){ if((mm>>a)&1) continue; int m2=mm|(1<<a);
        if(c0<N-1){ for(int b=c0+1;b<N;b++){ if((m2>>b)&1) continue; int m3=m2|(1<<b);
            if(!dst[m3]) L[nl++]=m3; dst[m3]+=v; } }
        else { if(!dst[m2]) L[nl++]=m2; dst[m2]+=v; } }
    } else {
      for(int b=c0+1;b<N;b++){ if((mm>>b)&1) continue; int m3=mm|(1<<b);
        if(!dst[m3]) L[nl++]=m3; dst[m3]+=v; }
    }
  }
  len[i+1]=nl;
}
static void rec(int i, int avail){
  if(i==H){
    double *o=OUT+leaf*(long)KK;
    for(int t=0;t<len[H];t++){ int m=lst[H][t]; int c=CI[m]; if(c<0){err=1;continue;} o[c]=(double)dp[H][m]; }
    for(int r=0;r<H;r++) SEQ[leaf*H+r]=seq[r];
    leaf++; return; }
  for(int c=0;c<N;c++){ if(!((avail>>c)&1)) continue; seq[i]=c; step(i,c); rec(i+1, avail&~(1<<c)); }
}
int half_vectors(int n, int h, int set_mask, const int *colidx, int K, double *out, int *seqs){
  N=n; H=h; KK=K; CI=colidx; OUT=out; SEQ=seqs; leaf=0; err=0;
  for(int i=0;i<=h;i++){ dp[i]=calloc(1<<n,sizeof(u64)); lst[i]=malloc(sizeof(int)*(1<<n)); len[i]=0; }
  dp[0][0]=1; lst[0][0]=0; len[0]=1;
  rec(0,set_mask);
  for(int i=0;i<=h;i++){ free(dp[i]); free(lst[i]); }
  return err? -1 : (int)leaf;
}
// collect the set of masks that occur (nonzero) among all orderings: marks seen[mask]=1
static char *SEEN;
static void rec2(int i,int avail){
  if(i==H){ for(int t=0;t<len[H];t++) SEEN[lst[H][t]]=1; return; }
  for(int c=0;c<N;c++){ if(!((avail>>c)&1)) continue; step(i,c); rec2(i+1, avail&~(1<<c)); }
}
void half_support(int n,int h,int set_mask,char *seen){
  N=n;H=h;SEEN=seen;
  for(int i=0;i<=h;i++){ dp[i]=calloc(1<<n,sizeof(u64)); lst[i]=malloc(sizeof(int)*(1<<n)); len[i]=0; }
  dp[0][0]=1; lst[0][0]=0; len[0]=1;
  rec2(0,set_mask);
  for(int i=0;i<=h;i++){ free(dp[i]); free(lst[i]); }
}
