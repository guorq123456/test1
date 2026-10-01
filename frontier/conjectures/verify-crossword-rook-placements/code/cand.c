// Enumerate "minimal-counterexample candidates" for Conj 3.9 at size n:
// w not skew-merged, but w minus {value n}, minus {value 1}, minus first entry, minus last entry all skew-merged.
// Method: DFS over prefixes w(1..k) that avoid 3412 and 2143 (necessary: w minus last entry is skew-merged),
// then complete with last entry and test the other conditions directly. Prints candidates.
#include <stdio.h>
#include <stdlib.h>
static int n, w[32], used;
static long long ncand=0, nleaf=0;
static int bad_ending_at(const int*a, int k){ // occurrence of 3412 or 2143 with last element at index k
  int z=a[k];
  for(int p=0;p<k;p++)for(int q=p+1;q<k;q++)for(int r=q+1;r<k;r++){
    int x=a[p],y=a[q],u=a[r];
    if(u<z && z<x && x<y) return 1;      // 3412
    if(y<x && x<z && z<u) return 1;      // 2143
  }
  return 0;
}
static int skew(const int*a,int m){ for(int k=3;k<m;k++) if(bad_ending_at(a,k)) return 0; return 1; }
static int delval(const int*a,int m,int v,int*out){ int t=0; for(int i=0;i<m;i++) if(a[i]!=v) out[t++]=a[i]; return t; }
static void dfs(int k){
  if(k==n-1){
    for(int v=1;v<=n;v++) if(!((used>>v)&1)){ w[n-1]=v; break; }
    nleaf++;
    if(skew(w,n)) return;
    int t[32],m;
    m=delval(w,n,n,t); if(!skew(t,m)) return;
    m=delval(w,n,1,t); if(!skew(t,m)) return;
    if(!skew(w+1,n-1)) return;
    ncand++;
    for(int i=0;i<n;i++) printf("%d ",w[i]); printf("\n");
    return;
  }
  for(int v=1;v<=n;v++){ if((used>>v)&1) continue; w[k]=v;
    if(k>=3 && bad_ending_at(w,k)) continue;
    used|=1<<v; dfs(k+1); used&=~(1<<v); }
}
int main(int argc,char**argv){ n=atoi(argv[1]); dfs(0); fprintf(stderr,"n=%d candidates=%lld leaves=%lld\n",n,ncand,nleaf); return 0; }
