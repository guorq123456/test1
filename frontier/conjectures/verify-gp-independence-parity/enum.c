// Plain backtracking enumeration of all independent sets of GP(n,k) (Definition 2.1), counts by size.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static int N; static uint64_t adj[64]; static unsigned long long cnt[65];
static void rec(int i, uint64_t chosen, int sz){
  if(i==N){cnt[sz]++;return;}
  rec(i+1,chosen,sz);
  if(!(adj[i]&chosen)) rec(i+1,chosen|(1ULL<<i),sz+1);
}
int main(int argc,char**argv){
  int n=atoi(argv[1]),k=atoi(argv[2]); N=2*n;
  // vertex order: u_i -> 2i, v_i -> 2i+1
  #define U(i) (2*(((i)%n+n)%n))
  #define V(i) (2*(((i)%n+n)%n)+1)
  for(int i=0;i<n;i++){
    int e[3][2]={{U(i),U(i+1)},{V(i),V(i+k)},{U(i),V(i)}};
    for(int t=0;t<3;t++){int a=e[t][0],b=e[t][1]; adj[a]|=1ULL<<b; adj[b]|=1ULL<<a;}
  }
  rec(0,0,0);
  int d=N; while(d>0&&cnt[d]==0)d--;
  printf("%d %d ",k,n); for(int j=0;j<=d;j++) printf("%llu%s",cnt[j],j<d?",":"\n");
}
