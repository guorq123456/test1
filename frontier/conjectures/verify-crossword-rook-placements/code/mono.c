// Check Remark 3.4 (monotonicity under deleting value n) for all w in S_n.
#include "rpcore.h"
static int fact[16];
static int rankp(const int*p,int m){ int r=0; for(int i=0;i<m;i++){ int c=0; for(int j=i+1;j<m;j++) if(p[j]<p[i]) c++; r+=c*fact[m-1-i]; } return r; }
int main(int argc,char**argv){
  int n=atoi(argv[1]); fact[0]=1; for(int i=1;i<16;i++) fact[i]=fact[i-1]*i;
  // values for S_{n-1}
  int m=n-1; u128*tab=malloc(sizeof(u128)*fact[m]);
  init(m);
  int p[16]; for(int i=0;i<m;i++) p[i]=i;
  // iterate permutations lexicographically
  long cnt=0;
  while(1){ tab[rankp(p,m)]=rp(p); cnt++;
    int i=m-2; while(i>=0 && p[i]>p[i+1]) i--; if(i<0) break;
    int j=m-1; while(p[j]<p[i]) j--; int t=p[i];p[i]=p[j];p[j]=t;
    for(int a=i+1,b=m-1;a<b;a++,b--){t=p[a];p[a]=p[b];p[b]=t;} }
  // free and re-init for n
  for(int t=0;t<2;t++){ free(val[t]); free(lst[t]); free(flag[t]); }
  init(n);
  for(int i=0;i<n;i++) p[i]=i;
  long viol=0, tot=0, eq=0;
  while(1){ u128 v=rp(p); int q[16],k=0; for(int i=0;i<n;i++) if(p[i]!=n-1) q[k++]=p[i];
    u128 v2=tab[rankp(q,m)]; if(v2>v){ viol++; } if(v2==v) eq++; tot++;
    int i=n-2; while(i>=0 && p[i]>p[i+1]) i--; if(i<0) break;
    int j=n-1; while(p[j]<p[i]) j--; int t=p[i];p[i]=p[j];p[j]=t;
    for(int a=i+1,b=n-1;a<b;a++,b--){t=p[a];p[a]=p[b];p[b]=t;} }
  printf("n=%d checked %ld perms, violations of RP(w minus n) <= RP(w): %ld (equalities %ld)\n",n,tot,viol,eq);
  return 0;
}
