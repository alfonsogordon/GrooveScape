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
for filename in ("pad_dsp.c","pad_dsp.h"):
    shutil.copyfile(root/"firmware/audio"/filename,target/filename)
app=(target/"app.c").read_text()
anchor='#include "fastmath.h"'
assert app.count(anchor)==1
app=app.replace(anchor,anchor+'\n#include "pad_dsp.h"\nstatic gs_pad gs_voice;')
old='    voice_vel = (float)vel / 127.0f;\n    voice_note = note;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = note;\n    gs_pad_note(&gs_voice, 440.0f * fm_exp2f((float)(note - 69) / 12.0f), 1);')
old='    if (voice_note == note)\n        voice_note = -1;'
assert app.count(old)==1
app=app.replace(old,'    if (voice_note == note) {\n        voice_note = -1;\n        gs_pad_note(&gs_voice, 0.0f, 0);\n    }')
start=app.index('void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)')
end=app.index('\nvoid app_panic(void)',start)
app=app[:start]+'''void app_render(int32_t *lr, uint32_t n, uint32_t master_q12)
{
    midi_in();
    gs_pad_render(&gs_voice, lr, n, master_q12);
}
'''+app[end:]
old='    voice_note = -1;\n    voice_level = 0.0f;'
assert app.count(old)==1
app=app.replace(old,'    voice_note = -1;\n    voice_level = 0.0f;\n    gs_pad_panic(&gs_voice);')
old='void app_init(void)\n{'
assert app.count(old)==1
app=app.replace(old,'void app_init(void)\n{\n    gs_pad_init(&gs_voice);')
old='        else if (k == B_OCTUP)\n            octave_step(1);'
assert app.count(old)==1
app=app.replace(old,old+'\n        else if (k == B_FX) {\n            set.wave = (set.wave + 1u) % 16u;\n            gs_pad_environment(&gs_voice, set.wave, 0.65f);\n            set_dirty = 1;\n            app_say("PAD", "ENVIRONMENT");\n        }')
# Existing template wave setting is only 0..1; this integration keeps that
# setting for persistence and uses a separate transient environment selection.
# Avoid altering the stored wave's validation and existing PRESET behaviour.
app=app.replace('            set.wave = (set.wave + 1u) % 16u;\n            gs_pad_environment(&gs_voice, set.wave, 0.65f);\n            set_dirty = 1;', '            static unsigned env_index;\n            env_index = (env_index + 1u) % 16u;\n            gs_pad_environment(&gs_voice, env_index, 0.65f);')
# The template oscillator variables are unused after replacing its renderer.
app=app.replace('static float voice_phase, voice_level, gain_now;   /* gain_now glides to MASTER: no step at a block\'s edge */', '')
app=app.replace('static volatile float voice_vel = 1.0f;', '')
app=app.replace('    voice_vel = (float)vel / 127.0f;\n', '')
app=app.replace('static void note_on(int32_t note, uint32_t vel)\n{', 'static void note_on(int32_t note, uint32_t vel)\n{\n    (void)vel;')
app=app.replace('    voice_level = 0.0f;\n', '')
# The pad environment starts from the default profile until FX is pressed.
# Preserve the template's original settings schema for this host-only prototype.
# Catch template drift before passing generated C to the compiler.
assert app.count('gs_pad_render(&gs_voice, lr, n, master_q12);') == 1
assert app.count('gs_pad_panic(&gs_voice);') == 1
assert app.count('gs_pad_init(&gs_voice);') == 1
assert 'voice_level' not in app and 'voice_phase' not in app and 'gain_now' not in app
assert 'voice_vel' not in app
(target/"app.c").write_text(app)
h=(target/"app.h").read_text().replace('#define APP_NAME "TEMPLATE"','#define APP_NAME "GROOVESCAPE"')
(target/"app.h").write_text(h)
toml=(target/"fm1.toml").read_text().replace('name = "TEMPLATE"','name = "GROOVESCAPE"').replace('usb_product = "TEMPLATE FM-1"','usb_product = "GrooveScape FM-1"').replace('ble = true','ble = false').replace('ble_central = true','ble_central = false').replace('id_prefix = "FM-1_11"','id_prefix = "FM-1_9017"')
assert 'o2 = []' in toml, 'Review upstream O2 build configuration'
toml = toml.replace('o2 = []', 'o2 = ["pad_dsp.c"]')
(target/"fm1.toml").write_text(toml)
print(f"Generated {target}. Build with: {base}/tools/build.py {target} --host")
print("BLE disabled; prototype ID. DO NOT FLASH hardware.")
