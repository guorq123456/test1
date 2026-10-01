// E6: exhaustive search for counterexamples to SUFFICIENCY of b <= 1 + sum floor(a_i/r)
// in the fit box r in {2..6}, 1<=k<=8, 1<=a_i<=12 (multisets), 1<=b<=60.
// Usage: ./exh r   -> prints aggregate statistics for that r.
// For each multiset a (sorted) it computes A = prod [a_i]_q, then P_b = P_{b-1} + q^{r(b-1)} A
// incrementally for b = 1..60, stopping after the first non-unimodal b ("first fail").
// Margins (computed only for b inside the bound region b <= 1+S, S = sum floor(a_i/r)):
//   Delta_j = c_{j+1}-c_j = sum_{t=0}^{b-1} dA_{j+1-rt},  dA_m = A_m - A_{m-1}
//   Pos_j / Neg_j = sum of positive / negative parts of those dA terms.
//   "contested" position: j <= floor(N/2)-1 with Neg_j > 0 (only such j can give Delta_j<0).
//   ratio = max over contested j of Neg_j/Pos_j  (>1 <=> failure at j; ==1 exact cancellation).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef long long ll;
#define KMAX 8
#define AMAX 12
#define BMAX 60
#define LEN 1024
static int R;
static int a[KMAX+1];
static ll Abuf[KMAX+1][LEN];
// stats
static ll n_multisets=0, n_inst_region=0, n_fail_region=0, n_contested_inst=0, n_tie_inst=0;
static ll n_uni_mismatch=0, n_delta_mismatch=0;
static ll n_div_inst=0, n_div_fail=0; // instances with r | some a_i, all b<=60 (Cor 4.3 sanity)
static ll slack_hist[BMAX+3]; // first_fail - bound (index), or BMAX+2 for "no failure up to 60"
static ll ratio_hist[12];     // bins of ratio: 0 (uncontested), (0,.1],...,(0.9,1),==1, >1
static double best_ratio_rk[KMAX+1]; static ll best_ratio_rk_cnt[KMAX+1];
static double best_ratio_atbound_rk[KMAX+1];
static ll inst_rk[KMAX+1], fail_rk[KMAX+1], tie_rk[KMAX+1];
#define TOPN 40
typedef struct { double ratio; int k; int a[KMAX]; int b; int S; int j; ll pos, neg; ll c; } Top;
static Top top[TOPN]; static int ntop=0;
static void push_top(double ratio,int k,int b,int S,int j,ll pos,ll neg,ll c){
  // keep TOPN largest ratio (ties: keep earlier)
  if(ntop==TOPN && ratio<=top[TOPN-1].ratio) return;
  Top t; t.ratio=ratio;t.k=k;for(int i=0;i<k;i++)t.a[i]=a[i];t.b=b;t.S=S;t.j=j;t.pos=pos;t.neg=neg;t.c=c;
  int p = (ntop<TOPN)? ntop++ : TOPN-1;
  top[p]=t;
  while(p>0 && top[p].ratio>top[p-1].ratio){ Top x=top[p];top[p]=top[p-1];top[p-1]=x;p--; }
}
// smallest positive absolute Delta at a contested position
static ll best_absmin = -1; static int best_absmin_k, best_absmin_b; static int best_absmin_a[KMAX];

static ll c[LEN], Pos[LEN], Neg[LEN], dA[LEN];

static int unimodal_general(ll *x,int N){
  int i=0; while(i<N && x[i]<=x[i+1]) i++; while(i<N && x[i]>=x[i+1]) i++; return i==N;
}
static int firsthalf_nondec(ll *x,int N){
  for(int j=0;j<N/2;j++) if(x[j+1]<x[j]) return 0; return 1;
}

