#ifndef GS_EXTRA_DSP_H
#define GS_EXTRA_DSP_H
#include <stdint.h>
typedef struct {float phase,mod,env,hz,brightness;uint8_t gate;} gs_lead;
typedef struct {
    float phase, env, hat, kick, snare;
    uint32_t rng, step;
    float beat_pos;
    uint8_t playing, pattern, fill, mute;
    uint8_t clock_running, queued_start, queued_pattern;
    uint16_t kick_steps[2], snare_steps[2], hat_steps[2];
} gs_drums;
void gs_lead_init(gs_lead *p);
void gs_lead_note(gs_lead *p,float hz,int gate);
void gs_lead_mix(gs_lead *p,int32_t *lr,uint32_t n,uint32_t gain);
void gs_drums_init(gs_drums *d);
void gs_drums_clock_start(gs_drums *d);
void gs_drums_panic(gs_drums *d);
void gs_drums_set_playing(gs_drums *d, int playing, int quantized);
void gs_drums_set_pattern(gs_drums *d, unsigned pattern, int quantized);
void gs_drums_hit(gs_drums *d,unsigned instrument,float velocity);
void gs_drums_mix(gs_drums *d,int32_t *lr,uint32_t n,uint32_t gain,int bpm);
#endif
