// E6 margins: finer near-failure statistics inside the sufficiency region b <= 1+S (S=sum floor(a_i/r)),
// fit box r in {2..6}, 1<=k<=8, 1<=a_i<=12 (sorted multisets), b<=60.
// Usage: ./margins r [dump]   (dump: also print "FF r k a... firstfail bound" for every multiset with no r|a_i)
// Notation: c = coefficients of P, Delta_j = c_{j+1}-c_j = Pos_j - Neg_j (see exh.c), j < floor(N/2).
// "hard" instance: no a_i divisible by r, all a_i >= 2, b >= 2.
// Reports per (r,k) and for the hard subset:
//   - max ratio Neg/Pos among contested positions with Neg<Pos (strict, non-tie)
//   - ties (Neg==Pos>0): largest tie size Neg, largest tie depth Neg/c_j
//   - number of hard instances at b=bound having a tie
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef long long ll;
#define KMAX 8
#define AMAX 12
#define BMAX 60
#define LEN 1024
static int R, DUMP=0;
static int a[KMAX+1];
static ll Abuf[KMAX+1][LEN];
static ll c[LEN], Pos[LEN], Neg[LEN], dA[LEN];
typedef struct { double v; int k; int a[KMAX]; int b; int bound; int j; ll pos, neg, cj; int set; } Rec;
// index 0..KMAX: per k (all instances); index KMAX+1: hard subset (all k)
static Rec strictRatio[KMAX+2], tieSize[KMAX+2], tieDepth[KMAX+2];
static ll hard_atbound[KMAX+1], hard_atbound_tie[KMAX+1], hard_inst[KMAX+1], hard_tie[KMAX+1];
static void upd(Rec *R0,double v,int k,int b,int bound,int j,ll pos,ll neg,ll cj){
  if(R0->set && v<=R0->v) return;
  R0->set=1;R0->v=v;R0->k=k;for(int i=0;i<k;i++)R0->a[i]=a[i];R0->b=b;R0->bound=bound;R0->j=j;R0->pos=pos;R0->neg=neg;R0->cj=cj;
}
static void pr(const char*name,int idx,Rec*R0){
  if(!R0->set){printf("r=%d %s idx=%d none\n",R,name,idx);return;}
  printf("r=%d %s %s value=%.6f k=%d a=",R,name,idx==KMAX+1?"HARD":"k",R0->v,R0->k);
  for(int i=0;i<R0->k;i++) printf("%d,",R0->a[i]);
  printf(" b=%d bound=%d j=%d Pos=%lld Neg=%lld c_j=%lld\n",R0->b,R0->bound,R0->j,R0->pos,R0->neg,R0->cj);
}
static int unimodal_general(ll *x,int N){ int i=0; while(i<N && x[i]<=x[i+1]) i++; while(i<N && x[i]>=x[i+1]) i++; return i==N; }

static void process(int k, ll *A, int degA){
  int S=0, div=0, allge2=1; for(int i=0;i<k;i++){ S+=a[i]/R; if(a[i]%R==0) div=1; if(a[i]<2) allge2=0; }
  int bound=1+S;
  for(int m=0;m<=degA+1;m++){ ll hi=(m<=degA)?A[m]:0, lo=(m>=1)?A[m-1]:0; dA[m]=hi-lo; }
  int L=degA+R*BMAX+4; memset(c,0,sizeof(ll)*L); memset(Pos,0,sizeof(ll)*L); memset(Neg,0,sizeof(ll)*L);
  int firstfail=-1;
  for(int b=1;b<=BMAX;b++){
    int s=R*(b-1);
    for(int m=0;m<=degA;m++) c[m+s]+=A[m];
    for(int m=0;m<=degA+1;m++){ int idx=m+s-1; if(idx<0) continue; ll d=dA[m]; if(d>0) Pos[idx]+=d; else Neg[idx]-=d; }
    int N=degA+s;
    if(firstfail<0 && !unimodal_general(c,N)) firstfail=b;
    if(b<=bound){
      int hard = (!div && allge2 && b>=2);
      int tie=0;
      for(int j=0;j<N/2;j++){
        if(Neg[j]==0) continue;
        if(Neg[j]<Pos[j]){ double q=(double)Neg[j]/Pos[j]; upd(&strictRatio[k],q,k,b,bound,j,Pos[j],Neg[j],c[j]); if(hard) upd(&strictRatio[KMAX+1],q,k,b,bound,j,Pos[j],Neg[j],c[j]); }
        else if(Neg[j]==Pos[j]){ tie=1;
          upd(&tieSize[k],(double)Neg[j],k,b,bound,j,Pos[j],Neg[j],c[j]);
          upd(&tieDepth[k],(double)Neg[j]/c[j],k,b,bound,j,Pos[j],Neg[j],c[j]);
          if(hard){ upd(&tieSize[KMAX+1],(double)Neg[j],k,b,bound,j,Pos[j],Neg[j],c[j]); upd(&tieDepth[KMAX+1],(double)Neg[j]/c[j],k,b,bound,j,Pos[j],Neg[j],c[j]); }
        } else { printf("COUNTEREXAMPLE?? r=%d k=%d b=%d\n",R,k,b); }
      }
      if(hard){ hard_inst[k]++; if(tie) hard_tie[k]++; if(b==bound){ hard_atbound[k]++; if(tie) hard_atbound_tie[k]++; } }
    }
    if(b>=bound && firstfail>0 && !(DUMP==0 && div)) break;
    if(b>=bound && div) break;
  }
  if(DUMP && !div){ printf("FF %d %d",R,k); for(int i=0;i<k;i++) printf(" %d",a[i]); printf(" %d %d\n",firstfail,bound); }
}
static void rec(int k,int minv,int degA){
  if(k>=1) process(k,Abuf[k],degA);
  if(k==KMAX) return;
  for(int v=minv;v<=AMAX;v++){
    a[k]=v; ll *src=Abuf[k], *dst=Abuf[k+1]; int nd=degA+v-1; ll s=0;
    for(int t=0;t<=nd;t++){ if(t<=degA) s+=src[t]; if(t-v>=0 && t-v<=degA) s-=src[t-v]; dst[t]=s; }
    rec(k+1,v,nd);
  }
}
int main(int argc,char**argv){
  R=atoi(argv[1]); if(argc>2) DUMP=1;
  Abuf[0][0]=1; rec(0,1,0);
  if(DUMP) return 0;
  for(int k=1;k<=KMAX+1;k++){ pr("maxStrictRatio",k,&strictRatio[k]); pr("maxTieSize",k,&tieSize[k]); pr("maxTieDepth",k,&tieDepth[k]); }
  for(int k=1;k<=KMAX;k++) printf("r=%d k=%d hard_instances=%lld hard_with_tie=%lld hard_at_b=bound=%lld of_which_tie=%lld\n",R,k,hard_inst[k],hard_tie[k],hard_atbound[k],hard_atbound_tie[k]);
  return 0;
}
