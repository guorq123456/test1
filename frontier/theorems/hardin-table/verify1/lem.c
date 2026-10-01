// Check (F2), Lemma 1 and Proposition 2 and the classification for given (n,k), exhaustively.
#include <stdio.h>
#include <stdlib.h>
int n,k,R,C; int x[32][32],D[32][32];
int main(int argc,char**argv){
  n=atoi(argv[1]);k=atoi(argv[2]);R=n+1;C=k+1;int cells=R*C;
  long long nvalid=0,f2bad=0,l1bad=0,p2bad=0,p2fwd=0,p2bwd=0,rowtype=0,frozen=0,other=0,rectbad=0;
  for(long long m=0;m<(1LL<<cells);m++){
    for(int i=0;i<R;i++)for(int j=0;j<C;j++) x[i][j]=(m>>(i*C+j))&1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++) D[i][j]=x[i][j]+x[i+1][j+1]-x[i][j+1]-x[i+1][j];
    int ok=1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++){
      if(j+1<k && D[i][j]>D[i][j+1]) ok=0;
      if(i+1<n && D[i][j]>D[i+1][j]) ok=0;
      if(i+1<n && j+1<k && D[i][j+1]>D[i+1][j]) ok=0;
    }
    // Prop 2 condition
    int z=1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++){
      int inCm=(i==0&&(j==0||j==1)); int inCp=(i==n-1&&(j==k-2||j==k-1));
      if(!inCm&&!inCp&&D[i][j]!=0) z=0;
    }
    int ch = (D[0][0]<=D[0][1]) && (D[0][1]<=0) && (0<=D[n-1][k-2]) && (D[n-1][k-2]<=D[n-1][k-1]);
    int p2=z&&ch;
    if(p2!=ok){ p2bad++; if(ok) p2fwd++; else p2bwd++; }
    if(!ok) continue;
    nvalid++;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++){
      if(D[i][j]>=1 && !(i>=n-2 && j>=k-2)) f2bad++;
      if(D[i][j]<=-1 && !(i<=1 && j<=1)) f2bad++;
      if(D[i][j]>=1 && !(i==n-1 && (j==k-2||j==k-1))) l1bad++;
      if(D[i][j]<=-1 && !(i==0 && (j==0||j==1))) l1bad++;
    }
    // classification: rows R_1..R_{n-1}
    if(n>=2){
      int allconst=1, allequal=1;
      for(int i=1;i<=n-1;i++){ int c=1; for(int j=1;j<C;j++) if(x[i][j]!=x[i][0]) c=0; if(!c) allconst=0; for(int j=0;j<C;j++) if(x[i][j]!=x[1][j]) allequal=0; }
      if(allconst){
        // R0 in {0^,1^,01^k}, Rn in {0^,1^,0^k1}
        int r0ok=1; { int c=1; for(int j=1;j<C;j++) if(x[0][j]!=x[0][0]) c=0; int o=(x[0][0]==0); for(int j=1;j<C;j++) if(x[0][j]!=1) o=0; r0ok=c||o; }
        int rnok=1; { int c=1; for(int j=1;j<C;j++) if(x[n][j]!=x[n][0]) c=0; int o=(x[n][k]==1); for(int j=0;j<k;j++) if(x[n][j]!=0) o=0; rnok=c||o; }
        if(r0ok&&rnok) rowtype++; else other++;
      } else if(allequal) frozen++; else other++;
    }
  }
  printf("n=%d k=%d valid=%lld F2bad=%lld L1bad=%lld P2bad=%lld (valid-but-not-P2 %lld, P2-but-invalid %lld) rowtype=%lld (9*2^(n-1)=%d) frozen=%lld other=%lld\n",
    n,k,nvalid,f2bad,l1bad,p2bad,p2fwd,p2bwd,rowtype,9*(1<<(n-1)),frozen,other);
}
