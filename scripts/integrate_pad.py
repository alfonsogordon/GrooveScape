#!/usr/bin/env python3
"""Install GrooveScape C pad into a separate fm1-base template copy.
No hardware flash, no source modifications to the upstream template.
"""
from pathlib import Path
import argparse
import shutil

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument("--base",type=Path,default=root/".work/fm1-base")
args=parser.parse_args()
base=args.base.resolve()
source=base/"template"
target=base/"groovescape"
if not (source/"app.c").is_file():
    raise SystemExit("Missing fm1-base template. Run bootstrap first.")
if target.exists():
    raise SystemExit(f"Refusing to overwrite {target}; move it away first")
shutil.copytree(source,target,ignore=shutil.ignore_patterns("build"))
for filename in ("pad_dsp.c","pad_dsp.h","bass_dsp.c","bass_dsp.h","extra_dsp.c","extra_dsp.h"):
    shutil.copyfile(root/"firmware/audio"/filename,target/filename)
app=(target/"app.c").read_text()
anchor='#include "fastmath.h"'
assert app.count(anchor)==1
app=app.replace(anchor,anchor+'\n#include "pad_dsp.h"\nstatic gs_pad gs_voice;\nstatic gs_pad gs_fading_voice;\nstatic gs_pad gs_chord[2], gs_chord_fading[2];\nstatic gs_pad gs_melody;\nstatic gs_pad gs_melody_fading;\nstatic int gs_chord_select = 0;\nstatic int gs_root = 9, gs_minor = 0, gs_latch = 1, gs_last_chord = -1;\nstatic unsigned gs_track, gs_page, gs_page_num;\n#include \"bass_dsp.h\"\nstatic gs_bass gs_bass_voice;\n#include "extra_dsp.h"\nstatic gs_lead gs_lead_voice;\nstatic gs_drums gs_drum_voice;\nstatic int gs_pad_key = -1, gs_bass_key = -1;')
# Expose the active pad environment on the real FM1 screen.
app=app.replace('static gs_pad gs_voice;', 'static gs_pad gs_voice;\nstatic unsigned gs_env_index;\nstatic int gs_intensity_percent = 35;\nstatic const char *const gs_env_names[16] = {\n    "DRIFT", "BLOOM", "EMBER", "GLASS CHOIR", "DEEP FOREST", "CATHEDRAL",\n    "OCEAN", "RIFT", "MIST", "MACHINE AIR", "TAPE GHOST", "HOLLOW EARTH",\n    "NEON WEATHER", "ICE BLOOM", "AURORA BODY", "NOIR VOID"\n};')
old='    voice_vel = (float)vel / 127.0f;\n    voice_note = note;'
assert app.count(old)==1
app=app.replace(old,'''    voice_note = note;
    gs_drums_clock_start(&gs_drum_voice);
    if (gs_track == 0 && gs_chord_select) {
        static const int major_steps[7] = {0,2,4,5,7,9,11};
        static const int minor_steps[7] = {0,2,3,5,7,8,10};
        const int *steps = gs_minor ? minor_steps : major_steps;
        int rel = (note - 48 - gs_root) % 12;
        if (rel < 0) rel += 12;
        int degree = 0, distance = 99;
        for (int i=0;i<7;i++) {
            int d = rel > steps[i] ? rel-steps[i] : steps[i]-rel;
            if (d < distance) { distance=d; degree=i; }
        }
        int base = 48 + gs_root + 12*((note-48-gs_root)/12);
        int notes[3];
        for (int i=0;i<3;i++) {
            int idx = degree + 2*i;
            notes[i] = base + steps[idx%7] + 12*(idx/7);
        }
        if (gs_last_chord == notes[0] && gs_latch) return;
        gs_last_chord = notes[0];
        /* Release the previous chord, then retune the sustained chord voices.
           Avoid copying multi-kilobyte reverb buffers on the UI thread. */
        gs_pad_note(&gs_voice, 0.0f, 0);
        gs_pad_note(&gs_fading_voice, 0.0f, 0);
        for (int i=0;i<2;i++) gs_pad_note(&gs_chord[i], 0.0f, 0);
        gs_pad *active[3] = {&gs_voice, &gs_chord[0], &gs_chord[1]};
        for (int i=0;i<3;i++) {
            /* Retain the envelope and wash so chord changes glide smoothly. */
            gs_pad_environment(active[i], gs_env_index, (float)gs_intensity_percent/100.0f);
            gs_pad_note(active[i], 440.0f*fm_exp2f((float)(notes[i]-69)/12.0f), 1);
        }
        gs_pad_key = note;
    } else if (gs_track == 0) {
        static const int major_scale[7] = {0,2,4,5,7,9,11};
        static const int minor_scale[7] = {0,2,3,5,7,8,10};
        const int *scale = gs_minor ? minor_scale : major_scale;
        int relative = (note - gs_root) % 12;
        if (relative < 0) relative += 12;
        int degree = 0, nearest = 100;
        for (int i=0;i<7;i++) {
            int delta = relative > scale[i] ? relative-scale[i] : scale[i]-relative;
            if (delta < nearest) { nearest=delta; degree=i; }
        }
        int locked = note + scale[degree] - relative;
        /* Preserve the previous melody as a fading voice rather than retuning
           an audible oscillator. Fresh melody fades in organically. */
        if (gs_melody.gate && gs_melody.target_hz != 440.0f*fm_exp2f((float)(locked-69)/12.0f)) {
            /* Sustain the existing pad envelope and glide its oscillator
               toward the next scale-locked note without resetting reverb. */
            gs_pad_environment(&gs_melody, gs_env_index, (float)gs_intensity_percent/100.0f);
        }
        gs_pad_note(&gs_melody, 440.0f*fm_exp2f((float)(locked-69)/12.0f), 1);\n    } else if (gs_track == 2) {\n        gs_drums_hit(&gs_drum_voice, (unsigned)(note >= 36 ? note - 36 : note), (float)vel / 127.0f);\n    } else if (gs_track == 3) {\n        gs_lead_note(&gs_lead_voice, 440.0f*fm_exp2f((float)(note-69)/12.0f), 1);\n    } else if (gs_track == 1) {
        /* Bass uses the same scale/chord keyboard, with monophonic root voicing. */
        static const int major_scale[7] = {0,2,4,5,7,9,11};
        static const int minor_scale[7] = {0,2,3,5,7,8,10};
        const int *scale = gs_minor ? minor_scale : major_scale;
        int relative = (note - gs_root) % 12;
        if (relative < 0) relative += 12;
        int degree = 0, nearest = 100;
        for (int i=0;i<7;i++) {
            int delta = relative > scale[i] ? relative-scale[i] : scale[i]-relative;
            if (delta < nearest) { nearest=delta; degree=i; }
        }
        int locked = note + scale[degree] - relative;
        if (gs_chord_select) {
            locked -= 12;
            gs_last_chord = locked;
        }
        gs_bass_key = note;
        gs_bass_note(&gs_bass_voice, 440.0f*fm_exp2f((float)(locked-69)/12.0f), 1);
    }''')

