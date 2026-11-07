/* GrooveScape original FM1-ready C pad prototype. No allocations or I/O in audio callback. */
#include "pad_dsp.h"
#include <math.h>
#include <string.h>
#define GS_SR 44100.0f
#define GS_PI2 6.283185307179586f
#define GS_OUTPUT 6500000.0f
static const float spec[16][4] = {
 {0.72f,0.25f,0.08f,0.55f},{0.82f,0.33f,0.06f,0.64f},
 {0.62f,0.45f,0.16f,0.42f},{0.54f,0.68f,0.22f,0.78f},
 {0.76f,0.20f,0.18f,0.48f},{0.88f,0.52f,0.11f,0.92f},
 {0.80f,0.28f,0.13f,0.72f},{0.64f,0.74f,0.38f,0.74f},
 {0.50f,0.30f,0.10f,0.82f},{0.58f,0.48f,0.42f,0.56f},
 {0.74f,0.24f,0.09f,0.58f},{0.90f,0.26f,0.30f,0.66f},
 {0.56f,0.72f,0.24f,0.76f},{0.48f,0.82f,0.20f,0.88f},
 {0.70f,0.56f,0.15f,0.84f},{0.84f,0.18f,0.36f,0.90f}
};
static float clampf(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
void gs_pad_init(gs_pad *p){memset(p,0,sizeof *p);p->hz=110.0f;p->intensity=0.5f;}
void gs_pad_note(gs_pad *p,float hz,int gate){if(gate && isfinite(hz))p->hz=clampf(hz,30.0f,1500.0f);p->gate=(uint8_t)(gate!=0);}
void gs_pad_panic(gs_pad *p){p->gate=0;p->env=0.0f;}
void gs_pad_environment(gs_pad *p,unsigned environment,float intensity){p->environment=(uint8_t)(environment%16u);p->intensity=isfinite(intensity)?clampf(intensity,0.0f,1.0f):0.5f;}
void gs_pad_render(gs_pad *p,int32_t *lr,uint32_t frames,uint32_t master_q12){
 const float *s=spec[p->environment%16u];
 const float master=clampf((float)master_q12/4096.0f,0.0f,1.0f);
 const unsigned partials=4u+(unsigned)(p->intensity*8.0f);
 for(uint32_t n=0;n<frames;n++){
  const float target=p->gate?1.0f:0.0f;
  const float env_rate=p->gate?1.0f/(GS_SR*2.5f):1.0f/(GS_SR*5.0f);
  p->env+=(target-p->env)*env_rate;
  p->phase+=GS_PI2*p->hz/GS_SR;
  if(p->phase>=GS_PI2)p->phase-=GS_PI2;
  p->drift+=GS_PI2*0.11f/GS_SR;
  if(p->drift>=GS_PI2)p->drift-=GS_PI2;
  const float wobble=0.003f*sinf(p->drift)*(0.4f+p->intensity);
  float l=0.0f,r=0.0f,weight_total=0.0f;
  for(unsigned j=0;j<partials;j++){
   const float harmonic=(float)(j+1u);
   const float stretch=1.0f+s[2]*0.006f*(float)((int)(j%3u)-1);
   const float weight=1.0f/powf(harmonic,0.85f+s[1]*0.5f);
   const float angle=p->phase*harmonic*stretch*(1.0f+wobble*(1.0f+j*0.06f));
   const float spread=0.2f+s[3]*0.7f;
   l+=sinf(angle+j*0.21f)*weight*(1.0f+spread*0.15f*sinf(p->drift+j));
   r+=sinf(angle+j*0.21f+j*0.06f)*weight*(1.0f-spread*0.15f*sinf(p->drift+j));
   weight_total+=weight;
  }
  const float amp=p->env*s[0]*0.28f/(weight_total>0.0f?weight_total:1.0f);
  const float scale=GS_OUTPUT*master;
  lr[2u*n]=(int32_t)(tanhf(l*amp)*scale);
  lr[2u*n+1u]=(int32_t)(tanhf(r*amp)*scale);
 }
}
