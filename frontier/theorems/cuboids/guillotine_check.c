/* guillotine_check.c -- exhaustive check of the guillotine lemma on small boxes.
   For every box L1 x L2 x L3 with 1<=L1<=L2<=L3<=M, enumerate ALL tilings by exactly k
   axis-parallel integer boxes (k = 2..K) (first-empty-cell backtracking, every box shape
   allowed, pieces unlabeled: a tiling is a set of placed boxes, enumerated once since
   the first-empty-cell order fixes the order of placement), and test whether the tiling
   has a guillotine plane (a plane x_i = h, 0<h<L_i, crossing no tile interior).
   Prints, per k, the number of tilings and the number of non-guillotine tilings.     */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int L[3], K, k;
static unsigned char g[8*8*8];
static int P[8][6]; /* x0,y0,z0,x1,y1,z1 */
static long ntil[9], nbad[9];
static int guill(int m){
    for(int ax=0;ax<3;ax++) for(int h=1;h<L[ax];h++){
        int ok=1;
        for(int i=0;i<m;i++) if(P[i][ax]<h && h<P[i][ax+3]){ok=0;break;}
        if(ok) return 1;
    }
    return 0;
}
static void dfs(int m,int start){
    int N=L[0]*L[1]*L[2], c=start;
    while(c<N && g[c]) c++;
    if(c==N){ if(m==k){ntil[k]++; if(!guill(m)) nbad[k]++;} return; }
    if(m==k) return;
    int x0=c%L[0], y0=(c/L[0])%L[1], z0=c/(L[0]*L[1]);
    for(int a=1;x0+a<=L[0];a++){
        if(g[(z0*L[1]+y0)*L[0]+x0+a-1]) break;
        for(int b=1;y0+b<=L[1];b++){
            int okb=1; for(int x=x0;x<x0+a;x++) if(g[(z0*L[1]+y0+b-1)*L[0]+x]){okb=0;break;}
            if(!okb) break;
            for(int d=1;z0+d<=L[2];d++){
                int okd=1; for(int y=y0;y<y0+b&&okd;y++)for(int x=x0;x<x0+a;x++) if(g[((z0+d-1)*L[1]+y)*L[0]+x]){okd=0;break;}
                if(!okd) break;
                for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++)for(int x=x0;x<x0+a;x++) g[(z*L[1]+y)*L[0]+x]=1;
                P[m][0]=x0;P[m][1]=y0;P[m][2]=z0;P[m][3]=x0+a;P[m][4]=y0+b;P[m][5]=z0+d;
                dfs(m+1,c);
                for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++)for(int x=x0;x<x0+a;x++) g[(z*L[1]+y)*L[0]+x]=0;
            }
        }
    }
}
int main(int argc,char**argv){
    int M=atoi(argv[1]); K=atoi(argv[2]);
    long T[9]={0},B[9]={0};
    for(L[0]=1;L[0]<=M;L[0]++)for(L[1]=L[0];L[1]<=M;L[1]++)for(L[2]=L[1];L[2]<=M;L[2]++)
      for(k=2;k<=K;k++){
        memset(ntil,0,sizeof ntil); memset(nbad,0,sizeof nbad); memset(g,0,sizeof g);
        dfs(0,0); T[k]+=ntil[k]; B[k]+=nbad[k];
        if(nbad[k] && L[2]<=3) printf("box %dx%dx%d k=%d: %ld non-guillotine of %ld\n",L[0],L[1],L[2],k,nbad[k],ntil[k]);
      }
    for(k=2;k<=K;k++) printf("k=%d: tilings=%ld non-guillotine=%ld\n",k,T[k],B[k]);
    return 0;
}
