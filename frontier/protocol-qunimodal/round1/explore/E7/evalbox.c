// evalbox.c: evaluate candidate rules on the whole fit box.
// Enumerates r=2..6, multisets of size 0..8 from {2..12} (INCLUDING multiples of r), b=1..60.
// Entries a_i=1 are trivial factors: a multiset of size k' stands for (9-k') box tuples (adding j ones, k'+j in 1..8;
// for k'=0 that is 8 tuples). Reports unweighted and box-weighted error counts.
// Rules: TRUTH (direct unimodality of P), EXACT (g_i>=g_{i-rb}, i<=h), THRESH (g_i>=0, i<=h), CONJ.
#include <stdio.h>
#include <string.h>
typedef long long L;
static int vals[16], nv=11, cur[16], r;
static L err[4][2], tot[2];  // [rule][weighted?]
static L p[1024], c[2048], g[2048];
static void process(int k){
  int deg=0; p[0]=1; static L d[1024];
  for(int i=0;i<k;i++){int A=cur[i]; int nd=deg+A-1; L s=0;
    for(int t=0;t<=nd;t++){ if(t<=deg) s+=p[t]; if(t-A>=0&&t-A<=deg) s-=p[t-A]; d[t]=s;}
    deg=nd; memcpy(p,d,sizeof(L)*(deg+1));}
  int D=deg; L w = (k==0)?8:(9-k);
  int maxN=D+r*59;
  for(int i=0;i<=maxN;i++){ L v=(i<=D?p[i]:0)-((i>=1&&i-1<=D)?p[i-1]:0); g[i]=v+(i>=r?g[i-r]:0); }
  int F=0, div=0; for(int i=0;i<k;i++){F+=cur[i]/r; if(cur[i]%r==0) div=1;}
  memset(c,0,sizeof(L)*(maxN+2));
  for(int b=1;b<=60;b++){
    int R=r*(b-1); for(int j=0;j<=D;j++) c[R+j]+=p[j];
    int N=D+R, h=N/2, rb=r*b;
    int i=0; while(i<N && c[i]<=c[i+1]) i++; while(i<N && c[i]>=c[i+1]) i++;
    int truth=(i==N);
    int ex=1, th=1;
    for(int j=0;j<=h;j++){ L gb=(j>=rb)?g[j-rb]:0; if(g[j]<gb) ex=0; if(g[j]<0) th=0; }
    int cj = div || (b<=1+F);
    int pr[3]={ex,th,cj};
    tot[0]++; tot[1]+=w;
    for(int q=0;q<3;q++) if(pr[q]!=truth){ err[q][0]++; err[q][1]+=w; }
  }
}
static void rec(int k,int start){ process(k); if(k==8) return; for(int i=start;i<nv;i++){cur[k]=vals[i]; rec(k+1,i);} }
int main(){
  for(int a=2;a<=12;a++) vals[a-2]=a;
  const char*nm[3]={"EXACT","THRESH","CONJ"};
  for(r=2;r<=6;r++){
    L e0[3][2]; for(int q=0;q<3;q++){e0[q][0]=err[q][0];e0[q][1]=err[q][1];}
    L t0=tot[0], t1=tot[1];
    rec(0,0);
    printf("r=%d instances(distinct P)=%lld boxweighted=%lld :",r,tot[0]-t0,tot[1]-t1);
    for(int q=0;q<3;q++) printf(" %s=%lld/%lld",nm[q],err[q][0]-e0[q][0],err[q][1]-e0[q][1]);
    printf("\n");
  }
  printf("TOTAL instances %lld boxweighted %lld :",tot[0],tot[1]);
  for(int q=0;q<3;q++) printf(" %s=%lld/%lld",nm[q],err[q][0],err[q][1]);
  printf("\n");
}