old='    if (voice_note == note)\n        voice_note = -1;'
assert app.count(old)==1
app=app.replace(old,'    if (voice_note == note) voice_note = -1;\n    if (gs_track == 0 && ((note % 12)!=1 && (note % 12)!=3 && (note % 12)!=6 && (note % 12)!=8 && (note % 12)!=10)) gs_pad_note(&gs_melody, 0.0f, 0);\n    if (gs_track == 3) gs_lead_note(&gs_lead_voice, 0, 0);\n    if (gs_bass_key == note && (!gs_latch || ((note % 12)!=1 && (note % 12)!=3 && (note % 12)!=6 && (note % 12)!=8 && (note % 12)!=10))) { gs_bass_note(&gs_bass_voice, 0.0f, 0); gs_bass_key = -1; }')
start=app.index('void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)')
end=app.index('\nvoid app_panic(void)',start)
app=app[:start]+'''void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)
{
    midi_in();
    uint32_t pad_gain = (uint32_t)((uint64_t)master_q12 * (unsigned)gs_knobs[0][8][0][0] / 100u);
    uint32_t bass_gain = (uint32_t)((uint64_t)master_q12 * (unsigned)gs_knobs[1][8][0][0] / 100u);
    uint32_t drum_gain = (uint32_t)((uint64_t)master_q12 * (unsigned)gs_knobs[2][8][0][0] / 100u);
    uint32_t lead_gain = (uint32_t)((uint64_t)master_q12 * (unsigned)gs_knobs[3][8][0][0] / 100u);
    int any_solo = gs_track_solo[0] || gs_track_solo[1] || gs_track_solo[2] || gs_track_solo[3];
    if (gs_track_mute[0] || (any_solo && !gs_track_solo[0])) pad_gain=0;
    if (gs_track_mute[1] || (any_solo && !gs_track_solo[1])) bass_gain=0;
    if (gs_track_mute[2] || (any_solo && !gs_track_solo[2])) drum_gain=0;
    if (gs_track_mute[3] || (any_solo && !gs_track_solo[3])) lead_gain=0;
    gs_pad_render(&gs_voice, lr, n, pad_gain);\n    gs_pad_mix(&gs_fading_voice, lr, n, pad_gain);\n    gs_pad_mix(&gs_melody, lr, n, pad_gain);\n    gs_pad_mix(&gs_melody_fading, lr, n, pad_gain);\n    for (int i=0;i<2;i++) { gs_pad_mix(&gs_chord[i], lr, n, pad_gain); gs_pad_mix(&gs_chord_fading[i], lr, n, pad_gain); }\n    gs_bass_mix(&gs_bass_voice, lr, n, bass_gain);\n    gs_lead_mix(&gs_lead_voice, lr, n, lead_gain);\n    gs_drums_mix(&gs_drum_voice, lr, n, drum_gain, gs_tempo);
}
'''+app[end:]
old='    voice_note = -1;\n    voice_level = 0.0f;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = -1;\n    gs_pad_key = -1; gs_bass_key = -1;\n    gs_pad_panic(&gs_voice);\n    gs_pad_panic(&gs_fading_voice);\n    gs_pad_panic(&gs_melody); gs_pad_panic(&gs_melody_fading);\n    for (int i=0;i<2;i++) { gs_pad_panic(&gs_chord[i]); gs_pad_panic(&gs_chord_fading[i]); }\n    gs_last_chord = -1;\n    gs_bass_panic(&gs_bass_voice);\n    gs_lead_note(&gs_lead_voice, 0, 0); gs_drums_panic(&gs_drum_voice);')
old='void app_init(void)\n{'
assert app.count(old)==1
app=app.replace(old,'void app_init(void)\n{\n    /* Nonzero mixer defaults: otherwise all four tracks are silent. */\n    for (int track=0;track<4;track++) gs_knobs[track][8][0][0] = 75;\n    gs_knobs[0][5][0][1] = 100; /* Four texture voices by default. */\n    gs_pad_init(&gs_voice);\n    gs_pad_init(&gs_fading_voice);\n    gs_pad_init(&gs_melody); gs_pad_init(&gs_melody_fading);\n    for (int i=0;i<2;i++) { gs_pad_init(&gs_chord[i]); gs_pad_init(&gs_chord_fading[i]); }\n    gs_bass_init(&gs_bass_voice);\n    gs_lead_init(&gs_lead_voice); gs_drums_init(&gs_drum_voice);')
# Physical keyboard: white notes, black chord triggers, last black latch.
app=app.replace('            note_on(note, v);', '''            if (gs_track == 2) {
                if (gs_page != 7) {
                    /* Outside SEQ the piano is a live drum kit, never a step editor. */
                    gs_drums_hit(&gs_drum_voice, (unsigned)k % 4u, (float)v / 127.0f);
                    app_say("DRUM LIVE", k % 4u == 0 ? "KICK" : k % 4u == 1 ? "SNARE" : k % 4u == 2 ? "HAT" : "PERC");
                } else if (k < 16) {
                    uint16_t bit = (uint16_t)(1u << k);
                    if (gs_page == 7 && gs_page_num == 1) gs_drum_voice.snare_steps[gs_drum_voice.pattern] ^= bit;
                    else if (gs_page == 7 && gs_page_num == 2) gs_drum_voice.hat_steps[gs_drum_voice.pattern] ^= bit;
                    else gs_drum_voice.kick_steps[gs_drum_voice.pattern] ^= bit;
                    app_say("DRUM STEP", "TOGGLE");
                } else if (k == 16) { gs_drums_set_playing(&gs_drum_voice, !(gs_drum_voice.playing || gs_drum_voice.queued_start), 1); app_say("DRUMS", gs_drum_voice.queued_start ? "QUEUED" : gs_drum_voice.playing ? "PLAY" : "STOP"); }
                else if (k == 17) { gs_drums_set_pattern(&gs_drum_voice, gs_drum_voice.queued_pattern ? (unsigned)(gs_drum_voice.queued_pattern - 1u) ^ 1u : gs_drum_voice.pattern ^ 1u, 1); app_say("PATTERN", gs_drum_voice.queued_pattern ? "NEXT BAR" : gs_drum_voice.pattern ? "B" : "A"); }
                else if (k == 18) { gs_drum_voice.fill ^= 1u; app_say("FILL", gs_drum_voice.fill ? "ON" : "OFF"); }
                else if (k == 19) { gs_drum_voice.mute ^= 1u; app_say("DRUM MUTE", gs_drum_voice.mute ? "ON" : "OFF"); }
            } else {
                gs_chord_select = ((note % 12)==1 || (note % 12)==3 || (note % 12)==6 || (note % 12)==8 || (note % 12)==10);
                if (k == 25) { gs_latch = !gs_latch; app_say("CHORD LATCH", gs_latch ? "ON" : "OFF"); }
                else note_on(note, v);
            }''')
