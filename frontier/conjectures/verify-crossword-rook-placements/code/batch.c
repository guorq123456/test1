#include "rpcore.h"
// read: n, then perms (1-based) one per line; print value per line
int main(){ int n; if(scanf("%d",&n)!=1) return 1; init(n); int w[32];
  while(1){ for(int i=0;i<n;i++){ if(scanf("%d",&w[i])!=1) return 0; w[i]--; } print128(rp(w)); putchar('\n'); } }
