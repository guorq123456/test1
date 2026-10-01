// Independent sparse row DP for |RP(Grid(w))|, exact via unsigned __int128.
// Modes:
//   vdp perm n w1 ... wn         : single permutation
//   vdp layered n [topK]         : all compositions of n (layered perms), print top K
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static int N;
static u128 *val[2];
static uint32_t *lst[2];
static int len[2];
static uint8_t *flag[2];

static void print128(u128 x){ char b[64]; int k=0; if(!x){putchar('0');return;} while(x){b[k++]='0'+(int)(x%10); x/=10;} while(k) putchar(b[--k]); }

static inline void add(int t, uint32_t T, u128 v){
  if(!flag[t][T]){ flag[t][T]=1; lst[t][len[t]++]=T; val[t][T]=0; }
  val[t][T]+=v;
}
static void clearbuf(int t){ for(int k=0;k<len[t];k++) flag[t][lst[t][k]]=0; len[t]=0; }

static void init(int n){
  N=n; size_t M=(size_t)1<<n;
  for(int t=0;t<2;t++){ val[t]=malloc(M*sizeof(u128)); lst[t]=malloc(M*sizeof(uint32_t)); flag[t]=calloc(M,1); len[t]=0; }
}

// w: 0-based values
static u128 rp(const int *w){
  int n=N; if(n==1) return 1;
  int cur=0; clearbuf(0); clearbuf(1);
  add(cur, 1u<<w[0], 1);
  uint32_t full=(n==32)?0xffffffffu:((1u<<n)-1);
  for(int i=0;i<n;i++){
    int c=w[i]; int nx=cur^1;
    // close upper word of column c, open lower word
    for(int k=0;k<len[cur];k++){ uint32_t S=lst[cur][k]; if(!((S>>c)&1)) continue;
      uint32_t T=(i<n-1)?(S&~(1u<<c)):S; add(nx,T,val[cur][S]); }
    clearbuf(cur); cur=nx;
    int lo[2]={0,c+1}, hi[2]={c,n};
    for(int s=0;s<2;s++){ if(lo[s]>=hi[s]) continue; nx=cur^1;
      for(int k=0;k<len[cur];k++){ uint32_t S=lst[cur][k]; u128 v=val[cur][S];
        for(int j=lo[s];j<hi[s];j++) if(!((S>>j)&1)) add(nx,S|(1u<<j),v); }
      clearbuf(cur); cur=nx; }
  }
  u128 r=0; if(flag[cur][full]) r=val[cur][full];
  clearbuf(cur);
  return r;
}

int main(int argc,char**argv){
  if(argc<3) return 1;
  if(!strcmp(argv[1],"perm")){
    int n=atoi(argv[2]); init(n); int w[32];
    for(int i=0;i<n;i++) w[i]=atoi(argv[3+i])-1;
    print128(rp(w)); putchar('\n'); return 0;
  }
  if(!strcmp(argv[1],"layered")){
    int n=atoi(argv[2]); int K=argc>3?atoi(argv[3]):10; init(n);
    // enumerate compositions via bitmask of cuts among n-1 gaps
    typedef struct{u128 v; uint32_t cuts;} rec;
    rec *top=calloc(K,sizeof(rec)); int ntop=0;
    for(uint32_t cuts=0; cuts < (1u<<(n-1)); cuts++){
      int w[32]; int start=0;
      for(int i=0;i<n;i++){ if(i==n-1 || ((cuts>>i)&1)){ for(int k=start;k<=i;k++) w[k]=start+i-k; start=i+1; } }
      u128 v=rp(w);
      // insert into top list
      if(ntop<K || v>top[ntop-1].v){
        int p = ntop<K? ntop++ : K-1;
        while(p>0 && top[p-1].v<v){ top[p]=top[p-1]; p--; }
        top[p].v=v; top[p].cuts=cuts;
      }
    }
    for(int t=0;t<ntop;t++){
      printf("n=%d rank %d value ",n,t+1); print128(top[t].v); printf(" shape (");
      int start=0, first=1;
      for(int i=0;i<n;i++) if(i==n-1 || ((top[t].cuts>>i)&1)){ printf(first?"%d":",%d",i-start+1); first=0; start=i+1; }
      printf(")\n");
    }
    return 0;
  }
  return 1;
}
