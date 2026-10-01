// Exact q-Fibonomial [m+n choose n]_F = prod_{k=1}^n (1-q^{F_{m+k}})/(1-q^{F_k}), truncated at degree floor(N/2),
// multi-limb two's complement (64-bit limbs). Checks nonnegativity + c_0<=...<=c_{floor(N/2)} (=> unimodal by symmetry),
// and prints the total coefficient sum (2*sum_{t<N/2} c_t + [N even] c_{N/2}) in hex for cross-checking against the Fibonomial.
// usage: fibq m n
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
typedef unsigned long long u64; typedef unsigned __int128 u128;
static int L;
static inline void sub_into(u64 *x,const u64 *y){ // x -= y
  u64 br=0; for(int i=0;i<L;i++){ u128 d=(u128)x[i]-y[i]-br; x[i]=(u64)d; br=(d>>64)?1:0; } }
static inline void add_into(u64 *x,const u64 *y){ u64 cy=0; for(int i=0;i<L;i++){ u128 s=(u128)x[i]+y[i]+cy; x[i]=(u64)s; cy=(u64)(s>>64);} }
static inline int is_neg(const u64 *x){ return (x[L-1]>>63)&1; }
static inline int less(const u64 *x,const u64 *y){ // signed x<y
  int nx=is_neg(x), ny=is_neg(y); if(nx!=ny) return nx;
  for(int i=L-1;i>=0;i--){ if(x[i]!=y[i]) return x[i]<y[i]; } return 0; }
int main(int argc,char**argv){
  int m=atoi(argv[1]), n=atoi(argv[2]);
  u64 F[100]; F[0]=0;F[1]=1; for(int i=2;i<92;i++) F[i]=F[i-1]+F[i-2];
  u64 N=0; double bits=0;
  for(int k=1;k<=n;k++){ N+=F[m+k]-F[k]; bits+=log2((double)F[m+k])-log2((double)F[k]); }
  L=(int)((bits+4)/64)+1;
  u64 len=N/2+1;
  u64 *c=calloc((size_t)len*L,8); if(!c){fprintf(stderr,"oom\n");return 1;}
  c[0]=1;
  for(int k=1;k<=n;k++){
    u64 A=F[m+k], B=F[k];
    if(A<len) for(u64 t=len-1;t>=A;t--){ sub_into(c+t*L,c+(t-A)*L); if(t==A) break; }
    for(u64 t=B;t<len;t++) add_into(c+t*L,c+(t-B)*L);
  }
  long long firstneg=-1, firstdesc=-1;
  for(u64 t=0;t<len;t++){ if(is_neg(c+t*L)){firstneg=t;break;} }
  for(u64 t=0;t+1<len;t++){ if(less(c+(t+1)*L,c+t*L)){firstdesc=t;break;} }
  // total sum
  u64 *s=calloc(L+1,8);
  for(u64 t=0;t<len;t++) add_into(s,c+t*L);
  add_into(s,s); // *2
  if(N%2==0){ sub_into(s,c+(len-1)*L); }
  printf("m=%d n=%d N=%llu limbs=%d bits=%.1f firstneg=%lld firstdesc=%lld %s sum=0x",m,n,N,L,bits,firstneg,firstdesc,
     (firstneg<0&&firstdesc<0)?"UNIMODAL":"NOT_UNIMODAL");
  int top=L-1; while(top>0&&s[top]==0) top--;
  printf("%llx",s[top]); for(int i=top-1;i>=0;i--) printf("%016llx",s[i]); printf("\n");
  if(argc>3){ // dump coefficients (low limb only, for small tests)
    FILE*f=fopen(argv[3],"w"); for(u64 t=0;t<len;t++) fprintf(f,"%llu\n",c[t*L]); fclose(f);}
  return 0;
}