app=app.replace('            note_off(note);', '''            if ((note % 12)==1 || (note % 12)==3 || (note % 12)==6 || (note % 12)==8 || (note % 12)==10) {
                if (!gs_latch && gs_track == 0) {
                    gs_pad_note(&gs_voice, 0.0f, 0);
                    for (int i=0;i<2;i++) gs_pad_note(&gs_chord[i], 0.0f, 0);
                    gs_last_chord = -1;
                }
            } else if (k != 25) note_off(note);''')
# The pad track is always ToneScape V2. PRESET selects one of its original\n# 16 environments, never an alternative synth engine. ALGO adjusts intensity.
old='        } else if (k == EN_PRESET) {\n            set.wave ^= 1u;\n            set_dirty = 1;\n            app_say("WAVE", WAVE_NAME[set.wave]);'
assert app.count(old)==1
app=app.replace(old,'        } else if (k == EN_PRESET) {\n            gs_env_index = (unsigned)(((int)gs_env_index + e % 16 + 16) % 16);\n            gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent / 100.0f);\n            app_say("TONESCAPE ENV", gs_env_names[gs_env_index]);\n        } else if (k == EN_ALGO) {\n            gs_intensity_percent += e * 5;\n            if (gs_intensity_percent < 0) gs_intensity_percent = 0;\n            if (gs_intensity_percent > 100) gs_intensity_percent = 100;\n            gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent / 100.0f);\n            int_text(gs_intensity_percent, t);\n            app_say("TONESCAPE INT", t);')
# Existing template wave setting is only 0..1; this integration keeps that
# setting for persistence and uses a separate transient environment selection.
# Avoid altering the stored wave's validation and existing PRESET behaviour.

