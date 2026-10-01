/* For every 0..1 array of size (n+1)x(k+1) (exhaustive), check that
     valid (A253435 rule)  <=>  [ D = 0 off C  and  D(0,0)<=D(0,1)<=0<=D(n-1,k-2)<=D(n-1,k-1) ]
   where C = {(0,0),(0,1),(n-1,k-2),(n-1,k-1)}   (Proposition 2; hypothesis k>=2, max(n,k)>=4).
   Also checks Lemma 1 (support of positive / negative D entries) for every valid array.
   usage: check_char n k */
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){
  int n=atoi(argv[1]),k=atoi(argv[2]);
  int R=n+1,C=k+1,cells=R*C; long long cnt=0,cntc=0,bad=0,badL=0;
  int x[16][16],D[16][16];
  for(unsigned long long m=0;m<(1ULL<<cells);m++){
    for(int i=0;i<R;i++)for(int j=0;j<C;j++)x[i][j]=(m>>(i*C+j))&1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++)D[i][j]=x[i][j]+x[i+1][j+1]-x[i][j+1]-x[i+1][j];
    int ok=1;
    for(int i=0;i<n&&ok;i++)for(int j=0;j<k&&ok;j++){
      if(j+1<k && !(D[i][j]<=D[i][j+1]))ok=0;
      if(i+1<n && !(D[i][j]<=D[i+1][j]))ok=0;
      if(i+1<n && j+1<k && !(D[i][j+1]<=D[i+1][j]))ok=0;
    }
    int ch=1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++){
      int inC=(i==0&&j<=1)||(i==n-1&&j>=k-2);
      if(!inC && D[i][j]!=0)ch=0;
    }
    if(!(D[0][0]<=D[0][1] && D[0][1]<=0 && 0<=D[n-1][k-2] && D[n-1][k-2]<=D[n-1][k-1]))ch=0;
    if(ok){ /* Lemma 1 */
      for(int i=0;i<n;i++)for(int j=0;j<k;j++){
        if(D[i][j]<0 && !(i==0&&j<=1))badL++;
        if(D[i][j]>0 && !(i==n-1&&j>=k-2))badL++;
      }
    }
    cnt+=ok; cntc+=ch; if(ok!=ch)bad++;
  }
  printf("n=%d k=%d valid=%lld char=%lld mismatches=%lld lemma1_violations=%lld\n",n,k,cnt,cntc,bad,badL);
  return 0;
}
