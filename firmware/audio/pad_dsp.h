#ifndef GROOVESCAPE_PAD_DSP_H
#define GROOVESCAPE_PAD_DSP_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { float phase, drift, env, hz, intensity; uint8_t environment, gate; } gs_pad;
void gs_pad_init(gs_pad *p);
void gs_pad_note(gs_pad *p, float hz, int gate);
void gs_pad_environment(gs_pad *p, unsigned environment, float intensity);
void gs_pad_render(gs_pad *p, int32_t *lr, uint32_t frames, uint32_t master_q12);
#ifdef __cplusplus
}
#endif
#endif
