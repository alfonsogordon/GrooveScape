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
app=app.replace(anchor,anchor+'\n#include "pad_dsp.h"\nstatic gs_pad gs_voice;\n#include \"bass_dsp.h\"\nstatic gs_bass gs_bass_voice;')
# Expose the active pad environment on the real FM1 screen.
app=app.replace('static gs_pad gs_voice;', 'static gs_pad gs_voice;\nstatic unsigned gs_env_index;\nstatic const char *const gs_env_names[16] = {\n    "DRIFT", "BLOOM", "EMBER", "GLASS CHOIR", "DEEP FOREST", "CATHEDRAL",\n    "OCEAN", "RIFT", "MIST", "MACHINE AIR", "TAPE GHOST", "HOLLOW EARTH",\n    "NEON WEATHER", "ICE BLOOM", "AURORA BODY", "NOIR VOID"\n};')
old='    voice_vel = (float)vel / 127.0f;\n    voice_note = note;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = note;\n    if (note < 48) {\n        gs_pad_note(&gs_voice, 0.0f, 0);\n        gs_bass_note(&gs_bass_voice, 440.0f * fm_exp2f((float)(note - 69) / 12.0f), 1);\n    } else {\n        gs_bass_note(&gs_bass_voice, 0.0f, 0);\n        gs_pad_note(&gs_voice, 440.0f * fm_exp2f((float)(note - 69) / 12.0f), 1);\n    }')
old='    if (voice_note == note)\n        voice_note = -1;'
assert app.count(old)==1
app=app.replace(old,'    if (voice_note == note) {\n        voice_note = -1;\n        gs_pad_note(&gs_voice, 0.0f, 0);\n        gs_bass_note(&gs_bass_voice, 0.0f, 0);\n    }')
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
app=app.replace(old,'    voice_note = -1;\n    voice_level = 0.0f;\n    gs_pad_panic(&gs_voice);\n    gs_bass_panic(&gs_bass_voice);')
old='void app_init(void)\n{'
assert app.count(old)==1
app=app.replace(old,'void app_init(void)\n{\n    gs_pad_init(&gs_voice);\n    gs_bass_init(&gs_bass_voice);')
# PRESET encoder steps the environment; no B_FX button exists upstream.
old='        } else if (k == EN_PRESET) {\n            set.wave ^= 1u;\n            set_dirty = 1;\n            app_say("WAVE", WAVE_NAME[set.wave]);'
assert app.count(old)==1
app=app.replace(old,'        } else if (k == EN_PRESET) {\n            gs_env_index = (unsigned)(((int)gs_env_index + e % 16 + 16) % 16);\n            gs_pad_environment(&gs_voice, gs_env_index, 0.65f);\n            app_say("PAD", gs_env_names[gs_env_index]);')
# Existing template wave setting is only 0..1; this integration keeps that
# setting for persistence and uses a separate transient environment selection.
# Avoid altering the stored wave's validation and existing PRESET behaviour.

# Display the actual environment, rather than the now-unused sine/triangle setting.
old='cv_text(112, 36, &FONT_XS, WAVE_NAME[set.wave], C_HI);'
assert app.count(old)==1
app=app.replace(old,'cv_text(112, 36, &FONT_XS, gs_env_names[gs_env_index], C_HI);')
# The template oscillator variables are unused after replacing its renderer.
app=app.replace('static float voice_phase, voice_level, gain_now;   /* gain_now glides to MASTER: no step at a block\'s edge */', '')
app=app.replace('static volatile float voice_vel = 1.0f;', '')
app=app.replace('    voice_vel = (float)vel / 127.0f;\n', '')
app=app.replace('static void note_on(int32_t note, uint32_t vel)\n{', 'static void note_on(int32_t note, uint32_t vel)\n{\n    (void)vel;')
app=app.replace('    voice_level = 0.0f;\n', '')
# Keep the native screen and audio environment synchronized at boot.
# In particular, resetting the DSP must not leave a stale UI selection.
app=app.replace('    gs_pad_init(&gs_voice);', '    gs_env_index = 0;\n    gs_pad_init(&gs_voice);\n    gs_pad_environment(&gs_voice, gs_env_index, 0.65f);')
# The template only supports BLE when configured; keep all Bluetooth paths
# off in this unverified native prototype to avoid hardware crash regressions.
assert app.count('static gs_pad gs_voice;') == 1
assert app.count('gs_pad_note(&gs_voice,') == 3
assert app.count('gs_pad_environment(&gs_voice,') == 2
assert app.count('void app_render(') == 1
# The pad environment starts from the default profile until FX is pressed.
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
