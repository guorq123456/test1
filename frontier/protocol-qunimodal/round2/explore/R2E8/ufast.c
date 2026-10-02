// Fast exact U computation (int128; caller guarantees prod a_i < 2^120).
// stdin: "r k a1..ak" ; stdout: "T6 F Bh1 Ubits" where Ubits is string of 0/1 for b=1..T6+3,
// Bh1 = H1 prediction.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
static I A[1<<15], d[1<<15], g[1<<16];
int main(void){
  int r,k; int a[64];
  while(scanf("%d %d",&r,&k)==2){
    for(int i=0;i<k;i++) scanf("%d",&a[i]);
    int deg=0; A[0]=1;
    for(int i=0;i<k;i++){ int Aa=a[i], nd=deg+Aa-1; I s=0;
      for(int t=0;t<=nd;t++){ if(t<=deg) s+=A[t]; if(t-Aa>=0&&t-Aa<=deg) s-=A[t-Aa]; d[t]=s; }
      deg=nd; memcpy(A,d,sizeof(I)*(deg+1)); }
    int D=deg, F=0; for(int i=0;i<k;i++) F+=a[i]/r;
    // tau = residue-class sums of A(1-q)
    I tau[64]; for(int t=0;t<r;t++) tau[t]=0;
    for(int t=0;t<=D+1;t++){ I v=(t<=D?A[t]:0)-(t>=1?A[t-1]:0); tau[t%r]+=v; }
    int mu=0; for(int j=1;j<r;j++) if(tau[j]>0) mu=j;
    int T6=1+ (int)((D+1-2*mu)>=0 ? (D+1-2*mu)/r : -((-(D+1-2*mu)+r-1)/r));
    int s=(D+1)%r; int Bh1 = (tau[s]<=-2 && s>=2*mu)? T6-2 : T6;
    int bmax=T6+3; int Nmax=D+r*(bmax-1); int L=Nmax/2+2;
    for(int i=0;i<L;i++){ I v=0; if(i<=D+1) v=(i<=D?A[i]:0)-(i>=1?A[i-1]:0); g[i]=v+(i>=r?g[i-r]:0); }
    printf("%d %d %d ",T6,F,Bh1);
    for(int b=1;b<=bmax;b++){ int N=D+r*(b-1), rb=r*b, ok=1;
      for(int i=1;i<=N/2;i++){ I c=(i>=rb)?g[i-rb]:0; if(g[i]<c){ok=0;break;} }
      putchar(ok?'1':'0'); }
    putchar('\n');
  }
  return 0;
}
