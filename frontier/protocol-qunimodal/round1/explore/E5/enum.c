// Enumerate r in 2..6, sorted tuples a (2<=a_i<=12, r not dividing a_i), k=1..8,
// output: r k a1..ak mask  where mask bit (b-1) set iff P unimodal, b=1..60
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef long long L;
static int r, K, vals[16], nv;
static int a[16];
static L A[200];
static int degA;
static L c[1000];
int isuni(L *d,int deg){ int i=0; while(i<deg && d[i]<=d[i+1]) i++; while(i<deg && d[i]>=d[i+1]) i++; return i==deg; }
void process(int k){
  // build A
  static L t[200]; degA=0; A[0]=1;
  for(int i=0;i<k;i++){ int m=a[i], nd=degA+m-1; L s=0;
    for(int x=0;x<=nd;x++){ if(x<=degA) s+=A[x]; if(x-m>=0 && x-m<=degA) s-=A[x-m]; t[x]=s;} degA=nd; memcpy(A,t,sizeof(L)*(degA+1)); }
  memset(c,0,sizeof(c));
  unsigned long long mask=0;
  for(int b=1;b<=60;b++){
    int off=r*(b-1);
    for(int x=0;x<=degA;x++) c[x+off]+=A[x];
    if(isuni(c,degA+off)) mask|=1ULL<<(b-1);
  }
  printf("%d %d",r,k); for(int i=0;i<k;i++) printf(" %d",a[i]); printf(" %llu\n",mask);
}
void rec(int pos,int k,int start){
  if(pos==k){ process(k); return; }
  for(int j=start;j<nv;j++){ a[pos]=vals[j]; rec(pos+1,k,j); }
}
int main(int argc,char**argv){
  r=atoi(argv[1]); int kmax=atoi(argv[2]);
  nv=0; for(int v=2;v<=12;v++) if(v%r) vals[nv++]=v;
  for(int k=1;k<=kmax;k++) rec(0,k,0);
  return 0;
}
