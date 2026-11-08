#include "extra_dsp.h"
#include <math.h>
#include <string.h>
#define SR 44100.0f
#define TAU 6.28318530718f
static float cl(float v,float a,float b){return v<a?a:(v>b?b:v);}
static void add(int32_t *lr,uint32_t i,float x){int32_t v=(int32_t)cl(x,-7000000.f,7000000.f);for(unsigned k=0;k<2;k++){int64_t s=(int64_t)lr[i*2+k]+v;lr[i*2+k]=(int32_t)(s>8388607?8388607:(s< -8388608?-8388608:s));}}
void gs_lead_init(gs_lead *p){memset(p,0,sizeof *p);p->hz=440;p->brightness=.45f;}
void gs_lead_note(gs_lead *p,float hz,int gate){if(gate&&hz>0)p->hz=cl(hz,70,2400);p->gate=(uint8_t)!!gate;}
void gs_lead_mix(gs_lead *p,int32_t *lr,uint32_t n,uint32_t gain){
float master=cl((float)gain/4096.f,0,1);
for(uint32_t i=0;i<n;i++){/* slow ghostly release */
float target=p->gate?1.f:0.f;p->env+=(target-p->env)*(p->gate?.0015f:.00012f);
p->phase+=p->hz/SR;if(p->phase>=1)p->phase-=1;
p->mod+=.23f/SR;if(p->mod>=1)p->mod-=1;
float sh=sinf(TAU*p->phase+1.2f*sinf(TAU*p->phase*2.f));
float sparkle=sinf(TAU*p->phase*4.01f)*(.10f+.25f*p->brightness);
float out=(sh*.5f+sparkle)*p->env*master*950000.f;add(lr,i,out);
}}
void gs_drums_init(gs_drums *d){memset(d,0,sizeof *d);d->rng=0xC017A12u;d->kick=0.8f;d->snare=0.4f;d->hat=.0f;d->kick=0.f;d->snare=0.f;d->kick_steps[0]=0x0101u;d->snare_steps[0]=0x1010u;d->hat_steps[0]=0x4444u;d->kick_steps[1]=0x0101u;d->snare_steps[1]=0x0100u;d->hat_steps[1]=0x0404u;}
void gs_drums_clock_start(gs_drums *d){
    if(!d->clock_running){d->clock_running=1;d->beat_pos=0.f;d->step=15u;}
}
void gs_drums_panic(gs_drums *d){
    d->playing=0;d->queued_start=0;d->queued_pattern=0;d->clock_running=0;
    d->kick=0.f;d->snare=0.f;d->hat=0.f;d->beat_pos=0.f;d->step=15u;
}
void gs_drums_set_playing(gs_drums *d,int playing,int quantized){
    if(!playing){d->playing=0;d->queued_start=0;d->queued_pattern=0;return;}
    if(d->playing || d->queued_start)return;
    if(quantized && d->clock_running && d->step!=15u){d->queued_start=1;return;}
    d->playing=1;d->queued_start=0;
    if(!d->clock_running){gs_drums_clock_start(d);d->beat_pos=1.f;}
}
void gs_drums_set_pattern(gs_drums *d,unsigned pattern,int quantized){
    uint8_t next=(uint8_t)(pattern&1u);
    if(quantized && (d->playing || d->queued_start) && d->step!=15u){d->queued_pattern=(uint8_t)(next+1u);return;}
    d->pattern=next;d->queued_pattern=0;
}
void gs_drums_hit(gs_drums *d,unsigned instrument,float velocity){
float v=cl(velocity,0.f,1.f);
switch(instrument%4u){case 0:d->kick=v;break;case 1:d->snare=v;break;case 2:d->hat=v;break;default:d->snare=v*.5f;d->hat=v*.6f;break;}
}
void gs_drums_mix(gs_drums *d,int32_t *lr,uint32_t n,uint32_t gain,int bpm){
float master=cl((float)gain/4096.f,0,1);if(bpm<30)bpm=30;if(bpm>300)bpm=300;
for(uint32_t i=0;i<n;i++){
if(d->clock_running){d->beat_pos+=(float)bpm/(60.f*SR)*4.f;
if(d->beat_pos>=1.f){d->beat_pos-=1.f;d->step=(d->step+1u)&15u;
if(d->step==0u){
    if(d->queued_pattern){d->pattern=(uint8_t)(d->queued_pattern-1u);d->queued_pattern=0;}
    if(d->queued_start){d->playing=1;d->queued_start=0;}
}
if(d->playing){
uint16_t bit=(uint16_t)(1u<<d->step);
if(d->kick_steps[d->pattern]&bit)d->kick=1.f;
if(d->snare_steps[d->pattern]&bit)d->snare=.8f;
if(d->hat_steps[d->pattern]&bit)d->hat=.4f;
if(d->fill && (d->step&1u))d->snare=.55f;
}}}
d->phase+= (48.f+95.f*d->kick*d->kick)/SR;if(d->phase>=1)d->phase-=1;
d->rng^=d->rng<<13;d->rng^=d->rng>>17;d->rng^=d->rng<<5;
float noise=(float)((int32_t)d->rng)/2147483648.f;
float kick=sinf(TAU*d->phase)*d->kick;
float snare=noise*d->snare;float hat=noise*d->hat;
d->kick*=.9992f;d->snare*=.996f;d->hat*=.984f;
if(!d->mute)add(lr,i,(kick*.7f+snare*.22f+hat*.07f)*master*1200000.f);
}}
