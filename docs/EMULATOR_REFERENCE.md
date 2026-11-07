# Browser emulator reference: JIANT

User-approved reference: https://play.thefirmwarehub.com/?fw=jiant

Verified findings:
- The Firmware Hub uses Joakim Eriksson's fm1-emu browser emulator, which runs firmware update packages unchanged with front panel, screen, keys, knobs and audio.
- Source: https://github.com/joakimeriksson/fm1-emu (MIT).
- JIANT itself: https://github.com/juanjiant-bit/JIANT (GPL-3.0-only). Its firmware/web builds provide another example of shared hardware/browser behaviour.
- GrooveScape must target a real FM1-compatible .fwsc package, not an HTML imitation. The firmware hub player could then run it through fm1-emu when packaged correctly.
- Do not copy JIANT visual style or sound; only use the emulator interaction model.
- Keep the existing standalone HTML prototype as a temporary sound-design testbench, clearly marked as such.
- No FM1-compatible package has been built or tested yet.

Next technical steps:
1. Select a proven FM1 firmware base with correct audio, display, input, MIDI, storage, build, and loader integration; audit licenses.
2. Port and validate PadVoice.hpp in that base with host DSP tests.
3. Compile a minimal FM1 firmware image, run it in an emulator, then add pad controls and the other voices.
4. Keep BLE SMC budget and fail-safe startup throughout; do not flash the user's hardware until image/recovery validation.
