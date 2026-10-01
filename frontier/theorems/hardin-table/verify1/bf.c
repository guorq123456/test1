// Independent brute force: count (R)x(C) 0/1 arrays (R=n+1 rows, C=k+1 cols)
// D(i,j)=x(i,j)+x(i+1,j+1)-x(i,j+1)-x(i+1,j); V1: D(i,j)<=D(i,j+1); V2: D(i,j)<=D(i+1,j)
// V3 mode: 0: D(i,j+1)<=D(i+1,j) (NE->SW nondecr); 1: D(i+1,j)<=D(i,j+1); 2: D(i,j)<=D(i+1,j+1); 3: D(i+1,j+1)<=D(i,j); 4: none
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){
  int n=atoi(argv[1]),k=atoi(argv[2]);
  int R=n+1,C=k+1; int cells=R*C;
  long long cnt[5]={0};
  int x[32][32]; int D[32][32];
  for(long long m=0;m<(1LL<<cells);m++){
    for(int i=0;i<R;i++)for(int j=0;j<C;j++) x[i][j]=(m>>(i*C+j))&1;
    for(int i=0;i<n;i++)for(int j=0;j<k;j++) D[i][j]=x[i][j]+x[i+1][j+1]-x[i][j+1]-x[i+1][j];
    int ok=1;
    for(int i=0;i<n&&ok;i++)for(int j=0;j+1<k;j++) if(D[i][j]>D[i][j+1]){ok=0;break;}
    for(int i=0;i+1<n&&ok;i++)for(int j=0;j<k;j++) if(D[i][j]>D[i+1][j]){ok=0;break;}
    if(!ok) continue;
    int okm[5]={1,1,1,1,1};
    for(int i=0;i+1<n;i++)for(int j=0;j+1<k;j++){
      if(D[i][j+1]>D[i+1][j]) okm[0]=0;
      if(D[i+1][j]>D[i][j+1]) okm[1]=0;
      if(D[i][j]>D[i+1][j+1]) okm[2]=0;
      if(D[i+1][j+1]>D[i][j]) okm[3]=0;
    }
    for(int t=0;t<5;t++) cnt[t]+=okm[t];
  }
  printf("%d %d %lld %lld %lld %lld %lld\n",n,k,cnt[0],cnt[1],cnt[2],cnt[3],cnt[4]);
  return 0;
}
