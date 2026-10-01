// Ground truth over the full fit box: for every r in 2..6, k in 1..8, nondecreasing a_i in 1..12,
// output a 60-bit mask of b in 1..60 with P unimodal (same algorithm as tools/uni.c).
#include <stdio.h>
#include <string.h>
typedef __int128 I;
static I c[1024], d[1024];
int a[8];
void emit(int r,int k){
  int deg=0; c[0]=1;
  for(int i=0;i<k;i++){ int A=a[i], nd=deg+A-1; I s=0;
    for(int t=0;t<=nd;t++){ if(t<=deg) s+=c[t]; if(t-A>=0 && t-A<=deg) s-=c[t-A]; d[t]=s; }
    deg=nd; memcpy(c,d,sizeof(I)*(deg+1)); }
  unsigned long long mask=0;
  static I e[2048];
  for(int b=1;b<=60;b++){
    int nd=deg+r*(b-1);
    for(int t=0;t<=nd;t++){ I s=0; for(int y=0;y<b;y++){ int u=t-r*y; if(u>=0&&u<=deg) s+=c[u]; } e[t]=s; }
    int i=0; while(i<nd && e[i]<=e[i+1]) i++; while(i<nd && e[i]>=e[i+1]) i++;
    if(i==nd) mask|=1ULL<<(b-1);
  }
  printf("%d %d",r,k); for(int i=0;i<k;i++) printf(" %d",a[i]); printf(" %llx\n",mask);
}
void rec(int r,int k,int pos,int lo){
  if(pos==k){ emit(r,k); return; }
  for(int v=lo; v<=12; v++){ a[pos]=v; rec(r,k,pos+1,v); }
}
int main(){ for(int r=2;r<=6;r++) for(int k=1;k<=8;k++) rec(r,k,0,1); return 0; }