# SLOOP control mapping: ALGORITHM chooses track, SELECT changes tempo/pages.
# HOME returns to TRACKS; tapping a function button opens/cycles its pages.
# These are navigation shells, not claims that recording/sequencing is ready.
app=app.replace('static unsigned gs_env_index;', 'static unsigned gs_env_index;\nstatic int gs_tempo = 90;\nstatic uint8_t gs_track_mute[4], gs_track_solo[4];\nstatic const unsigned gs_page_count[10] = {2,3,3,4,3,2,3,3,3,2};')
app=app.replace('        if (k == B_OCTDN)', '''        if (k == B_HOME) {
            if (gs_page == 0) gs_page_num = (gs_page_num + 1u) % 2u;
            else { gs_page = 0; gs_page_num = 0; }
            app_say("HOME", gs_page_num ? "VISUAL" : "TRACKS");
        } else if (k == B_ENV || k == B_LFO || k == B_FX ||
                   k == B_SEL || k == B_EDIT || k == B_ARP ||
                   k == B_SEQ || k == B_GLO || k == B_SAVE) {
            unsigned next = k == B_ENV ? 1u : k == B_LFO ? 2u :
                k == B_FX ? 3u : k == B_SEL ? 4u : k == B_EDIT ? 5u :
                k == B_ARP ? 6u : k == B_SEQ ? 7u : k == B_GLO ? 8u : 9u;
            if (gs_page == next) gs_page_num = (gs_page_num + 1u) % gs_page_count[next];
            else { gs_page = next; gs_page_num = 0; }
            app_say("PAGE", BTN_NAME[k]);
        } else if (k == B_OCTDN)''')
app=app.replace('        } else if (k == EN_PRESET) {', '''        } else if (k == EN_SELECT) {
            if (gs_page == 0) {
                gs_tempo += e;
                if (gs_tempo < 40) gs_tempo = 40;
                if (gs_tempo > 240) gs_tempo = 240;
                int_text(gs_tempo, t);
                app_say("BPM", t);
            } else {
                gs_page_num = (unsigned)(((int)gs_page_num + e % (int)gs_page_count[gs_page] + (int)gs_page_count[gs_page]) % (int)gs_page_count[gs_page]);
                app_say("PAGE", gs_page_num == 0 ? "1" : gs_page_num == 1 ? "2" : "3");
            }
        } else if (k == EN_PRESET) {''')
app=app.replace('        } else if (k == EN_ALGO) {', '''        } else if (k == EN_ALGO) {
            gs_track = (unsigned)(((int)gs_track + e % 4 + 4) % 4);
            app_say("TRACK", gs_track == 0 ? "TONESCAPE" : gs_track == 1 ? "BASS" : gs_track == 2 ? "DRUMS" : "LEAD");
        } else if (k == EN_K1) {''')
