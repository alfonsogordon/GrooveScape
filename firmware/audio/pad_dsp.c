/* GrooveScape ToneScape V2 texture port. No allocations or I/O in audio callback. */
#include "pad_dsp.h"
#include <math.h>
#include <string.h>
#define GS_SR 44100.0f
#define GS_PI2 6.283185307179586f
#define GS_OUTPUT 6500000.0f /* signed 24-bit samples stored in int32_t */
/* Parameters ported from ToneScape V2 TextureEngine(1).cpp, in its original
 * environment order: body, brightness, inharmonicity, breath, rip, space. */
static const float spec[16][6] = {
 {0.72f,.25f,.08f,.62f,.08f,.55f},{.82f,.33f,.06f,.40f,.12f,.64f},
 {.62f,.45f,.16f,.25f,.42f,.42f},{.54f,.68f,.22f,.36f,.15f,.78f},
 {.76f,.20f,.18f,.72f,.10f,.48f},{.88f,.52f,.11f,.30f,.18f,.92f},
 {.80f,.28f,.13f,.86f,.16f,.72f},{.64f,.74f,.38f,.34f,.86f,.74f},
 {.50f,.30f,.10f,.92f,.06f,.82f},{.58f,.48f,.42f,.28f,.55f,.56f},
 {.74f,.24f,.09f,.46f,.24f,.58f},{.90f,.26f,.30f,.44f,.32f,.66f},
 {.56f,.72f,.24f,.58f,.28f,.76f},{.48f,.82f,.20f,.32f,.10f,.88f},
 {.70f,.56f,.15f,.68f,.18f,.84f},{.84f,.18f,.36f,.52f,.38f,.90f}
};
static float gs_hash(float x){float a=sinf(x*12.9898f+78.233f)*43758.5453f;return fabsf(a)-floorf(fabsf(a));}
static float gs_soft(float x,float drive){return tanhf(x*drive)/fmaxf(.001f,drive);}
static float gs_smooth(float x){x=fmaxf(0.0f,fminf(1.0f,x));return x*x*(3.0f-2.0f*x);}
static float gs_texture(float phase,const float *s,float intensity,float seed,const float *weights,const float *odds){
 const float t=gs_smooth(intensity),density=4.0f+12.0f*t;
 const float driftBase=.002f+.010f*s[3]+.016f*t;
 float sum=0.0f,weightSum=0.0f;
 for(unsigned j=0;j<16;j++){
  float fi=(float)j,active=fmaxf(0.0f,fminf(1.0f,density-fi));
  if(active<=0.0f)continue;
  float harmonic=1.0f+fi,odd=odds[j];
  float ratio=harmonic*(1.0f+s[2]*.035f*odd*(fi/15.0f));
  float drift=sinf(phase*(.0009f+fi*.00013f)+seed+fi)*driftBase*(1.0f+fi*.08f);
  float formant=.72f+.28f*sinf(phase*.0017f+seed*1.9f+fi*.61f);
  float pp=phase*ratio*(1.0f+drift)+seed*(2.7f+fi*.13f);
  float w=active*weights[j]
          *(1.0f+s[1]*t*fi*.045f)*formant;
  float partial=sinf(pp)+.23f*sinf(pp*(1.997f+s[2]*.03f)+seed);
  sum+=gs_soft(partial,1.0f+s[4]*.55f+t*.35f)*w;
  weightSum+=w;
 }
 float body=weightSum>.000001f?sum/sqrtf(weightSum):0.0f;
 float n=sinf(phase*17.171f+seed*4.1f)*.52f
       +sinf(phase*31.337f-seed*2.7f)*.31f
       +sinf(phase*53.733f+seed*.9f)*.17f;
 float slow=sinf(phase*.013f+seed*1.7f)*.52f
           +sinf(phase*.021f-seed*2.3f+1.4f)*.31f
           +sinf(phase*.034f+seed*.8f-.7f)*.17f;
 float breath=tanhf(n*1.8f)*(.55f+.45f*tanhf(slow*(1.2f+s[3])))
              *(.012f+.050f*s[3])*(.45f+t*.90f);
 float ripAmt=s[4]*fmaxf(0.0f,(t-.30f)/.70f);
 float rip=0.0f;
 if(ripAmt>.0001f){
  float x=sinf(phase*(2.01f+s[2]*.8f)+seed)
         +.55f*sinf(phase*(3.77f+s[2]*1.7f)-seed*.7f)
         +.25f*sinf(phase*(7.13f+s[2]*2.1f)+seed*1.9f);
  rip=tanhf(x*(1.2f+ripAmt*3.5f))*ripAmt*.13f;
 }
 float x=body*(.55f+s[0]*.35f+t*.42f)*(.80f+s[1]*.28f+t*.25f)+breath+rip;
 return gs_soft(x,.92f+t*.95f+s[4]*t*.85f)*.82f;
}
static float gs_clampf(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
void gs_pad_init(gs_pad *p){memset(p,0,sizeof *p);p->hz=110.0f;p->target_hz=110.0f;p->glide_sec=3.0f;p->attack_sec=4.0f;p->release_sec=8.0f;gs_pad_environment(p,0,0.5f);}
void gs_pad_note(gs_pad *p,float hz,int gate){if(gate && isfinite(hz)){p->target_hz=gs_clampf(hz,30.0f,1500.0f);if(p->env<0.00001f)p->hz=p->target_hz;}p->gate=(uint8_t)(gate!=0);}
void gs_pad_panic(gs_pad *p){p->gate=0;p->env=0.0f;memset(p->wash_l,0,sizeof p->wash_l);memset(p->wash_r,0,sizeof p->wash_r);p->wash_pos_l=0;p->wash_pos_r=0;}
void gs_pad_environment(gs_pad *p,unsigned environment,float intensity){p->environment=(uint8_t)(environment%16u);p->intensity=isfinite(intensity)?gs_clampf(intensity,0.0f,1.0f):0.5f;
 const float *s=spec[p->environment];
 for(unsigned j=0;j<16;j++){
  float fi=(float)j;
  p->harmonic_weight[j]=powf(1.0f/(1.0f+fi),.72f+s[1]*.65f);
  p->odd_l[j]=2.0f*gs_hash(.37f+fi*11.31f)-1.0f;
  p->odd_r[j]=2.0f*gs_hash(1.11f+fi*11.31f)-1.0f;
 }
}
void gs_pad_render(gs_pad *p,int32_t *lr,uint32_t frames,uint32_t master_q12){
 const float *s=spec[p->environment%16u];
 const float master=gs_clampf((float)master_q12/4096.0f,0.0f,1.0f);
 /* Block-invariant coefficients: preserve the same sample-by-sample sound. */
 const float glide_rate=1.0f/(GS_SR*gs_clampf(p->glide_sec,0.01f,30.0f));
 const float envelope_rate=1.0f/(GS_SR*(p->gate?gs_clampf(p->attack_sec,0.02f,30.0f):gs_clampf(p->release_sec,0.02f,40.0f)));
 const float scale=GS_OUTPUT*master*1.15f;
 static const float ratios[4]={0.997f,1.0f,1.003f,0.5f};
 static const float pans[4]={-0.72f,0.64f,-0.27f,0.32f};
 float pan_l[4],pan_r[4];
 for(unsigned v=0;v<4;v++){pan_l[v]=sqrtf(.5f*(1.0f-pans[v]));pan_r[v]=sqrtf(.5f*(1.0f+pans[v]));}
 for(uint32_t n=0;n<frames;n++){
  p->hz += (p->target_hz-p->hz)*glide_rate;
  float rate=envelope_rate;
  p->env+=((p->gate?1.0f:0.0f)-p->env)*rate;
  /* Independent slowly detuned ToneScape-style voices, spread in stereo.
   * Keep modulation per voice instead of multiplying a single mono oscillator. */
  float left=0.0f,right=0.0f;
  if (p->gate || p->env > 0.00005f) {
  for(unsigned v=0;v<4;v++){
   float ph=p->voice_phase[v];
   float lfo=p->voice_lfo[v];
   float motion=.003f*sinf(lfo);
   float moved=ph*(1.0f+motion+s[5]*.0015f*sinf(ph*.0007f+.37f+v));
   float seed=.37f+(float)v*.71f;
   float sample=gs_texture(moved,s,p->intensity,seed,p->harmonic_weight,p->odd_l);
   /* Original MorphPadEngine adds air harmonics and a warm sub-body,
      then applies soft texture shaping before its stereo processing. */
   sample+=.040f*s[1]*sinf(ph*5.0f+seed)+.026f*s[0]*sinf(ph*.5f);
   sample=gs_soft(sample,1.08f);
   left+=sample*pan_l[v];
   right+=sample*pan_r[v];
   ph+=GS_PI2*p->hz*ratios[v]/GS_SR;
   if(ph>=GS_PI2)ph-=GS_PI2;
   p->voice_phase[v]=ph;
   lfo+=GS_PI2*(.06f+.019f*(float)v)/GS_SR;
   if(lfo>=GS_PI2)lfo-=GS_PI2;
   p->voice_lfo[v]=lfo;
  }
  }
  left*=.50f;
  right*=.50f;
  /* Stereo wash: cross-fed, decaying diffusion taps. Tail continues after note-off. */
  float wet_l=p->wash_l[p->wash_pos_l];
  float wet_r=p->wash_r[p->wash_pos_r];
  float dry_l=left*p->env*.24f;
  float dry_r=right*p->env*.24f;
  p->wash_l[p->wash_pos_l]=gs_clampf(dry_l+wet_l*.72f+wet_r*.10f,-1.0f,1.0f);
  p->wash_r[p->wash_pos_r]=gs_clampf(dry_r+wet_r*.71f+wet_l*.11f,-1.0f,1.0f);
  if(++p->wash_pos_l==4093u)p->wash_pos_l=0;
  if(++p->wash_pos_r==4787u)p->wash_pos_r=0;
  float out_l=gs_clampf((dry_l+wet_l*.32f)*scale,-8388607.0f,8388607.0f);
  float out_r=gs_clampf((dry_r+wet_r*.32f)*scale,-8388607.0f,8388607.0f);
  lr[2u*n]=(int32_t)out_l;
  lr[2u*n+1u]=(int32_t)out_r;
 }
}

/* Render an overlapping retiring layer without overwriting the newer layer. */
void gs_pad_mix(gs_pad *p,int32_t *lr,uint32_t frames,uint32_t master_q12){
 int32_t tmp[128];
 for(uint32_t off=0;off<frames;){
  uint32_t count=frames-off;
  if(count>64u)count=64u;
  gs_pad_render(p,tmp,count,master_q12);
  for(uint32_t i=0;i<count*2u;i++){
   int64_t v=(int64_t)lr[off*2u+i]+tmp[i];
   if(v>8388607)v=8388607;
   if(v< -8388607)v= -8388607;
   lr[off*2u+i]=(int32_t)v;
  }
  off+=count;
 }
}
