/* Count distinct shape-sets from reduced 4-box tiling types (types4.txt) for each n.
   usage: typecount strict nmin nmax  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { int P,Q,R; int b[4][6]; } Type;
static Type T[1000]; static int nt=0;
typedef struct { unsigned long long a,b; } Key;
static Key *keys; static long long nk, capk;
static int cmpk(const void*x,const void*y){const Key*p=x,*q=y; if(p->a!=q->a) return p->a<q->a?-1:1; if(p->b!=q->b) return p->b<q->b?-1:1; return 0;}
static int strict;
static int n;
/* combos */
static int ncomb(int L,int arr[][8]){ /* all strictly increasing sequences 0=c0<c1<..<cL=n */
  int cnt=0; int c[8]; c[0]=0; c[L]=n;
  if(L==1){arr[cnt][0]=0;arr[cnt][1]=n;return 1;}
  /* iterate interior L-1 values from 1..n-1 */
  int m=L-1; int idx[8]; for(int i=0;i<m;i++) idx[i]=i+1;
  if(m>n-1) return 0;
  while(1){
    c[0]=0; for(int i=0;i<m;i++) c[i+1]=idx[i]; c[L]=n;
    memcpy(arr[cnt],c,sizeof(int)*(L+1)); cnt++;
    int i=m-1; while(i>=0 && idx[i]==n-1-(m-1-i)) i--;
    if(i<0) break; idx[i]++; for(int j=i+1;j<m;j++) idx[j]=idx[j-1]+1;
  }
  return cnt;
}
static int (*CX)[8],(*CY)[8],(*CZ)[8];
int main(int argc,char**argv){
  strict=atoi(argv[1]); int nmin=atoi(argv[2]), nmax=atoi(argv[3]);
  FILE*f=fopen(argc>4?argv[4]:"types4.txt","r"); char tag[4];
  while(fscanf(f,"%3s",tag)==1){Type*t=&T[nt]; int g; fscanf(f,"%d %d %d %d",&t->P,&t->Q,&t->R,&g);
    for(int i=0;i<4;i++) for(int j=0;j<6;j++) fscanf(f,"%d",&t->b[i][j]); nt++;}
  fclose(f);
  /* filter for strict: drop types where a box spans full extent in 2 axes */
  int use[1000]; int nuse=0;
  for(int i=0;i<nt;i++){use[i]=1; if(strict){ for(int k=0;k<4;k++){int full=0; Type*t=&T[i];
        if(t->b[k][0]==0&&t->b[k][1]==t->P) full++; if(t->b[k][2]==0&&t->b[k][3]==t->Q) full++; if(t->b[k][4]==0&&t->b[k][5]==t->R) full++;
        if(full>=2) use[i]=0;}} nuse+=use[i];}
  fprintf(stderr,"types=%d used=%d\n",nt,nuse);
  long long maxc=200000000LL/8;
  CX=malloc(sizeof(int[8])*2000000); CY=malloc(sizeof(int[8])*2000000); CZ=malloc(sizeof(int[8])*2000000);
  for(n=nmin;n<=nmax;n++){
    nk=0;
    for(int ti=0;ti<nt;ti++){ if(!use[ti]) continue; Type*t=&T[ti];
      int nx=ncomb(t->P,CX), ny=ncomb(t->Q,CY), nz=ncomb(t->R,CZ);
      for(int ix=0;ix<nx;ix++)for(int iy=0;iy<ny;iy++)for(int iz=0;iz<nz;iz++){
        unsigned c[4]; int ok=1;
        for(int k=0;k<4;k++){int*bb=t->b[k];
          int d[3]={CX[ix][bb[1]]-CX[ix][bb[0]],CY[iy][bb[3]]-CY[iy][bb[2]],CZ[iz][bb[5]]-CZ[iz][bb[4]]};
          for(int a=0;a<3;a++)for(int b=a+1;b<3;b++) if(d[b]<d[a]){int tt=d[a];d[a]=d[b];d[b]=tt;}
          if(strict&&(d[0]==d[1]||d[1]==d[2])){ok=0;break;}
          c[k]=(unsigned)((d[0]*256+d[1])*256+d[2]);}
        if(!ok) continue;
        for(int a=0;a<4;a++)for(int b=a+1;b<4;b++) if(c[b]<c[a]){unsigned tt=c[a];c[a]=c[b];c[b]=tt;}
        if(c[0]==c[1]||c[1]==c[2]||c[2]==c[3]) continue;
        if(nk==capk){capk=capk?2*capk:1<<20; keys=realloc(keys,capk*sizeof(Key));}
        keys[nk].a=((unsigned long long)c[0]<<32)|c[1]; keys[nk].b=((unsigned long long)c[2]<<32)|c[3]; nk++;
      }
    }
    qsort(keys,nk,sizeof(Key),cmpk);
    long long d=0; for(long long i=0;i<nk;i++) if(i==0||cmpk(&keys[i],&keys[i-1])) d++;
    printf("%d %lld\n",n,d); fflush(stdout);
  }
  return 0;
}