# The upstream template has no EN_SELECT/EN_K1 branches. Replace its real
# encoder fallback, otherwise all page/track/knob changes are display-only.
old_encoder = '''        } else {
            int_text(ui.turns[k], t);
            app_say(ENC_NAME[k], t);
        }
    }
    if (keys != ui.keys || btn != ui.btn)'''
assert app.count(old_encoder) == 1, "Upstream encoder handler changed"
app=app.replace(old_encoder, '''        } else if (k == EN_SELECT) {
            if (gs_page == 0) {
                gs_tempo += e;
                if (gs_tempo < 40) gs_tempo = 40;
                if (gs_tempo > 240) gs_tempo = 240;
                int_text(gs_tempo, t); app_say("BPM", t);
            } else {
                int count = (int)gs_page_count[gs_page];
                gs_page_num = (unsigned)(((int)gs_page_num + e % count + count) % count);
                int_text((int32_t)gs_page_num+1, t); app_say("PAGE", t);
            }
        } else if (k == EN_ALGO) {
            gs_track = (unsigned)(((int)gs_track + e % 4 + 4) % 4);
            app_say("TRACK", gs_track == 0 ? "TONESCAPE" : gs_track == 1 ? "BASS" : gs_track == 2 ? "DRUMS" : "LEAD");
        } else if (k >= EN_K1 && k <= EN_K4) {
            unsigned knob = (unsigned)(k - EN_K1);
            if (gs_page == 0 && gs_track == 0 && knob == 0) {
                gs_intensity_percent += e * 5;
                if (gs_intensity_percent < 0) gs_intensity_percent = 0;
                if (gs_intensity_percent > 100) gs_intensity_percent = 100;
                gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent/100.0f);
                int_text(gs_intensity_percent, t); app_say("INTENSITY", t);
            } else {
                int *v = &gs_knobs[gs_track][gs_page][gs_page_num][knob];
                *v += e;
                if (*v < 0) *v = 0;
                if (*v > 100) *v = 100;
                if (gs_page == 4 && gs_page_num == 0) {
                    if (knob == 0) { if (*v > 11) *v = 11; gs_root = *v; }
                    if (knob == 1) { *v = *v >= 50 ? 100 : 0; gs_minor = *v >= 50; }
                    if (knob == 2) gs_latch = *v >= 50;
                    gs_last_chord = -1;
                }
                if (gs_track == 0 && gs_page == 5 && gs_page_num == 0 && knob == 1) {
                    /* EDIT K2: selectable 2/3/4 texture voices per pad.
                       Default stays four until explicitly changed. */
                    unsigned voices = *v < 34 ? 2u : (*v < 67 ? 3u : 4u);
                    gs_pad *pads[8] = {&gs_voice,&gs_fading_voice,&gs_melody,&gs_melody_fading,&gs_chord[0],&gs_chord[1],&gs_chord_fading[0],&gs_chord_fading[1]};
                    for (int n=0;n<8;n++) pads[n]->texture_voices = (uint8_t)voices;
                }
                if (gs_track == 0 && gs_page == 5 && gs_page_num == 0 && knob == 0) {
                    gs_env_index = (unsigned)*v % 16u;
                    gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent/100.0f);
                }
                if (gs_track == 0 && gs_page == 1 && gs_page_num == 0 && knob < 2) {
                    float seconds = 0.1f + (float)*v * (knob == 0 ? .299f : .399f);
                    gs_pad *pads[8] = {&gs_voice,&gs_fading_voice,&gs_melody,&gs_melody_fading,&gs_chord[0],&gs_chord[1],&gs_chord_fading[0],&gs_chord_fading[1]};
                    for (int n=0;n<8;n++) {
                        if (knob == 0) pads[n]->attack_sec = seconds;
                        else pads[n]->release_sec = seconds;
                    }
                }
                if (gs_page == 5 && gs_page_num == 0) {
                    if (gs_track == 3 && knob == 0) gs_lead_voice.brightness = (float)*v/100.0f;
                    if (gs_track == 1 && knob == 0) gs_bass_voice.cutoff = 0.015f + (float)*v*0.003f;
                    if (gs_track == 2 && knob == 0) gs_drums_set_pattern(&gs_drum_voice, (unsigned)(*v >= 50), 1);
                }
                if (gs_track == 0 && gs_page == 2 && gs_page_num == 0) {
                    /* Motion page: gentle pitch drift rate (K1) and depth (K2). */
                    if (knob == 0 || knob == 1) {
                        float glide = 0.25f + (float)gs_knobs[0][2][0][0]*.12f;
                        float depth = (float)gs_knobs[0][2][0][1]/100.f;
                        gs_pad *pads[8] = {&gs_voice,&gs_fading_voice,&gs_melody,&gs_melody_fading,&gs_chord[0],&gs_chord[1],&gs_chord_fading[0],&gs_chord_fading[1]};
                        for(int n=0;n<8;n++) pads[n]->glide_sec = glide * (1.f + depth);
                    }
                }
                if (gs_page == 1 && gs_page_num == 0 && gs_track == 0 && knob < 2) {
                    /* ENV edits also apply to the melody tail, not just active chord pads. */
                    gs_melody_fading.attack_sec = gs_melody.attack_sec;
                    gs_melody_fading.release_sec = gs_melody.release_sec;
                }
                if (gs_page == 5 && gs_page_num == 0 && gs_track == 2 && knob == 1) {
                    /* Drum EDIT K2 enables/disables fills during playback. */
                    gs_drum_voice.fill = (uint8_t)(*v >= 50);
                }
                if (gs_page == 8 && gs_page_num == 1) {
                    if (knob == 0) gs_track_mute[gs_track] = *v >= 50;
                    if (knob == 1) gs_track_solo[gs_track] = *v >= 50;
                }
                if (gs_page == 7 && gs_track == 2 && knob == 0) gs_drums_set_playing(&gs_drum_voice, *v >= 50, 1);
                int_text(*v, t); app_say("PARAM", t);
            }
        } else {
            int_text(ui.turns[k], t);
            app_say(ENC_NAME[k], t);
        }
    }
    if (keys != ui.keys || btn != ui.btn)''')
