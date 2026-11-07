/* Original GrooveScape monophonic bass, 44.1 kHz, signed 24-bit mix bus.
 * No allocations or I/O in the audio callback. */
#include "bass_dsp.h"
#include <math.h>
#include <string.h>
#define GS_SR 44100.0f
#define GS_PI2 6.28318530718f
static float clampf(float v,float lo,float hi){return v<lo?lo:(v>hi?hi:v);}
void gs_bass_init(gs_bass *b){memset(b,0,sizeof *b);b->hz=55.0f;b->cutoff=0.12f;}
void gs_bass_note(gs_bass *b,float hz,int gate){
 if(gate && isfinite(hz))b->hz=clampf(hz,25.0f,700.0f);
 b->gate=(uint8_t)(gate!=0);
}
void gs_bass_panic(gs_bass *b){b->gate=0;b->env=0.0f;b->lowpass=0.0f;}
void gs_bass_mix(gs_bass *b,int32_t *lr,uint32_t frames,uint32_t master_q12){
 const float master=clampf((float)master_q12/4096.0f,0.0f,1.0f);
 for(uint32_t i=0;i<frames;i++){
  float target=b->gate?1.0f:0.0f;
  float rate=b->gate?0.0035f:0.00042f;
  b->env+=(target-b->env)*rate;
  b->phase+=b->hz/GS_SR;
  if(b->phase>=1.0f)b->phase-=1.0f;
  float saw=2.0f*b->phase-1.0f;
  float sub=sinf(GS_PI2*b->phase);
  float cutoff=clampf(b->cutoff*(0.5f+b->env),0.005f,0.45f);
  b->lowpass+=cutoff*(saw-b->lowpass);
  /* Keep the sub dominant and the saw harmonics restrained, leaving
     spectral room for ToneScape's evolving midrange textures. */
  float sample=(0.72f*sub+0.28f*b->lowpass)*b->env*master*2900000.0f;
  for(unsigned ch=0;ch<2;ch++){
   int64_t mixed=(int64_t)lr[2u*i+ch]+(int32_t)sample;
   if(mixed>8388607)mixed=8388607;
   if(mixed< -8388608)mixed= -8388608;
   lr[2u*i+ch]=(int32_t)mixed;
  }
 }
}
