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
for filename in ("pad_dsp.c","pad_dsp.h","bass_dsp.c","bass_dsp.h"):
    shutil.copyfile(root/"firmware/audio"/filename,target/filename)
app=(target/"app.c").read_text()
anchor='#include "fastmath.h"'
assert app.count(anchor)==1
app=app.replace(anchor,anchor+'\n#include "pad_dsp.h"\nstatic gs_pad gs_voice;\n#include \"bass_dsp.h\"\nstatic gs_bass gs_bass_voice;\nstatic int gs_pad_key = -1, gs_bass_key = -1;')
# Expose the active pad environment on the real FM1 screen.
app=app.replace('static gs_pad gs_voice;', 'static gs_pad gs_voice;\nstatic unsigned gs_env_index;\nstatic int gs_intensity_percent = 65;\nstatic const char *const gs_env_names[16] = {\n    "DRIFT", "BLOOM", "EMBER", "GLASS CHOIR", "DEEP FOREST", "CATHEDRAL",\n    "OCEAN", "RIFT", "MIST", "MACHINE AIR", "TAPE GHOST", "HOLLOW EARTH",\n    "NEON WEATHER", "ICE BLOOM", "AURORA BODY", "NOIR VOID"\n};')
old='    voice_vel = (float)vel / 127.0f;\n    voice_note = note;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = note;\n    if (note < 48) {\n        gs_bass_key = note;\n        gs_bass_note(&gs_bass_voice, 440.0f * fm_exp2f((float)(note - 69) / 12.0f), 1);\n    } else {\n        gs_pad_key = note;\n        gs_pad_note(&gs_voice, 440.0f * fm_exp2f((float)(note - 69) / 12.0f), 1);\n    }')
old='    if (voice_note == note)\n        voice_note = -1;'
assert app.count(old)==1
app=app.replace(old,'    if (voice_note == note) voice_note = -1;\n    if (gs_pad_key == note) { gs_pad_note(&gs_voice, 0.0f, 0); gs_pad_key = -1; }\n    if (gs_bass_key == note) { gs_bass_note(&gs_bass_voice, 0.0f, 0); gs_bass_key = -1; }')
start=app.index('void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)')
end=app.index('\nvoid app_panic(void)',start)
app=app[:start]+'''void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)
{
    midi_in();
    gs_pad_render(&gs_voice, lr, n, master_q12);\n    gs_bass_mix(&gs_bass_voice, lr, n, master_q12);
}
'''+app[end:]
old='    voice_note = -1;\n    voice_level = 0.0f;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = -1;\n    gs_pad_key = -1; gs_bass_key = -1;\n    gs_pad_panic(&gs_voice);\n    gs_bass_panic(&gs_bass_voice);')
old='void app_init(void)\n{'
assert app.count(old)==1
app=app.replace(old,'void app_init(void)\n{\n    gs_pad_init(&gs_voice);\n    gs_bass_init(&gs_bass_voice);')
# The pad track is always ToneScape V2. PRESET selects one of its original\n# 16 environments, never an alternative synth engine. ALGO adjusts intensity.
old='        } else if (k == EN_PRESET) {\n            set.wave ^= 1u;\n            set_dirty = 1;\n            app_say("WAVE", WAVE_NAME[set.wave]);'
assert app.count(old)==1
app=app.replace(old,'        } else if (k == EN_PRESET) {\n            gs_env_index = (unsigned)(((int)gs_env_index + e % 16 + 16) % 16);\n            gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent / 100.0f);\n            app_say("TONESCAPE ENV", gs_env_names[gs_env_index]);\n        } else if (k == EN_ALGO) {\n            gs_intensity_percent += e * 5;\n            if (gs_intensity_percent < 0) gs_intensity_percent = 0;\n            if (gs_intensity_percent > 100) gs_intensity_percent = 100;\n            gs_pad_environment(&gs_voice, gs_env_index, (float)gs_intensity_percent / 100.0f);\n            int_text(gs_intensity_percent, t);\n            app_say("TONESCAPE INT", t);\n            } else {\n                int_text((int32_t)gs_page_num + 1, t);\n                app_say("PAGE KNOB", t);\n            }')
# Existing template wave setting is only 0..1; this integration keeps that
# setting for persistence and uses a separate transient environment selection.
# Avoid altering the stored wave's validation and existing PRESET behaviour.

