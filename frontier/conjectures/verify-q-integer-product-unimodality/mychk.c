// Independent checker for Conj 5.4 of arXiv:2605.12822.
// For r, multisets {a_i} (2<=a_i<=amax, r !| a_i, size 1..kmax), and b=1..bmax,
// test unimodality of prod [a_i]_q * [b]_{q^r} by direct full scan.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
static int r, kmax, amax;
static int vals[512], nv;
static I *poly[32]; static int deg[32];
static int cur[32];
static long long nmult=0, nchecks=0, suffail=0, necfail[64], r3mis=0;
static int maxkept=0;
static I *buf; static int bufcap;
static int unimodal(I *c, int n){ // c[0..n-1]
  int i=0; while(i+1<n && c[i]<=c[i+1]) i++;
  while(i+1<n && c[i]>=c[i+1]) i++;
  return i>=n-1;
}
static int printed=0;
static void process(int k){
  I *P=poly[k]; int D=deg[k];
  int F=0,S=0; for(int i=0;i<k;i++){F+=cur[i]/r; if(cur[i]%3==2) S++;}
  nmult++;
  int bmax=(D+2*r)/r+3; // lemma: no unimodality once r(b-1)>=D+2r; go beyond to test the lemma
  int N=D+r*(bmax-1)+1;
  if(N>bufcap){bufcap=2*N; buf=realloc(buf,sizeof(I)*bufcap);}
  memset(buf,0,sizeof(I)*N);
  int maxuni=0;
  for(int b=1;b<=bmax;b++){
    int sh=r*(b-1);
    for(int t=0;t<=D;t++) buf[t+sh]+=P[t];
    int n=D+sh+1;
    int u=unimodal(buf,n); nchecks++;
    int cond=(b<=1+F);
    if(u && b>maxuni) maxuni=b;
    if(cond && !u){suffail++; if(printed<30){printed++;printf("SUFF FAIL r=%d b=%d a=",r,b);for(int i=0;i<k;i++)printf("%d ",cur[i]);printf("\n");}}
    if(!cond && u){necfail[k]++; if((k<=3 || r<=3) && printed<30){printed++;printf("NEC FAIL r=%d k=%d b=%d F=%d a=",r,k,b,F);for(int i=0;i<k;i++)printf("%d ",cur[i]);printf("\n");}}
    if(r==3){int rule=(b<=F+1+2*(S/6)); if(rule!=u){r3mis++; if(printed<30){printed++;printf("R3RULE MISMATCH b=%d u=%d a=",b,u);for(int i=0;i<k;i++)printf("%d ",cur[i]);printf("\n");}}}
    if(u && r*(b-1)>=D+2*r){printf("LEMMA VIOLATION r=%d b=%d\n",r,b);}
  }
}
static void rec(int k, int start){
  if(k>=1) process(k);
  if(k==kmax) return;
  for(int vi=start; vi<nv; vi++){
    int a=vals[vi]; cur[k]=a;
    int D=deg[k]; I *P=poly[k]; I *Q=poly[k+1];
    int nd=D+a-1; deg[k+1]=nd;
    // Q = P * [a]_q via sliding window
    I s=0;
    for(int t=0;t<=nd;t++){ if(t<=D) s+=P[t]; if(t-a>=0 && t-a<=D) s-=P[t-a]; Q[t]=s; }
    rec(k+1, vi);
  }
}
int main(int argc,char**argv){
  r=atoi(argv[1]); kmax=atoi(argv[2]); amax=atoi(argv[3]);
  nv=0; for(int a=2;a<=amax;a++) if(a%r) vals[nv++]=a;
  for(int i=0;i<=kmax;i++) poly[i]=calloc(kmax*amax+10,sizeof(I));
  poly[0][0]=1; deg[0]=0;
  rec(0,0);
  printf("r=%d kmax=%d amax=%d multisets=%lld checks=%lld suff_fail=%lld",r,kmax,amax,nmult,nchecks,suffail);
  printf(" nec_fail_by_k:"); for(int k=1;k<=kmax;k++) printf(" %lld",necfail[k]);
  if(r==3) printf(" r3rule_mismatch=%lld",r3mis);
  printf("\n");
  return 0;
}
