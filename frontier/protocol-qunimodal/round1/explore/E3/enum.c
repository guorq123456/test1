// Enumerate the full fit box: r in 2..6, k in 1..8, 1<=a_1<=...<=a_k<=12, b in 1..60.
// Output per (r,a): "r k a1..ak mask" where bit (b-1) of mask = 1 iff P unimodal (weakly).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef long long L;
#define KMAX 8
#define AMAX 12
#define BMAX 60
static L stk[KMAX+1][128]; static int sdeg[KMAX+1];
static int a[KMAX];
static int R;
static L P[1024];
static int unimodal(L *d,int deg){ int i=0; while(i<deg && d[i]<=d[i+1]) i++; while(i<deg && d[i]>=d[i+1]) i++; return i==deg; }
static void emit(int k){
  L *A=stk[k]; int dA=sdeg[k];
  unsigned long long mask=0;
  int maxdeg=dA+R*(BMAX-1);
  memset(P,0,sizeof(L)*(maxdeg+1));
  for(int b=1;b<=BMAX;b++){
    int off=R*(b-1);
    for(int t=0;t<=dA;t++) P[off+t]+=A[t];
    if(unimodal(P,dA+off)) mask|=1ULL<<(b-1);
  }
  printf("%d %d",R,k); for(int i=0;i<k;i++) printf(" %d",a[i]); printf(" %llu\n",mask);
}
static void rec(int k,int lo){
  if(k>=1) emit(k);
  if(k==KMAX) return;
  for(int v=lo;v<=AMAX;v++){
    a[k]=v;
    // multiply stk[k] by [v]_q into stk[k+1]
    int dd=sdeg[k], nd=dd+v-1; L s=0;
    for(int t=0;t<=nd;t++){ if(t<=dd) s+=stk[k][t]; if(t-v>=0&&t-v<=dd) s-=stk[k][t-v]; stk[k+1][t]=s; }
    sdeg[k+1]=nd;
    rec(k+1,v);
  }
}
int main(int argc,char**argv){
  R=atoi(argv[1]);
  stk[0][0]=1; sdeg[0]=0;
  rec(0,1);
  return 0;
}
