/* Independent enumerator: all tilings of a P x Q x R integer grid by exactly K boxes.
   First-empty-cell (lex order z,y,x) for boxes 1..K-1; last box = remainder, which must be
   the box [c, c'+1) where c = lex-first free cell, c' = lex-last free cell.
   Modes:
     cube n strict      : count distinct shape-sets of 4 pairwise-distinct shapes (strict=1: all strict)
     types Pmax K       : print reduced tilings (types) of all grids up to Pmax, check guillotine
     guil Pmax K        : count tilings and non-guillotine tilings for all grids <= Pmax
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { int x0,y0,z0,x1,y1,z1; } Box;
static int P,Q,R,K;
static Box bx[8];
static int nb;
static int strictprune=0;
static long long ntil=0, nnong=0;
static int mode=0; /* 0: cube shapes, 1: types, 2: guil count */

static inline int incell(const Box*b,int x,int y,int z){return x>=b->x0&&x<b->x1&&y>=b->y0&&y<b->y1&&z>=b->z0&&z<b->z1;}
static inline int boxfree(int x0,int y0,int z0,int x1,int y1,int z1){
  if(x1>P||y1>Q||z1>R) return 0;
  for(int i=0;i<nb;i++){const Box*b=&bx[i];
    if(x0<b->x1&&b->x0<x1&&y0<b->y1&&b->y0<y1&&z0<b->z1&&b->z0<z1) return 0;}
  return 1;
}
static int firstfree(int *cx,int *cy,int *cz){
  for(int z=0;z<R;z++)for(int y=0;y<Q;y++){int x=0;
    while(x<P){int hit=-1;for(int i=0;i<nb;i++) if(incell(&bx[i],x,y,z)){hit=i;break;}
      if(hit<0){*cx=x;*cy=y;*cz=z;return 1;} x=bx[hit].x1;}}
  return 0;
}
static int lastfree(int *cx,int *cy,int *cz){
  for(int z=R-1;z>=0;z--)for(int y=Q-1;y>=0;y--){int x=P-1;
    while(x>=0){int hit=-1;for(int i=0;i<nb;i++) if(incell(&bx[i],x,y,z)){hit=i;break;}
      if(hit<0){*cx=x;*cy=y;*cz=z;return 1;} x=bx[hit].x0-1;}}
  return 0;
}
/* shape-set storage */
typedef struct { unsigned int s[5]; } SS;
static SS *store=NULL; static long long nstore=0, capstore=0;
static int cmpu(const void*a,const void*b){unsigned x=*(unsigned*)a,y=*(unsigned*)b;return x<y?-1:x>y;}
static int cmpss(const void*a,const void*b){return memcmp(a,b,sizeof(SS));}
static int isguil(void){
  /* plane x=h, 0<h<P, no box with x0<h<x1 */
  for(int ax=0;ax<3;ax++){int L=ax==0?P:ax==1?Q:R;
    for(int h=1;h<L;h++){int ok=1;
      for(int i=0;i<nb;i++){int lo=ax==0?bx[i].x0:ax==1?bx[i].y0:bx[i].z0;int hi=ax==0?bx[i].x1:ax==1?bx[i].y1:bx[i].z1;
        if(lo<h&&h<hi){ok=0;break;}}
      if(ok) return 1;}}
  return 0;
}
static void record(void){
  ntil++;
  int g=isguil(); if(!g) nnong++;
  if(mode==0){
    unsigned c[8];
    for(int i=0;i<nb;i++){int d[3]={bx[i].x1-bx[i].x0,bx[i].y1-bx[i].y0,bx[i].z1-bx[i].z0};
      /* sort */
      for(int a=0;a<3;a++)for(int b=a+1;b<3;b++) if(d[b]<d[a]){int t=d[a];d[a]=d[b];d[b]=t;}
      if(strictprune && (d[0]==d[1]||d[1]==d[2])) return;
      c[i]=(unsigned)(d[0]*4096+d[1]*64+d[2]);}
    qsort(c,nb,sizeof(unsigned),cmpu);
    for(int i=1;i<nb;i++) if(c[i]==c[i-1]) return; /* not pairwise distinct */
    if(nstore==capstore){capstore=capstore?2*capstore:1<<16;store=realloc(store,capstore*sizeof(SS));}
    SS s; memset(&s,0,sizeof s); for(int i=0;i<nb;i++) s.s[i]=c[i];
    store[nstore++]=s;
  } else if(mode==1){
    /* reduced? every interior coordinate in each axis is some box endpoint */
    int red=1;
    for(int ax=0;ax<3&&red;ax++){int L=ax==0?P:ax==1?Q:R;
      for(int h=1;h<L;h++){int f=0;for(int i=0;i<nb;i++){int lo=ax==0?bx[i].x0:ax==1?bx[i].y0:bx[i].z0;int hi=ax==0?bx[i].x1:ax==1?bx[i].y1:bx[i].z1; if(lo==h||hi==h)f=1;}
        if(!f){red=0;break;}}}
    if(red){
      printf("T %d %d %d %d",P,Q,R,g);
      for(int i=0;i<nb;i++) printf("  %d %d %d %d %d %d",bx[i].x0,bx[i].x1,bx[i].y0,bx[i].y1,bx[i].z0,bx[i].z1);
      printf("\n");
    }
  }
}
static inline int strictdims(int a,int b,int c){return a!=b&&b!=c&&a!=c;}
static void rec(int cx,int cy,int cz,long long remvol){
  if(nb==K-1){
    int ax,ay,az,ex,ey,ez;
    ax=cx;ay=cy;az=cz;
    if(!lastfree(&ex,&ey,&ez)) return;
    if(ex<ax||ey<ay||ez<az) return;
    long long v=(long long)(ex-ax+1)*(ey-ay+1)*(ez-az+1);
    if(v!=remvol) return;
    if(!boxfree(ax,ay,az,ex+1,ey+1,ez+1)) return;
    if(strictprune && !strictdims(ex-ax+1,ey-ay+1,ez-az+1)) return;
    bx[nb++]=(Box){ax,ay,az,ex+1,ey+1,ez+1};
    record();
    nb--; return;
  }
  for(int dz=1;cz+dz<=R;dz++){
    if(!boxfree(cx,cy,cz,cx+1,cy+1,cz+dz)) break;
    for(int dy=1;cy+dy<=Q;dy++){
      if(!boxfree(cx,cy,cz,cx+1,cy+dy,cz+dz)) break;
      for(int dx=1;cx+dx<=P;dx++){
        if(!boxfree(cx,cy,cz,cx+dx,cy+dy,cz+dz)) break;
        long long v=(long long)dx*dy*dz;
        if(v>=remvol) continue; /* need remaining boxes non-empty */
        if(strictprune && !strictdims(dx,dy,dz)) continue;
        bx[nb++]=(Box){cx,cy,cz,cx+dx,cy+dy,cz+dz};
        int nx,ny,nz;
        if(firstfree(&nx,&ny,&nz)) rec(nx,ny,nz,remvol-v);
        nb--;
      }
    }
  }
}
int main(int argc,char**argv){
  if(argc<2){fprintf(stderr,"usage\n");return 1;}
  if(!strcmp(argv[1],"cube")){
    int n=atoi(argv[2]); strictprune=atoi(argv[3]); K=argc>4?atoi(argv[4]):4; mode=0;
    P=Q=R=n; nb=0; ntil=0;nnong=0;
    rec(0,0,0,(long long)n*n*n);
    qsort(store,nstore,sizeof(SS),cmpss);
    long long d=0; for(long long i=0;i<nstore;i++) if(i==0||memcmp(&store[i],&store[i-1],sizeof(SS))) d++;
    printf("n=%d strict=%d K=%d tilings_counted=%lld nonguillotine=%lld distinct_sets=%lld\n",n,strictprune,K,ntil,nnong,d);
    if(argc>5){ for(long long i=0;i<nstore;i++) if(i==0||memcmp(&store[i],&store[i-1],sizeof(SS))){
        printf("S"); for(int j=0;j<K;j++){unsigned c=store[i].s[j]; printf(" %u,%u,%u",c/4096,(c/64)%64,c%64);} printf("\n");}}
  } else if(!strcmp(argv[1],"types")||!strcmp(argv[1],"guil")){
    int M=atoi(argv[2]); K=atoi(argv[3]); mode=!strcmp(argv[1],"types")?1:2;
    long long tot=0,totn=0,stot=0,stotn=0;
    for(P=1;P<=M;P++)for(Q=1;Q<=M;Q++)for(R=1;R<=M;R++){
      if((long long)P*Q*R<K) continue;
      nb=0; ntil=0; nnong=0; rec(0,0,0,(long long)P*Q*R); tot+=ntil; totn+=nnong; if(P<=Q&&Q<=R){stot+=ntil;stotn+=nnong;}
      if(mode==2 && nnong) fprintf(stderr,"grid %d %d %d: %lld tilings, %lld non-guillotine\n",P,Q,R,ntil,nnong);
    }
    fprintf(stderr,"M=%d K=%d total tilings=%lld nonguillotine=%lld ; P<=Q<=R: %lld %lld\n",M,K,tot,totn,stot,stotn);
  }
  return 0;
}