static void process(int k, ll *A, int degA){
  n_multisets++;
  int S=0, div=0; for(int i=0;i<k;i++){ S+=a[i]/R; if(a[i]%R==0) div=1; }
  int bound = 1+S; // sufficiency region b <= bound
  for(int m=0;m<=degA+1;m++){ ll hi = (m<=degA)?A[m]:0, lo=(m>=1)?A[m-1]:0; dA[m]=hi-lo; }
  memset(c,0,sizeof(ll)*(degA+R*BMAX+4));
  memset(Pos,0,sizeof(ll)*(degA+R*BMAX+4));
  memset(Neg,0,sizeof(ll)*(degA+R*BMAX+4));
  int firstfail = -1;
  for(int b=1;b<=BMAX;b++){
    int s=R*(b-1);
    for(int m=0;m<=degA;m++) c[m+s]+=A[m];
    for(int m=0;m<=degA+1;m++){ int idx=m+s-1; if(idx<0) continue; ll d=dA[m]; if(d>0) Pos[idx]+=d; else Neg[idx]-=d; }
    int N=degA+s;
    int ug=unimodal_general(c,N), uh=firsthalf_nondec(c,N);
    if(ug!=uh) n_uni_mismatch++;
    if(div){ n_div_inst++; if(!ug) n_div_fail++; }
    if(!ug && firstfail<0) firstfail=b;
    if(b<=bound){
      n_inst_region++; inst_rk[k]++;
      if(!ug){ n_fail_region++; fail_rk[k]++;
        printf("COUNTEREXAMPLE r=%d k=%d a=",R,k); for(int i=0;i<k;i++) printf("%d,",a[i]); printf(" b=%d\n",b); }
      double best=0; int bj=-1; int tie=0; ll babs=-1;
      for(int j=0;j<N/2;j++){
        ll D=c[j+1]-c[j];
        if(Pos[j]-Neg[j]!=D) n_delta_mismatch++;
        if(Neg[j]>0){
          double q = (Pos[j]>0)? (double)Neg[j]/(double)Pos[j] : 1e300;
          if(q>best){best=q;bj=j;}
          if(Neg[j]==Pos[j]) tie=1;
          if(D>0 && (babs<0 || D<babs)) babs=D;
        }
      }
      if(bj>=0){ n_contested_inst++; }
      if(tie){ n_tie_inst++; tie_rk[k]++; }
      int bin;
      if(bj<0) bin=0; else if(best>1) bin=11; else if(Neg[bj]==Pos[bj]) bin=10; else { bin=1+(int)(best*10); if(bin>9) bin=9; }
      ratio_hist[bin]++;
      if(bj>=0){
        if(best>best_ratio_rk[k]){best_ratio_rk[k]=best;best_ratio_rk_cnt[k]=1;} else if(best==best_ratio_rk[k]) best_ratio_rk_cnt[k]++;
        if(b==bound && best>best_ratio_atbound_rk[k]) best_ratio_atbound_rk[k]=best;
        push_top(best,k,b,S,bj,Pos[bj],Neg[bj],c[bj]);
      }
      if(babs>0 && (best_absmin<0 || babs<best_absmin)){ best_absmin=babs; best_absmin_k=k; best_absmin_b=b; for(int i=0;i<k;i++) best_absmin_a[i]=a[i]; }
    }
    if(firstfail>0 && b>=bound && !div) break; // past region; slack known
  }
  int idx = (firstfail<0)? BMAX+2 : (firstfail-bound);
  if(!div){ if(idx<0) idx=0; /* would be counterexample, already printed */ slack_hist[idx>BMAX+2?BMAX+2:idx]++; }
}

static void rec(int k,int minv,int degA){
  if(k>=1) process(k,Abuf[k],degA);
  if(k==KMAX) return;
  for(int v=minv;v<=AMAX;v++){
    a[k]=v;
    ll *src=Abuf[k], *dst=Abuf[k+1]; int nd=degA+v-1; ll s=0;
    for(int t=0;t<=nd;t++){ if(t<=degA) s+=src[t]; if(t-v>=0 && t-v<=degA) s-=src[t-v]; dst[t]=s; }
    rec(k+1,v,nd);
  }
}

int main(int argc,char**argv){
  R=atoi(argv[1]);
  Abuf[0][0]=1;
  rec(0,1,0);
  printf("r=%d multisets=%lld region_instances=%lld region_failures=%lld\n",R,n_multisets,n_inst_region,n_fail_region);
  printf("r=%d sanity: unimodal(general)!=firsthalf_nondec: %lld ; Delta identity mismatches: %lld\n",R,n_uni_mismatch,n_delta_mismatch);
  printf("r=%d CorollaryCheck r|some a_i, b<=60 (until stop): instances=%lld failures=%lld\n",R,n_div_inst,n_div_fail);
  printf("r=%d contested_instances=%lld exact_tie_instances(Neg==Pos>0 at some contested j)=%lld\n",R,n_contested_inst,n_tie_inst);
  printf("r=%d ratio_hist [uncontested,(0,.1),[.1,.2),...,[.8,1) ,==1, >1]:",R);
  for(int i=0;i<12;i++) printf(" %lld",ratio_hist[i]); printf("\n");
  for(int k=1;k<=KMAX;k++) printf("r=%d k=%d inst=%lld fail=%lld ties=%lld max_ratio=%.6f (count %lld) max_ratio_at_b=bound=%.6f\n",R,k,inst_rk[k],fail_rk[k],tie_rk[k],best_ratio_rk[k],best_ratio_rk_cnt[k],best_ratio_atbound_rk[k]);
  printf("r=%d slack hist (first_fail_b - bound) for multisets with no r|a_i; last bin = no failure up to b=60:",R);
  for(int i=0;i<=BMAX+2;i++) if(slack_hist[i]) printf(" [%d]:%lld",i==BMAX+2?-1:i,slack_hist[i]); printf("\n");
  if(best_absmin>0){ printf("r=%d smallest positive Delta at contested position: %lld at k=%d a=",R,best_absmin,best_absmin_k); for(int i=0;i<best_absmin_k;i++) printf("%d,",best_absmin_a[i]); printf(" b=%d\n",best_absmin_b);}
  for(int i=0;i<ntop;i++){ Top*t=&top[i]; printf("r=%d TOP%02d ratio=%.6f k=%d a=",R,i,t->ratio,t->k); for(int u=0;u<t->k;u++) printf("%d,",t->a[u]); printf(" b=%d bound=%d j=%d Pos=%lld Neg=%lld\n",t->b,t->S+1,t->j,t->pos,t->neg); }
  return 0;
}