# Four physical encoders follow the selected screen, with separate page values.
# K1 on TRACKS continues to control the real ToneScape intensity.
app=app.replace('static int gs_tempo = 90;', 'static int gs_tempo = 90;\nstatic int gs_knobs[4][10][4][4];')
app=app.replace('        } else if (k == EN_K1) {', '''        } else if (k >= EN_K1 && k <= EN_K4) {
            unsigned knob = (unsigned)(k - EN_K1);
            if (gs_page == 0 && gs_track == 0 && knob == 0) {''')
app=app.replace('            app_say("TONESCAPE INT", t);', '''            app_say("TONESCAPE INT", t);
            } else {
                int *v = &gs_knobs[gs_track][gs_page][gs_page_num][knob];
                *v += e;
                if (*v < 0) *v = 0;
                if (*v > 100) *v = 100;
                int_text(*v, t);
                if (gs_track == 0 && gs_page == 4 && gs_page_num == 0) {
                    if (knob == 0) { if (*v > 11) *v = 11; gs_root = *v; }
                    if (knob == 1) gs_minor = *v % 2;
                    if (knob == 2) gs_latch = *v >= 50;
                    gs_last_chord = -1;
                }
                if (gs_track == 0 && gs_page == 5 && gs_page_num == 0 && knob == 1) {
                    /* EDIT K2: selectable 2/3/4 texture voices per pad.
                       Default stays four until explicitly changed. */
                    unsigned voices = *v < 34 ? 2u : (*v < 67 ? 3u : 4u);
                    gs_pad *pads[8] = {&gs_voice,&gs_fading_voice,&gs_melody,&gs_melody_fading,&gs_chord[0],&gs_chord[1],&gs_chord_fading[0],&gs_chord_fading[1]};
                    for (int n=0;n<8;n++) pads[n]->texture_voices = (uint8_t)voices;
                }
                if (gs_track == 0 && gs_page == 5 && gs_page_num == 0 && knob == 0) {
                    gs_env_index = (unsigned)(*v) % 16u;
                    gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent / 100.0f);
                }
                app_say("PAGE VALUE", t);
            }''')
