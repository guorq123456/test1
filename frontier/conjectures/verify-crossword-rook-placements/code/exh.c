// Exhaustive |RP(Grid(w))| over S_n by DFS over rows with shared prefixes.
// Output: histogram value->count (to file), max value and maximizers, and
// skew-merged check (3412/2143 avoidance) for perms with value <=2 plus count of skew-merged perms
// (brute-force pattern check over all perms for n<=EXH_PAT).
// Parallelized over first value w(1) via fork-free OpenMP.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
typedef uint64_t u64;
static int n;
typedef struct { uint32_t *m; u64 *v; int len; } vec;
typedef struct {
  vec depth[3*24+2];
  u64 *scr; uint8_t *flg; uint32_t *tl; int tlen;
  int w[24]; int used;
  // results
  u64 *hist_v; u64 *hist_c; int hsize, hcap; // simple open addressing
  u64 maxv; int nmax; int maxw[64][24];
  u64 cnt1, cnt2, skew_le2, nonskew_le2, nperm;
} ctx;

static void hadd(ctx*c, u64 v){
  // open addressing hash
  if(c->hsize*2 >= c->hcap){
    int oc=c->hcap; u64*ov=c->hist_v,*occ=c->hist_c; c->hcap=oc?oc*2:1024;
    c->hist_v=calloc(c->hcap,8); c->hist_c=calloc(c->hcap,8); c->hsize=0;
    for(int i=0;i<oc;i++) if(occ[i]){ u64 x=ov[i]; u64 h=(x*0x9E3779B97F4A7C15ull)&(c->hcap-1);
      while(c->hist_c[h]) h=(h+1)&(c->hcap-1); c->hist_v[h]=x; c->hist_c[h]=occ[i]; c->hsize++; }
    free(ov); free(occ);
  }
  u64 h=(v*0x9E3779B97F4A7C15ull)&(c->hcap-1);
  while(c->hist_c[h] && c->hist_v[h]!=v) h=(h+1)&(c->hcap-1);
  if(!c->hist_c[h]){ c->hist_v[h]=v; c->hsize++; }
  c->hist_c[h]++;
}

