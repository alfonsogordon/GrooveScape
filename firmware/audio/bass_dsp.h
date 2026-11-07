#ifndef GROOVESCAPE_BASS_DSP_H
#define GROOVESCAPE_BASS_DSP_H
#include <stdint.h>
typedef struct {
    float phase, hz, env, cutoff, lowpass;
    uint8_t gate;
} gs_bass;
void gs_bass_init(gs_bass *b);
void gs_bass_note(gs_bass *b, float hz, int gate);
void gs_bass_panic(gs_bass *b);
void gs_bass_mix(gs_bass *b, int32_t *lr, uint32_t frames, uint32_t master_q12);
#endif