# The last replacement redirects the former intensity branch into K1, so
# ALGORITHM remains dedicated to track selection like SLOOP.
old='    for (i = 0; i < NB; i++)\n        cell(4 + (int32_t)(i % 4u) * 58, (int32_t)(i / 4u) * 21, 56, BTN_NAME[i], (ui.btn >> i) & 1u);'
assert app.count(old)==1
app=app.replace(old, '''    if (gs_page == 0) {
        static const char *const names[4] = {"TONESCAPE", "BASS", "DRUMS", "LEAD"};
        static const char *const desc[4] = {"AMBIENT", "SUB BASS", "SEQUENCER", "SPARKLE"};
        static const uint16_t track_color[4] = {0x4C7F, 0x4E6A, 0xF6A0, 0xE3DF};
        cv_text(8, 2, &FONT_B, gs_page_num ? "VISUAL" : "TRACKS", C_WHITE);
        for (i = 0; i < 4; i++) {
            int32_t y = 23 + (int32_t)i * 25;
            cv_rect(4, y, 5, 22, track_color[i]);
            cv_rect(12, y, 224, 22, i == gs_track ? track_color[i] : C_LINE);
            cv_text(18, y + 2, &FONT_XS, names[i], i == gs_track ? C_BLACK : C_WHITE);
            cv_text(133, y + 2, &FONT_XS, desc[i], i == gs_track ? C_BLACK : C_GRAY);
        }
        int_text(gs_tempo, t);
        cv_text(8, 127, &FONT_XS, "BPM", C_GRAY);
        cv_text(45, 127, &FONT_XS, t, C_HI);
        cv_text(100, 127, &FONT_XS, "ALGO: TRACK", C_GRAY);
    } else {
        static const char *const pages[] = {"TRACKS", "ENV", "LFO", "FX", "SCALE", "EDIT", "ARP", "SEQ", "MIX", "SONG"};
        static const uint16_t track_color[4] = {0x4C7F, 0x4E6A, 0xF6A0, 0xE3DF};
        cv_rect(4, 3, 5, 22, track_color[gs_track]);
        cv_text(15, 4, &FONT_B, pages[gs_page], C_WHITE);
        cv_text(170, 7, &FONT_XS, gs_page_num == 0 ? "PAGE 1" : gs_page_num == 1 ? "PAGE 2" : gs_page_num == 2 ? "PAGE 3" : "PAGE 4", C_HI);
        cv_rect(6, 31, 228, 85, C_LINE);
        cv_text(14, 40, &FONT_XS, gs_track == 0 ? "TONESCAPE" : gs_track == 1 ? "BASS" : gs_track == 2 ? "DRUMS" : "LEAD", track_color[gs_track]);
        static const char *const labels[10][4] = {
            {"TRACKS", "VISUAL", "", ""},
            {"ATTACK / RELEASE", "SHAPE / TONE", "LEVEL / WIDTH", ""},
            {"RATE / DEPTH", "DRIFT / MOTION", "STEREO / MOD", ""},
            {"REVERB / WASH", "DELAY / ECHO", "FILTER / EQ", "MASTER FX"},
            {"KEY / SCALE", "CHORD / VOICING", "TRANSPOSE", ""},
            {"SOUND / ENGINE", "TRACK EDIT", "", ""},
            {"ARP MODE", "RATE / GATE", "PATTERN", ""},
            {"STEPS / GRID", "NOTES / LENGTH", "QUANT / SWING", ""},
            {"TRACK LEVELS", "MUTE / SOLO", "GLOBAL / BPM", ""},
            {"SECTIONS A-D", "SAVE / LOAD", "", ""}
        };
        if (gs_page == 7 && gs_track == 2) {
            uint16_t steps = gs_page_num == 1 ? gs_drum_voice.snare_steps[gs_drum_voice.pattern] :
                gs_page_num == 2 ? gs_drum_voice.hat_steps[gs_drum_voice.pattern] :
                gs_drum_voice.kick_steps[gs_drum_voice.pattern];
            cv_text(14, 54, &FONT_XS, gs_page_num == 1 ? "SNARE" : gs_page_num == 2 ? "HAT" : "KICK", C_WHITE);
            for (i=0;i<16;i++) {
                uint16_t color = (steps & (1u<<i)) ? track_color[2] : C_LINE;
                cv_rect(14+(int32_t)i*13, 77, 11, 11, color);
            }
        } else {
            cv_text(14, 67, &FONT_XS, labels[gs_page][gs_page_num], C_WHITE);
        }
        for (i = 0; i < 4; i++) {
            char val[12];
            int_text(gs_knobs[gs_track][gs_page][gs_page_num][i], val);
            cv_text(14 + (int32_t)i * 56, 94, &FONT_XS, ENC_NAME[EN_K1 + i], C_GRAY);
            cv_text(14 + (int32_t)i * 56, 109, &FONT_XS, val, track_color[gs_track]);
        }
        cv_text(8, 128, &FONT_XS, "SELECT: PAGE  HOME: TRACKS", C_GRAY);
    }''')