static inline void sadd(ctx*c, uint32_t T, u64 v){
  if(!c->flg[T]){ c->flg[T]=1; c->tl[c->tlen++]=T; c->scr[T]=0; }
  c->scr[T]+=v;
}
static void flush(ctx*c, vec*out){
  out->len=c->tlen;
  for(int k=0;k<c->tlen;k++){ uint32_t T=c->tl[k]; out->m[k]=T; out->v[k]=c->scr[T]; c->flg[T]=0; }
  c->tlen=0;
}
static int skewmerged(const int*w){
  // avoid 3412 and 2143: O(n^4) fine for few
  for(int a=0;a<n;a++)for(int b=a+1;b<n;b++)for(int d=b+1;d<n;d++)for(int e=d+1;e<n;e++){
    int x=w[a],y=w[b],z=w[d],t=w[e];
    // 3412: z<t<x<y
    if(z<t && t<x && x<y) return 0;
    // 2143: y<x<t<z? pattern 2143: second<first<fourth<third
    if(y<x && x<t && t<z) return 0;
  }
  return 1;
}
static void record(ctx*c, u64 v){
  c->nperm++; hadd(c,v);
  if(v>c->maxv){ c->maxv=v; c->nmax=0; }
  if(v==c->maxv && c->nmax<64){ memcpy(c->maxw[c->nmax], c->w, sizeof(int)*n); c->nmax++; }
  if(v<=2){ if(v==1) c->cnt1++; else if(v==2) c->cnt2++;
    if(skewmerged(c->w)) c->skew_le2++; else { c->nonskew_le2++; } }
  if(v==0){ fprintf(stderr,"ZERO!\n"); }
}
// apply row i with black column col to vec in -> depth slot; returns pointer
static void step(ctx*c, int i, int col, vec*in, vec*out){
  vec *a=&c->depth[3*i], *b=&c->depth[3*i+1];
  for(int k=0;k<in->len;k++){ uint32_t S=in->m[k]; if(!((S>>col)&1)) continue;
    uint32_t T=(i<n-1)?(S&~(1u<<col)):S; sadd(c,T,in->v[k]); }
  flush(c,a);
  vec *src=a, *dst=b;
  if(col>0){ for(int k=0;k<src->len;k++){ uint32_t S=src->m[k]; u64 v=src->v[k];
      for(int j=0;j<col;j++) if(!((S>>j)&1)) sadd(c,S|(1u<<j),v); }
    flush(c,dst); vec*t=src; src=dst; dst=t; }
  if(col<n-1){ for(int k=0;k<src->len;k++){ uint32_t S=src->m[k]; u64 v=src->v[k];
      for(int j=col+1;j<n;j++) if(!((S>>j)&1)) sadd(c,S|(1u<<j),v); }
    flush(c,out); return; }
  // copy src to out
  out->len=src->len; memcpy(out->m,src->m,4*src->len); memcpy(out->v,src->v,8*src->len);
}
static void dfs(ctx*c, int i, vec*in){
  for(int col=0;col<n;col++){ if((c->used>>col)&1) continue;
    c->w[i]=col+1; c->used|=1<<col;
    vec*out=&c->depth[3*i+2];
    step(c,i,col,in,out);
    if(i==n-1){ uint32_t full=(1u<<n)-1; u64 v=0; for(int k=0;k<out->len;k++) if(out->m[k]==full) v+=out->v[k]; record(c,v); }
    else if(out->len) dfs(c,i+1,out);
    else { /* dead prefix: all completions give 0 -- impossible per Prop 3.3 */ fprintf(stderr,"dead prefix\n"); }
    c->used&=~(1<<col);
  }
}
int main(int argc,char**argv){
  n=atoi(argv[1]); const char*histfile=argv[2];
  int nt=omp_get_max_threads();
  ctx *cs=calloc(n,sizeof(ctx));
  #pragma omp parallel for schedule(dynamic,1)
  for(int f=0;f<n;f++){
    ctx*c=&cs[f]; size_t M=(size_t)1<<n;
    for(int d=0;d<3*n+2;d++){ c->depth[d].m=malloc(4*M); c->depth[d].v=malloc(8*M); }
    c->scr=malloc(8*M); c->flg=calloc(M,1); c->tl=malloc(4*M);
    vec init; init.m=malloc(4); init.v=malloc(8); init.len=1; init.m[0]=1u<<f; init.v[0]=1;
    if(n==1){ c->w[0]=1; record(c,1); continue; }
    c->w[0]=f+1; c->used=1<<f;
    vec*out=&c->depth[2]; step(c,0,f,&init,out); dfs(c,1,out);
  }
  // merge
  ctx T; memset(&T,0,sizeof T);
  u64 maxv=0; for(int f=0;f<n;f++) if(cs[f].maxv>maxv) maxv=cs[f].maxv;
  u64 nperm=0,c1=0,c2=0,sk=0,nsk=0;
  for(int f=0;f<n;f++){ ctx*c=&cs[f]; nperm+=c->nperm; c1+=c->cnt1; c2+=c->cnt2; sk+=c->skew_le2; nsk+=c->nonskew_le2;
    for(int h=0;h<c->hcap;h++) if(c->hist_c[h]){ for(u64 r=0;r<1;r++){} 
      // merge into T
      u64 v=c->hist_v[h], cnt=c->hist_c[h];
      if(T.hsize*2>=T.hcap) { hadd(&T,v); T.hist_c[0]+=0; /* trigger resize */ 
        // undo extra count
        u64 hh=(v*0x9E3779B97F4A7C15ull)&(T.hcap-1); while(T.hist_v[hh]!=v) hh=(hh+1)&(T.hcap-1); T.hist_c[hh]+=cnt-1; }
      else { u64 hh=(v*0x9E3779B97F4A7C15ull)&(T.hcap-1); while(T.hist_c[hh] && T.hist_v[hh]!=v) hh=(hh+1)&(T.hcap-1);
        if(!T.hist_c[hh]){T.hist_v[hh]=v; T.hsize++;} T.hist_c[hh]+=cnt; }
    }
  }
  printf("n=%d perms=%llu max=%llu count1=%llu count2=%llu le2_skewmerged=%llu le2_NOT_skewmerged=%llu distinct_values=%d\n",
    n,(unsigned long long)nperm,(unsigned long long)maxv,(unsigned long long)c1,(unsigned long long)c2,(unsigned long long)sk,(unsigned long long)nsk,T.hsize);
  for(int f=0;f<n;f++) if(cs[f].maxv==maxv) for(int k=0;k<cs[f].nmax;k++){ printf("maximizer:"); for(int i=0;i<n;i++) printf(" %d",cs[f].maxw[k][i]); printf("\n"); }
  FILE*fp=fopen(histfile,"w");
  for(int h=0;h<T.hcap;h++) if(T.hist_c[h]) fprintf(fp,"%llu %llu\n",(unsigned long long)T.hist_v[h],(unsigned long long)T.hist_c[h]);
  fclose(fp);
  return 0;
}
