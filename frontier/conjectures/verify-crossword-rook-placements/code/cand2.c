// Second, faster enumeration of Conj 3.9 minimal candidates:
// w such that the ONLY occurrence of 3412 or 2143 is the quadruple {first entry, value n, value 1, last entry}.
// (Equivalent to: w not skew-merged, and deleting first / last / value 1 / value n each yields skew-merged.)
// Place the four special entries first, then fill middle positions left to right with pruning.
#include <stdio.h>
#include <stdlib.h>
static int n, w[40], usedv;   // w[pos] = value or 0 if unplaced (positions 1..n)
static long long ncand=0, nodes=0;
static int sp[4]; // special positions
static int isbad(int a,int b,int c,int d){ // values in position order
  if(c<d && d<a && a<b) return 1; // 3412
  if(b<a && a<d && d<c) return 1; // 2143
  return 0;
}
static int special(int p1,int p2,int p3,int p4){ // positions sorted
  int s[4]={sp[0],sp[1],sp[2],sp[3]}; // sorted already
  return p1==s[0]&&p2==s[1]&&p3==s[2]&&p4==s[3];
}
// check all quadruples among placed positions that include position s
static int ok_with(int s){
  int P[40],m=0; for(int i=1;i<=n;i++) if(w[i]) P[m++]=i;
  for(int a=0;a<m;a++)for(int b=a+1;b<m;b++)for(int c=b+1;c<m;c++)for(int d=c+1;d<m;d++){
    int pa=P[a],pb=P[b],pc=P[c],pd=P[d];
    if(pa!=s&&pb!=s&&pc!=s&&pd!=s) continue;
    if(isbad(w[pa],w[pb],w[pc],w[pd]) && !special(pa,pb,pc,pd)) return 0;
  }
  return 1;
}
static void dfs(int s){
  nodes++;
  while(s<=n && w[s]) s++;
  if(s>n){ ncand++; for(int i=1;i<=n;i++) printf("%d ",w[i]); printf("\n"); return; }
  for(int v=2;v<n;v++){ if((usedv>>v)&1) continue; w[s]=v; usedv|=1<<v;
    if(ok_with(s)) dfs(s+1);
    w[s]=0; usedv&=~(1<<v); }
}
static void sort4(int*a){ for(int i=0;i<4;i++)for(int j=i+1;j<4;j++) if(a[j]<a[i]){int t=a[i];a[i]=a[j];a[j]=t;} }
int main(int argc,char**argv){
  n=atoi(argv[1]);
  for(int type=0;type<2;type++)
  for(int x=2;x<n;x++)for(int y=2;y<n;y++){ if(x==y) continue;
    if(type==0 && !(y<x)) continue; // 3412: x=3,n=4,1=1,y=2
    if(type==1 && !(x<y)) continue; // 2143: x=2,1=1,n=4,y=3
    for(int q=2;q<n;q++)for(int p=2;p<n;p++){ if(p==q) continue;
      if(type==0 && !(q<p)) continue; // n before 1
      if(type==1 && !(p<q)) continue; // 1 before n
      for(int i=0;i<=n;i++) w[i]=0; usedv=0;
      w[1]=x; w[n]=y; w[p]=1; w[q]=n; usedv=(1<<x)|(1<<y)|(1<<1)|(1<<n);
      sp[0]=1; sp[1]=p; sp[2]=q; sp[3]=n; sort4(sp);
      if(!isbad(w[sp[0]],w[sp[1]],w[sp[2]],w[sp[3]])) continue;
      dfs(2);
    }
  }
  fprintf(stderr,"n=%d candidates=%lld nodes=%lld\n",n,ncand,nodes);
  return 0;
}