app=app.replace('    gs_track = 0; gs_tracks_page = 1;', '    gs_track = 0; gs_page = 0; gs_page_num = 0; gs_tempo = 90;')
# The template draws a second set of encoder counters over the new page UI.
# Remove that obsolete overlay; GrooveScape already draws K1-K4 values itself.
old_enc = '''    for (i = 0; i < NE; i++) {
        int32_t x = 4 + (int32_t)(i % 4u) * 58, y = 88 + (int32_t)(i / 4u) * 28;
        int lit = ui.turned_at[i] && now - ui.turned_at[i] < 300u;
        cv_text(x, y, &FONT_XS, ENC_NAME[i], lit ? C_HI : C_GRAY);
        int_text(ui.turns[i], t);
        cv_text(x, y + 13, &FONT_XS, t, lit ? C_WHITE : C_DIM);
    }
'''
assert app.count(old_enc) == 1, "Template encoder overlay changed"
app = app.replace(old_enc, '')
# Display the actual environment, rather than the now-unused sine/triangle setting.
old='cv_text(112, 36, &FONT_XS, WAVE_NAME[set.wave], C_HI);'
assert app.count(old)==1
app=app.replace(old,'cv_text(112, 36, &FONT_XS, gs_env_names[gs_env_index], C_HI);')
# The template oscillator variables are unused after replacing its renderer.
app=app.replace('static float voice_phase, voice_level, gain_now;   /* gain_now glides to MASTER: no step at a block\'s edge */', '')
app=app.replace('static volatile float voice_vel = 1.0f;', '')
app=app.replace('    voice_vel = (float)vel / 127.0f;\n', '')
app=app.replace('static void note_on(int32_t note, uint32_t vel)\n{', 'static void note_on(int32_t note, uint32_t vel)\n{\n    (void)vel;')
# The legacy voice_level line in app_panic is removed only after the
# original panic block has been replaced; avoid broad substitutions.
# Keep the native screen and audio environment synchronized at boot.
# In particular, resetting the DSP must not leave a stale UI selection.
# Initialise scale editor to actual ToneScape defaults rather than zeroed placeholders.
app=app.replace('    gs_bass_init(&gs_bass_voice);\n    gs_lead_init(&gs_lead_voice); gs_drums_init(&gs_drum_voice);', '    gs_bass_init(&gs_bass_voice);\n    gs_lead_init(&gs_lead_voice); gs_drums_init(&gs_drum_voice);\n    for (int tr=0;tr<4;tr++) gs_knobs[tr][8][0][0]=100;\n    gs_knobs[0][1][0][0]=13; gs_knobs[0][1][0][1]=20;\n    gs_knobs[0][4][0][0] = 9; gs_knobs[0][4][0][1] = 0; gs_knobs[0][4][0][2] = 100;')
app=app.replace('    gs_pad_init(&gs_voice);', '    gs_pad_key = -1; gs_bass_key = -1;\n    gs_env_index = 0;\n    gs_intensity_percent = 35;\n    gs_pad_init(&gs_voice);\n    gs_pad_environment(&gs_voice, gs_env_index, 0.35f);')
# The template only supports BLE when configured; keep all Bluetooth paths
# off in this unverified native prototype to avoid hardware crash regressions.
assert app.count('static gs_pad gs_voice;') == 1
assert 'gs_pad_note(active[i]' in app
assert app.count('gs_pad_environment(&gs_voice,') >= 3
assert app.count('void app_render(') == 1
# The pad environment starts from the default profile until PRESET is turned.
# Preserve the template's original settings schema for this host-only prototype.
# Catch template drift before passing generated C to the compiler.
assert app.count('gs_pad_render(&gs_voice, lr, n, pad_gain);') == 1
assert app.count('gs_bass_mix(&gs_bass_voice, lr, n, bass_gain);') == 1
assert app.count('gs_pad_panic(&gs_voice);') >= 1
assert app.count('gs_pad_init(&gs_voice);') >= 1
assert 'voice_level' not in app and 'voice_phase' not in app and 'gain_now' not in app
assert 'voice_vel' not in app
(target/"app.c").write_text(app)
h=(target/"app.h").read_text().replace('#define APP_NAME "TEMPLATE"','#define APP_NAME "GROOVESCAPE"')
(target/"app.h").write_text(h)
toml=(target/"fm1.toml").read_text().replace('name = "TEMPLATE"','name = "GROOVESCAPE"').replace('usb_product = "TEMPLATE FM-1"','usb_product = "GrooveScape FM-1"').replace('ble = true','ble = false').replace('ble_central = true','ble_central = false').replace('id_prefix = "FM-1_11"','id_prefix = "FM-1_9017"')
assert 'o2 = []' in toml, 'Review upstream O2 build configuration'
toml = toml.replace('o2 = []', 'o2 = ["pad_dsp.c", "bass_dsp.c", "extra_dsp.c"]')
(target/"fm1.toml").write_text(toml)
print(f"Generated {target}. Build with: {base}/tools/build.py {target} --host")
print("BLE disabled; prototype ID. DO NOT FLASH hardware.")
