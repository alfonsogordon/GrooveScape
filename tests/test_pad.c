#include "../firmware/audio/pad_dsp.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(void){
 gs_pad p;gs_pad_init(&p);gs_pad_environment(&p,5,0.75f);gs_pad_note(&p,110.0f,1);
 int32_t buffer[512];int64_t energy=0;int32_t peak=0;
 for(unsigned block=0;block<600;block++){
  gs_pad_render(&p,buffer,256,4096);
  for(unsigned i=0;i<512;i++){int64_t v=buffer[i];energy+=(v*v)/1000000;int32_t a=abs(buffer[i]);if(a>peak)peak=a;}
 }
 if(peak<1000||peak>8388607||energy==0){fprintf(stderr,"FAIL peak %d\n",peak);return 1;}
 gs_pad_note(&p,110.0f,0);for(unsigned i=0;i<1000;i++)gs_pad_render(&p,buffer,256,4096);
 if(p.env>0.5f){fprintf(stderr,"FAIL release %f\n",p.env);return 2;}
 gs_pad_note(&p,110.0f,1);gs_pad_render(&p,buffer,256,4096);gs_pad_panic(&p);gs_pad_render(&p,buffer,256,4096);
 for(unsigned i=0;i<512;i++)if(buffer[i]!=0){fprintf(stderr,"FAIL panic nonzero sample\n");return 3;}
 for(unsigned env=0;env<16;env++){
  gs_pad_init(&p);gs_pad_environment(&p,env,1.0f);gs_pad_note(&p,440.0f,1);
  for(unsigned b=0;b<40;b++){
   gs_pad_render(&p,buffer,256,4096);
   for(unsigned i=0;i<512;i++)if(buffer[i]>8388607||buffer[i]<-8388608){
    fprintf(stderr,"FAIL 24-bit range env %u\\n",env);return 4;
   }
  }
 }
 printf("PASS: 44.1k stereo pad; peak=%d, release=%f\n",peak,p.env);return 0;
}
