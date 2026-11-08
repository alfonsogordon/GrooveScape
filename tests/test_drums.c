#include "../firmware/audio/extra_dsp.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(void) {
    gs_drums d;
    int32_t out[512]={0};
    gs_drums_init(&d);
    assert(d.pattern==0 && d.queued_pattern==0 && !d.playing);
    gs_drums_hit(&d,0,1.f);
    assert(d.kick>0.f && !d.playing); /* live drums outside SEQ */
    gs_drums_clock_start(&d);
    d.beat_pos=1.f; /* Advance the clock into the bar before requesting a queued start. */
    gs_drums_mix(&d,out,256,4096,120);
    gs_drums_set_playing(&d,1,1);
    assert(d.queued_start && !d.playing);
    gs_drums_set_pattern(&d,1,1);
    assert(d.pattern==0 && d.queued_pattern==2);
    /* 120 BPM: 16 sixteenth notes per 2 second bar. */
    for(unsigned i=0;i<300;i++)gs_drums_mix(&d,out,256,4096,120);
    assert(!d.playing && d.pattern==0);
    for(unsigned i=0;i<50;i++)gs_drums_mix(&d,out,256,4096,120);
    assert(d.playing && d.pattern==1 && !d.queued_start);
    gs_drums_set_playing(&d,0,1);
    assert(!d.playing);
    gs_drums_set_playing(&d,1,1);
    assert(d.queued_start && !d.playing);
    gs_drums_panic(&d);
    assert(!d.clock_running && !d.playing && !d.queued_start);
    gs_drums_set_playing(&d,1,1);
    gs_drums_mix(&d,out,256,4096,120);
    assert(d.playing && d.step==0);
    puts("PASS: live drums, quantized start/A-B, immediate stop and panic");
    return 0;
}
