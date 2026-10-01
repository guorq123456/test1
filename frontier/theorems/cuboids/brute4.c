/* brute4.c -- direct brute force for A386884 (strict=1) and A384311 (strict=0).
   For a given n, enumerate every SET of 4 pairwise distinct (noncongruent) shapes
   {x<=y<=z}, 1<=x,y,z<=n (strict: x<y<z), whose volumes sum to n^3, and decide
   by exhaustive backtracking on the unit-cell grid whether the n x n x n cube can be
   tiled using each shape exactly once, in any of its orientations, at any integer
   position.  No guillotine assumption is made: the search places, at each step, a
   piece whose minimal corner is the lexicographically first empty cell (z,y,x order),
   which is complete for tilings with integer coordinates (see proof.md, Lemma 6).
   Usage: brute4 n strict   -> prints n count number_of_volume_candidates          */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int n, N3;
static unsigned char *grid;
static int sh[4][3];           /* the 4 shapes of the candidate */
static int nor[4], ori[4][6][3];
static int dfs(int used, int start){
    if(used==15) return 1;
    int c=start; while(c<N3 && grid[c]) c++;
    if(c==N3) return 0;
    int x0=c%n, y0=(c/n)%n, z0=c/(n*n);
    for(int p=0;p<4;p++) if(!(used>>p&1)){
        for(int o=0;o<nor[p];o++){
            int a=ori[p][o][0], b=ori[p][o][1], d=ori[p][o][2];
            if(x0+a>n||y0+b>n||z0+d>n) continue;
            int ok=1;
            for(int z=z0;z<z0+d&&ok;z++)for(int y=y0;y<y0+b&&ok;y++)for(int x=x0;x<x0+a;x++)
                if(grid[(z*n+y)*n+x]){ok=0;break;}
            if(!ok) continue;
            for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++)for(int x=x0;x<x0+a;x++) grid[(z*n+y)*n+x]=1;
            int r=dfs(used|1<<p, c);
            for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++)for(int x=x0;x<x0+a;x++) grid[(z*n+y)*n+x]=0;
            if(r) return 1;
        }
    }
    return 0;
}
static void setori(int p){
    int perm[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
    nor[p]=0;
    for(int i=0;i<6;i++){
        int a=sh[p][perm[i][0]], b=sh[p][perm[i][1]], d=sh[p][perm[i][2]], dup=0;
        for(int j=0;j<nor[p];j++) if(ori[p][j][0]==a&&ori[p][j][1]==b&&ori[p][j][2]==d) dup=1;
        if(!dup){ori[p][nor[p]][0]=a;ori[p][nor[p]][1]=b;ori[p][nor[p]][2]=d;nor[p]++;}
    }
}
int main(int argc,char**argv){
    n=atoi(argv[1]); int strict=atoi(argv[2]); int verbose=argc>3?atoi(argv[3]):0;
    N3=n*n*n; grid=calloc(N3,1);
    int S[20000][3], V[20000], m=0;
    for(int x=1;x<=n;x++)for(int y=x;y<=n;y++)for(int z=y;z<=n;z++){
        if(strict && (x==y||y==z)) continue;
        S[m][0]=x;S[m][1]=y;S[m][2]=z;V[m]=x*y*z;m++;
    }
    long cand=0, cnt=0;
    for(int i=0;i<m;i++)for(int j=i+1;j<m;j++){
        int vij=V[i]+V[j]; if(vij>=N3) continue;
        for(int k=j+1;k<m;k++){
            int vk=vij+V[k]; if(vk>=N3) continue;
            for(int l=k+1;l<m;l++){
                if(vk+V[l]!=N3) continue;
                cand++;
                int idx[4]={i,j,k,l};
                for(int p=0;p<4;p++){for(int q=0;q<3;q++) sh[p][q]=S[idx[p]][q]; setori(p);}
                memset(grid,0,N3);
                if(dfs(0,0)){cnt++; if(verbose) printf("  {(%d,%d,%d),(%d,%d,%d),(%d,%d,%d),(%d,%d,%d)}\n",
                    S[i][0],S[i][1],S[i][2],S[j][0],S[j][1],S[j][2],S[k][0],S[k][1],S[k][2],S[l][0],S[l][1],S[l][2]);}
            }
        }
    }
    printf("%d %ld %ld\n",n,cnt,cand);
    return 0;
}
