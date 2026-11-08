#include "../firmware/audio/pad_dsp.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
int main(void){
 printf("Pad RAM: %zu bytes per instance, %zu bytes for eight instances (excluding stack and other tracks)\\n",sizeof(gs_pad),8u*sizeof(gs_pad));\n static gs_pad p;gs_pad_init(&p);if(p.texture_voices!=4){fprintf(stderr,"FAIL default texture quality\\n");return 9;}gs_pad_environment(&p,5,0.75f);gs_pad_note(&p,110.0f,1);
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
 /* Four texture voices must advance independently and retain different phases.
    A regression to the old single oscillator would fail this check. */
 gs_pad_init(&p);gs_pad_note(&p,220.0f,1);
 for(unsigned b=0;b<8;b++)gs_pad_render(&p,buffer,256,4096);
 if(p.voice_phase[0]==p.voice_phase[1] ||
    p.voice_phase[1]==p.voice_phase[2] ||
    p.voice_lfo[0]==p.voice_lfo[3]){
  fprintf(stderr,"FAIL independent ToneScape texture voices\\n");return 8;
 }
 /* Wash should create an audible tail after a note release, but panic must
    still clear both channels and all delay state immediately. */
 gs_pad_init(&p);gs_pad_environment(&p,5,0.75f);gs_pad_note(&p,220.0f,1);
 for(unsigned b=0;b<500;b++)gs_pad_render(&p,buffer,256,4096);
 gs_pad_note(&p,220.0f,0);
 int64_t tail_energy=0;int64_t stereo_difference=0;
 for(unsigned b=0;b<100;b++){
  gs_pad_render(&p,buffer,256,4096);
  for(unsigned i=0;i<256;i++){
   int64_t l=buffer[2*i],r=buffer[2*i+1];
   tail_energy+=(l*l+r*r)/1000000;
   stereo_difference+=llabs(l-r);
  }
 }
 if(tail_energy==0||stereo_difference==0){
  fprintf(stderr,"FAIL wash tail or stereo difference\\n");return 5;
 }
 gs_pad_panic(&p);gs_pad_render(&p,buffer,256,4096);
 for(unsigned i=0;i<512;i++)if(buffer[i]!=0){
  fprintf(stderr,"FAIL wash panic\\n");return 6;
 }
 /* Exercise all 16 environments and both intensity extremes after repeated
    switches to catch stale precomputed modal coefficients. */
 for(unsigned env=0;env<16;env++){
  gs_pad_init(&p);
  for(unsigned intensity=0;intensity<=1;intensity++){
   gs_pad_environment(&p,env,(float)intensity);
   gs_pad_note(&p,55.0f+(float)env*27.0f,1);
   for(unsigned b=0;b<12;b++){
    gs_pad_render(&p,buffer,256,4096);
    for(unsigned i=0;i<512;i++)if(buffer[i]>8388607||buffer[i]<-8388608){
     fprintf(stderr,"FAIL env output bounds %u\\n",env);return 7;
    }
   }
   gs_pad_note(&p,0.0f,0);
  }
 }
 /* Informational real-time budget benchmark, measured without sanitizer.
    A block of 256 frames at 44.1kHz has 5.805 ms to finish. */
 gs_pad_init(&p);gs_pad_environment(&p,7,1.0f);gs_pad_note(&p,220.0f,1);
 clock_t bench_start=clock();
 for(unsigned b=0;b<200;b++)gs_pad_render(&p,buffer,256,4096);
 clock_t bench_end=clock();
 double elapsed_ms=1000.0*(double)(bench_end-bench_start)/CLOCKS_PER_SEC;
 printf("DSP benchmark: 200 x 256 frames, CPU %.2f ms, avg %.3f ms/block, deadline 5.805 ms/block (host only)\\n",elapsed_ms,elapsed_ms/200.0);
 /* Real GrooveScape can mix eight independent ToneScape pad instances.
    Benchmark the worst-case concurrent pad load rather than a single voice. */
 static gs_pad ensemble[8];
 for(unsigned v=0;v<8;v++){
  gs_pad_init(&ensemble[v]);
  gs_pad_environment(&ensemble[v],v,0.75f);
  gs_pad_note(&ensemble[v],110.0f+(float)v*27.5f,1);
 }
 clock_t ensemble_start=clock();
 for(unsigned b=0;b<40;b++){
  for(unsigned v=0;v<8;v++)gs_pad_render(&ensemble[v],buffer,256,4096);
 }
 double ensemble_ms=1000.0*(double)(clock()-ensemble_start)/CLOCKS_PER_SEC/40.0;
 printf("Eight-pad stress benchmark: %.3f ms per 256-frame block, deadline 5.805 ms (host CPU, diagnostic only)\\n",ensemble_ms);
 clock_t four_start=clock();
 for(unsigned b=0;b<40;b++){
  for(unsigned v=0;v<4;v++)gs_pad_render(&ensemble[v],buffer,256,4096);
 }
 double four_ms=1000.0*(double)(clock()-four_start)/CLOCKS_PER_SEC/40.0;
 printf("Four-pad benchmark: %.3f ms per 256-frame block, deadline 5.805 ms (host CPU, diagnostic only)\\n",four_ms);
 for(unsigned quality=2;quality<=3;quality++){
  for(unsigned v=0;v<8;v++)ensemble[v].texture_voices=(uint8_t)quality;
  clock_t quality_start=clock();
  for(unsigned b=0;b<40;b++){
   for(unsigned v=0;v<8;v++)gs_pad_render(&ensemble[v],buffer,256,4096);
  }
  double quality_ms=1000.0*(double)(clock()-quality_start)/CLOCKS_PER_SEC/40.0;
  printf("Eight-pad %u-texture-voice benchmark: %.3f ms/block (host diagnostic)\\n",quality,quality_ms);
  clock_t compact_start=clock();
  for(unsigned b=0;b<40;b++){
   for(unsigned v=0;v<4;v++)gs_pad_render(&ensemble[v],buffer,256,4096);
  }
  double compact_ms=1000.0*(double)(clock()-compact_start)/CLOCKS_PER_SEC/40.0;
  printf("Four-pad %u-texture-voice benchmark: %.3f ms/block (host diagnostic)\\n",quality,compact_ms);
 }


 printf("PASS: 44.1k stereo pad; peak=%d, wash tail=%lld\\n",peak,(long long)tail_energy);return 0;
}
