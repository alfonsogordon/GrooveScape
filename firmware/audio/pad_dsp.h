#ifndef GROOVESCAPE_PAD_DSP_H
#define GROOVESCAPE_PAD_DSP_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { float phase, drift, env, hz, intensity, attack_sec, release_sec, target_hz, glide_sec; float voice_phase[4], voice_lfo[4]; uint8_t environment, gate, texture_voices; float wash_l[4093], wash_r[4787]; float harmonic_weight[16], odd_l[16], odd_r[16]; uint32_t wash_pos_l, wash_pos_r; } gs_pad;
void gs_pad_init(gs_pad *p);
void gs_pad_note(gs_pad *p, float hz, int gate);
void gs_pad_panic(gs_pad *p);
void gs_pad_environment(gs_pad *p, unsigned environment, float intensity);
void gs_pad_render(gs_pad *p, int32_t *lr, uint32_t frames, uint32_t master_q12);
void gs_pad_mix(gs_pad *p, int32_t *lr, uint32_t frames, uint32_t master_q12);
#ifdef __cplusplus
}
#endif
#endif
