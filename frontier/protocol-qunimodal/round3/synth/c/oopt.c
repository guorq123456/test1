// Float (long double) optimizer: minimise the M-margin  min_C (E_{J*-2}-|A_C| - E_{J*+1}) / E_{J*-2}
// Usage: mopt seed iters r a1 ... ak      prints progress; final instance.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef long double LD;
static int r,k; static long D,F;
static LD *al,*pre,*dl,*E,*tau; static long *yl;
static unsigned long long rs;
static unsigned long long rnd(){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
static long cap=0;
static void ensure(long X){ if(X+8>cap){ cap=2*(X+8); al=realloc(al,sizeof(LD)*cap); pre=realloc(pre,sizeof(LD)*(cap+1)); dl=realloc(dl,sizeof(LD)*cap);} }
typedef struct { LD marg, slack, ratio; long Jst, Cm; } Res;
static Res eval(int *a){
  Res R; D=0;F=0; for(int i=0;i<k;i++){D+=a[i]-1;F+=a[i]/r;}
  long X=(D+1)/2; ensure(X+2);
  al[0]=1; long len=1;
  for(int i=0;i<k;i++){ int ai=a[i]; if(ai<=1) continue; long nlen=len+ai-1; if(nlen>X+1) nlen=X+1;
    pre[0]=0; for(long j=0;j<nlen;j++) pre[j+1]=pre[j]+(j<len?al[j]:0);
    for(long j=0;j<nlen;j++){ long lo=j-ai+1; if(lo<0) lo=0; al[j]=pre[j+1]-pre[lo]; } len=nlen; }
  dl[0]=al[0]; for(long x=1;x<=X;x++) dl[x]=al[x]-al[x-1];
  // tau via residues (cyclic)
  LD *v=tau, *w=malloc(sizeof(LD)*r), *ps=malloc(sizeof(LD)*(2*r+1));
  for(int t=0;t<r;t++) v[t]=0; v[0]=1; v[1%r]-=1;
  for(int i=0;i<k;i++){ int s=a[i]%r; if(s<=1) continue;
    ps[0]=0; for(int t=0;t<2*r;t++) ps[t+1]=ps[t]+v[t%r];
    for(int t=0;t<r;t++){ // w_t = sum_{j<s} v_{t-j} = sum over indices t-s+1..t  (shift by r)
      w[t]=ps[t+r+1]-ps[t+r-s+1]; }
    memcpy(v,w,sizeof(LD)*r); }
  free(w); free(ps);
  long maxL=2*(D+1)/r+12; static LD *Eb=NULL; static long ecap=0; if(maxL+8>ecap){ecap=maxL+8; Eb=realloc(Eb,sizeof(LD)*ecap); yl=realloc(yl,sizeof(long)*ecap);} E=Eb;
  long Jst=1L<<60;
  // pass 1: J*
  for(int pass=0;pass<2;pass++){
   R.marg=1e30; R.slack=1e30; R.ratio=0; R.Cm=-1;
   for(int C=1;C<r;C++){ if(((C-(D+1))%2+2)%2) continue;
    long L=0; for(long kk=0;;kk++){ long Z=(kk/2)*2L*r+((kk%2==0)?C:2L*r-C); if(Z>D+1) break; yl[L++]=(D+1-Z)/2; }
    long M=L+6; E[M]=0;E[M+1]=0; for(long j=M-1;j>=0;j--) E[j]=E[j+2]+(j<L?dl[yl[j]]:0);
    long u=(((D+1-C)/2)%r+r)%r; LD Aa=fabsl(tau[u]); if(Aa==0) continue;
    if(pass==0){ for(long J=F%2; J<M+2; J+=2){ LD EJ=J<M?E[J]:0; if(EJ<Aa){ if(J<Jst) Jst=J; break; } } }
    else { long j=Jst-4; if(j<0) continue; LD Tj=(j<M?E[j]:0)-(j+1<M?E[j+1]:0);
      LD m=(Tj-Aa)/Aa; if(m<R.marg){R.marg=m; R.slack=Tj; R.ratio=Aa; R.Cm=C;} }
   }
  }
  R.Jst=Jst; return R;
}
int main(int argc,char**argv){
  rs=atoll(argv[1])*2654435761ULL+1; long iters=atol(argv[2]); r=atoi(argv[3]); k=argc-4;
  int *a=malloc(sizeof(int)*k), *b=malloc(sizeof(int)*k); for(int i=0;i<k;i++) a[i]=atoi(argv[4+i]);
  tau=malloc(sizeof(LD)*r);
  Res cur=eval(a);
  printf("start J*=%ld marg=%.3Le slack=%.3Le ratio=%.3Le C=%ld\n",cur.Jst,cur.marg,cur.slack,cur.ratio,cur.Cm); fflush(stdout);
  for(long it=0;it<iters;it++){
    memcpy(b,a,sizeof(int)*k);
    int i=rnd()%k, typ=rnd()%3;
    if(typ==0){ b[i]+=(rnd()%2)?1:-1; }
    else { int j=rnd()%k; if(j==i) continue; int d=1+rnd()%3; b[i]+=d; b[j]-=d; }
    int ok=1; for(int t=0;t<k;t++) if(b[t]<2||b[t]%r==0) ok=0; if(!ok) continue;
    Res nw=eval(b);
    if(nw.marg<cur.marg){ memcpy(a,b,sizeof(int)*k); cur=nw;
      if(it%1==0){ printf("it=%ld J*=%ld marg=%.3Le slack=%.3Le ratio=%.3Le C=%ld\n",it,cur.Jst,cur.marg,cur.slack,cur.ratio,cur.Cm); fflush(stdout);} 
      if(cur.marg<0){ printf("CANDIDATE r=%d a=",r); for(int t=0;t<k;t++) printf("%d ",a[t]); printf("\n"); fflush(stdout); break; } }
  }
  printf("final r=%d a=",r); for(int t=0;t<k;t++) printf("%d ",a[t]); printf("\n");
  return 0;
}
