// scan.c: enumerate the fit box r in 2..6, multisets a (size<=8, entries 2..12, none divisible by r;
// entries equal to 1 are trivial factors and are omitted -- tuples with 1's give identical P),
// b in 1..60. For each instance compute P and record unimodality and violation location.
// Output files:
//   tuples.txt : r k a1..ak mask_lo mask_hi   (bit b-1 set iff unimodal at b)
//   viol.txt   : r k a1..ak b D R N t s ndips  (only non-unimodal instances)
//     D=deg p=sum(a_i-1), R=r(b-1), N=D+R, t=first strict descent index (c_t>c_{t+1}),
//     s=first strict ascent index after t (c_s<c_{s+1}), ndips=number of strict "valleys"
//     (maximal runs where a strict descent is later followed by a strict ascent, counted over whole seq)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef long long L;
static int vals[16], nv; static int cur[16]; static int r;
static FILE *ft,*fv;
static L p[1024], c[2048];
static void process(int k){
  // build p
  int deg=0; p[0]=1;
  static L d[1024];
  for(int i=0;i<k;i++){int A=cur[i]; int nd=deg+A-1; L s=0;
    for(int t=0;t<=nd;t++){ if(t<=deg) s+=p[t]; if(t-A>=0&&t-A<=deg) s-=p[t-A]; d[t]=s;}
    deg=nd; memcpy(p,d,sizeof(L)*(deg+1));}
  int D=deg;
  memset(c,0,sizeof(c));
  unsigned long long mask=0;
  for(int b=1;b<=60;b++){
    int R=r*(b-1);
    for(int j=0;j<=D;j++) c[R+j]+=p[j];
    int N=D+R;
    int i=0; while(i<N && c[i]<=c[i+1]) i++; int t=i; while(i<N && c[i]>=c[i+1]) i++;
    if(i==N){ mask|=1ULL<<(b-1); continue; }
    // t: index after the weakly increasing run; first strict descent is at first idx>=t with c>c+1
    int td=t; while(td<N && !(c[td]>c[td+1])) td++; // first strict descent
    int s=td; while(s<N && !(c[s]<c[s+1])) s++;     // first strict ascent after it
    // count valleys: scan direction changes on strict moves
    int ndips=0, dir=0; for(int j=0;j<N;j++){ if(c[j]<c[j+1]){ if(dir==-1) ndips++; dir=1;} else if(c[j]>c[j+1]) dir=-1; }
    fprintf(fv,"%d %d",r,k); for(int q=0;q<k;q++) fprintf(fv," %d",cur[q]);
    fprintf(fv," %d %d %d %d %d %d %d\n",b,D,R,N,td,s,ndips);
  }
  fprintf(ft,"%d %d",r,k); for(int q=0;q<k;q++) fprintf(ft," %d",cur[q]);
  fprintf(ft," %llu\n",mask);
}
static void rec(int k,int start,int maxk){
  process(k);
  if(k==maxk) return;
  for(int i=start;i<nv;i++){cur[k]=vals[i]; rec(k+1,i,maxk);}
}
int main(){
  ft=fopen("/tmp/claude-0/qu/explore/E7/tuples.txt","w");
  fv=fopen("/tmp/claude-0/qu/explore/E7/viol.txt","w");
  for(r=2;r<=6;r++){ nv=0; for(int a=2;a<=12;a++) if(a%r) vals[nv++]=a; rec(0,0,8);}
  fclose(ft); fclose(fv); return 0;
}
