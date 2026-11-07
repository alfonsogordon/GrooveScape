#include "../firmware/audio/bass_dsp.h"
#include <stdint.h>
#include <stdio.h>
int main(void){
 gs_bass b;
 int32_t lr[512]={0};
 gs_bass_init(&b);
 gs_bass_note(&b,55.0f,1);
 int32_t peak=0;
 for(unsigned block=0;block<300;block++){
  for(unsigned i=0;i<512;i++)lr[i]=0;
  gs_bass_mix(&b,lr,256,4096);
  for(unsigned i=0;i<512;i++){
   int32_t a=lr[i]<0?-lr[i]:lr[i];
   if(a>peak)peak=a;
   if(lr[i]>8388607 || lr[i]<-8388608)return 2;
  }
 }
 if(peak<50000){fprintf(stderr,"Bass silent: %d\n",peak);return 1;}
 gs_bass_panic(&b);
 for(unsigned i=0;i<512;i++)lr[i]=0;
 gs_bass_mix(&b,lr,256,4096);
 for(unsigned i=0;i<512;i++)if(lr[i]!=0)return 3;
 printf("PASS: native bass, peak=%d\n",peak);
 return 0;
}
