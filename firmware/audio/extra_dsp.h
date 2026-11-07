#ifndef GS_EXTRA_DSP_H
#define GS_EXTRA_DSP_H
#include <stdint.h>
typedef struct {float phase,mod,env,hz,brightness;uint8_t gate;} gs_lead;
typedef struct {float phase,env,hat,kick,snare;uint32_t rng;uint32_t step;float beat_pos;uint8_t playing,pattern;} gs_drums;
void gs_lead_init(gs_lead *p);
void gs_lead_note(gs_lead *p,float hz,int gate);
void gs_lead_mix(gs_lead *p,int32_t *lr,uint32_t n,uint32_t gain);
void gs_drums_init(gs_drums *d);
void gs_drums_mix(gs_drums *d,int32_t *lr,uint32_t n,uint32_t gain,int bpm);
#endif
