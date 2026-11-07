# GrooveScape: FM1-native implementation plan

## Target
The browser companion must eventually execute the same FM1 firmware UI and DSP code as the device (WebAssembly host build), not an independent HTML lookalike. The existing `index.html` is a **temporary standalone prototype**, not the target emulator.

## Candidate foundation
Evaluate [fm1-base](https://github.com/charlesvestal/fm1-base) (MPL-2.0) for hardware/host/web abstraction, and [Hortator](https://github.com/DeadActive/hortator) (GPL-3.0-only) for the SMC BLE MIDI implementation. Verify licenses, compatibility, build toolchain, audio callbacks and BLE API before choosing. Do not transplant GPL source into an incompatible-licensed build.

## Firmware structure (proposed)
- `firmware/app/`: single application state, transport, UI event handlers and screen renderer
- `firmware/audio/`: pad, bass, lead, drums, effects and fixed-size audio mixer
- `firmware/generative/`: deterministic lead pattern generator with repeatable seeds
- `firmware/midi/`: SMC protocol mapping, BLE event queues and USB MIDI
- `firmware/platform/`: FM1 and WebAssembly host adapters
- `web/`: virtual FM1 device shell, controls, installer (disabled until validated), preset manager
- `tests/`: host audio tests, control parity, MIDI parser, pattern determinism and memory budget

## FM1 interface requirements
- Native 240x240 display framebuffer and original button/key/encoder scan semantics.
- Shared screen renderer and event handler on hardware and web, not duplicated HTML menus.
- Four channels PAD / BASS / LEAD / DRUMS, plus submix kick/snare/hats/percussion.
- ToneScape environment presets and intensity, long envelopes, subtle drift and stereo space, adapted to FM1 resources.
- Physical FM1 master volume stays master; SMC faders 1-8 map to PAD/BASS/LEAD/DRUMS/KICK/SNARE/HATS/PERC.
- Eight SMC knobs edit selected track's reverb, size, delay, feedback, cutoff, resonance, shimmer, width.
- Bluetooth is disabled by default; reserve RAM/flash/CPU and test worst-case load.

## Basilisk request
User specifically wants **the last algorithm described in the Wirehead Basilisk manual**, not a generic random melody generator. Manual: https://wireheadinstruments.com/s/Wirehead-Basilisk-Operation-Manual-v10.pdf . The exact algorithm name, mechanics, and source license have **not yet been verified**; do not label the existing seeded generator as a faithful implementation. Find the algorithm's original implementation and inspect the license before porting. Preserve clock, note trigger, scale, mutation and seed semantics.

## Milestones
1. Choose and build the platform with a reproducible native simulator + WebAssembly target.
2. Render a firmware-owned 240x240 UI in both hosts; test physical key/encoder mapping in browser.
3. Port one ToneScape environment and verify deterministic audio render without BLE.
4. Add bass, lead, drums and shared transport, preserving headroom for BLE.
5. Integrate and stress-test BLE SMC mixer, reconnect and failure recovery.
6. Produce checked firmware package with recovery and a guarded web flasher.

No hardware-ready image should be published until linker-map budgets, firmware packaging and recovery have passed checks.