# SLOOP control mapping: ALGORITHM chooses track, SELECT changes tempo/pages.
# HOME returns to TRACKS; tapping a function button opens/cycles its pages.
# These are navigation shells, not claims that recording/sequencing is ready.
app=app.replace('static unsigned gs_env_index;', 'static unsigned gs_env_index;\nstatic unsigned gs_track, gs_page, gs_page_num;\nstatic int gs_tempo = 90;\nstatic const unsigned gs_page_count[10] = {2,3,3,4,3,2,3,3,3,2};')
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
            app_say("TRACK", gs_track == 0 ? "TONESCAPE" : gs_track == 1 ? "BASS" : gs_track == 2 ? "DRUMS PLANNED" : "LEAD PLANNED");
        } else if (k >= EN_K1 && k <= EN_K4) {
            unsigned knob = k - EN_K1;
            if (gs_page == 0 && gs_track == 0 && knob == 0) {''')
# The last replacement redirects the former intensity branch into K1, so
# ALGORITHM remains dedicated to track selection like SLOOP.
old='    for (i = 0; i < NB; i++)\n        cell(4 + (int32_t)(i % 4u) * 58, (int32_t)(i / 4u) * 21, 56, BTN_NAME[i], (ui.btn >> i) & 1u);'
assert app.count(old)==1
app=app.replace(old, '''    if (gs_page == 0) {
        static const char *const names[4] = {"TONESCAPE", "BASS", "DRUMS", "LEAD"};
        static const char *const desc[4] = {"AMBIENT", "SUB BASS", "COMING", "COMING"};
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
        cv_text(14, 67, &FONT_XS, labels[gs_page][gs_page_num], C_WHITE);
        cv_text(14, 95, &FONT_XS, "LAYOUT PREVIEW", C_GRAY);
        cv_text(8, 128, &FONT_XS, "SELECT: PAGE  HOME: TRACKS", C_GRAY);
    }''')
app=app.replace('    gs_track = 0; gs_tracks_page = 1;', '    gs_track = 0; gs_page = 0; gs_page_num = 0; gs_tempo = 90;')
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
app=app.replace('    gs_pad_init(&gs_voice);', '    gs_pad_key = -1; gs_bass_key = -1;\n    gs_env_index = 0;\n    gs_intensity_percent = 65;\n    gs_pad_init(&gs_voice);\n    gs_pad_environment(&gs_voice, gs_env_index, 0.65f);')
# The template only supports BLE when configured; keep all Bluetooth paths
# off in this unverified native prototype to avoid hardware crash regressions.
assert app.count('static gs_pad gs_voice;') == 1
assert app.count('gs_pad_note(&gs_voice,') == 2
assert app.count('gs_pad_environment(&gs_voice,') == 3
assert app.count('void app_render(') == 1
# The pad environment starts from the default profile until PRESET is turned.
# Preserve the template's original settings schema for this host-only prototype.
# Catch template drift before passing generated C to the compiler.
assert app.count('gs_pad_render(&gs_voice, lr, n, master_q12);') == 1
assert app.count('gs_bass_mix(&gs_bass_voice, lr, n, master_q12);') == 1
assert app.count('gs_pad_panic(&gs_voice);') == 1
assert app.count('gs_pad_init(&gs_voice);') == 1
assert 'voice_level' not in app and 'voice_phase' not in app and 'gain_now' not in app
assert 'voice_vel' not in app
(target/"app.c").write_text(app)
h=(target/"app.h").read_text().replace('#define APP_NAME "TEMPLATE"','#define APP_NAME "GROOVESCAPE"')
(target/"app.h").write_text(h)
toml=(target/"fm1.toml").read_text().replace('name = "TEMPLATE"','name = "GROOVESCAPE"').replace('usb_product = "TEMPLATE FM-1"','usb_product = "GrooveScape FM-1"').replace('ble = true','ble = false').replace('ble_central = true','ble_central = false').replace('id_prefix = "FM-1_11"','id_prefix = "FM-1_9017"')
assert 'o2 = []' in toml, 'Review upstream O2 build configuration'
toml = toml.replace('o2 = []', 'o2 = ["pad_dsp.c", "bass_dsp.c"]')
(target/"fm1.toml").write_text(toml)
print(f"Generated {target}. Build with: {base}/tools/build.py {target} --host")
print("BLE disabled; prototype ID. DO NOT FLASH hardware.")
