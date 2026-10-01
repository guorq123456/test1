/* brute4b.c -- same algorithm and output as brute4.c (direct brute force from the OEIS
   definition, no structural assumption), but faster: shapes sorted by volume with a volume
   index for the 4th shape, and the grid stored as 64-bit row masks (n <= 64).
   Usage: brute4b n strict [verbose]   -> prints n count number_of_volume_candidates     */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static int n, N3;
static uint64_t R[64][64];      /* R[z][y] bit x = cell occupied */
static int sh[4][3], nor[4], ori[4][6][3];
static int dfs(int used, int zs, int ys){
    if(used==15) return 1;
    int z0=-1,y0=-1,x0=-1; uint64_t full = (n==64)?~0ULL:((1ULL<<n)-1);
    for(int z=zs; z<n && z0<0; z++) for(int y=(z==zs?ys:0); y<n; y++)
        if(R[z][y]!=full){ z0=z; y0=y; x0=__builtin_ctzll(~R[z][y]); break; }
    if(z0<0) return 0;
    for(int p=0;p<4;p++) if(!(used>>p&1)){
        for(int o=0;o<nor[p];o++){
            int a=ori[p][o][0], b=ori[p][o][1], d=ori[p][o][2];
            if(x0+a>n||y0+b>n||z0+d>n) continue;
            uint64_t m = ((a==64)?~0ULL:((1ULL<<a)-1))<<x0;
            int ok=1;
            for(int z=z0;z<z0+d&&ok;z++)for(int y=y0;y<y0+b;y++) if(R[z][y]&m){ok=0;break;}
            if(!ok) continue;
            for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++) R[z][y]|=m;
            int r=dfs(used|1<<p, z0, y0);
            for(int z=z0;z<z0+d;z++)for(int y=y0;y<y0+b;y++) R[z][y]&=~m;
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
static int S[50000][3], V[50000];
static int cmpv(const void*A,const void*B){ const int*a=A,*b=B; int va=a[0]*a[1]*a[2], vb=b[0]*b[1]*b[2];
    if(va!=vb) return va-vb; for(int i=0;i<3;i++) if(a[i]!=b[i]) return a[i]-b[i]; return 0; }
int main(int argc,char**argv){
    n=atoi(argv[1]); int strict=atoi(argv[2]); int verbose=argc>3?atoi(argv[3]):0;
    N3=n*n*n; int m=0;
    for(int x=1;x<=n;x++)for(int y=x;y<=n;y++)for(int z=y;z<=n;z++){
        if(strict && (x==y||y==z)) continue;
        S[m][0]=x;S[m][1]=y;S[m][2]=z;m++;
    }
    qsort(S,m,sizeof S[0],cmpv);
    for(int i=0;i<m;i++) V[i]=S[i][0]*S[i][1]*S[i][2];
    int *first=malloc(sizeof(int)*(N3+2));      /* first[v] = least index with V >= v */
    for(int v=0,i=0; v<=N3+1; v++){ while(i<m && V[i]<v) i++; first[v]=i; }
    long cand=0, cnt=0;
    for(int i=0;i<m;i++){ if(4*V[i]>N3) break;
     for(int j=i+1;j<m;j++){ int vij=V[i]+V[j]; if(vij+2*V[j]>N3) break;
      for(int k=j+1;k<m;k++){ int vk=vij+V[k], r=N3-vk; if(r<V[k]) break;
        for(int l=(first[r]>k+1?first[r]:k+1); l<m && V[l]==r; l++){
            cand++;
            int idx[4]={i,j,k,l};
            for(int p=0;p<4;p++){for(int q=0;q<3;q++) sh[p][q]=S[idx[p]][q]; setori(p);}
            memset(R,0,sizeof R);
            if(dfs(0,0,0)){cnt++; if(verbose){ printf(" ");
                for(int p=0;p<4;p++) printf("%s(%d,%d,%d)",p?",":" {",sh[p][0],sh[p][1],sh[p][2]); printf("}\n");}}
        }
      }
     }
    }
    printf("%d %ld %ld\n",n,cnt,cand);
    return 0;
}
