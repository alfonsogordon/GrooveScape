# GrooveScape FM1: Bluetooth-first architecture

Status: design constraints only; no FM1 firmware built or measured.

## Non-negotiable channels
1. PAD: ToneScape-derived evolving ambient sound.
2. BASS: selectable bass engines, scale-aware sequencer.
3. LEAD: polyphonic lead, chord mode, arpeggiator, latch.
4. DRUMS: independent sequencer, A/B patterns, fills and breaks.

All share one tempo/transport, quantized event scheduler, scale/chord context, and master output. Keep mixer and pattern state independent from audio synthesis so the browser companion can use the same parameter model.

## Bluetooth reserve (must be measured, not guessed)
- **Flash:** leave space for BLE host stack, controller/radio support, bonding/configuration and SMC mappings. Do not commit to a flash partition or numerical budget before confirming the FM1 memory map, actual linker map, and Bluetooth-enabled baseline.
- **RAM:** reserve BLE connection buffers, MIDI queues, stack/heap, and safety margin. Avoid dynamic allocation in the audio callback.
- **CPU:** benchmark worst-case four-channel playback with BLE scanning, connecting, connected idle, and high-rate mixer activity. Reject underruns and audio glitches.
- **Firmware variants:** initially build a safe non-BLE test image and a BLE-enabled image from the same source. Feature flags must not silently change sound engine behavior.
- **Startup:** BLE OFF by default. Never auto-start BLE after a previous BLE crash until recovery is confirmed.
- **No connection dependency:** audio, transport and saved projects must work without a mixer.
- **Overflow:** bounded MIDI/event queues; drop excess control events safely, never block the audio thread.
- **Persistence:** versioned settings with recovery to defaults if Bluetooth settings are invalid.

## SMC Mixer protocol reference
Hortator's GPL-3.0-only `firmware/src/smc.c` and Bluetooth manual document a working M-VAVE SMC-Mixer implementation:
- Mixer in DAW/Mackie Control mode.
- FM1 as BLE HOST, with SMC DAW mode or matching name prefix.
- Faders: MIDI pitch bend channels 1–8, soft takeover/pickup.
- Encoders: channel 1 CC16–23, relative sign-magnitude.
- Buttons: MIDI notes for REC/SOLO/MUTE/SELECT and transport.
- LED feedback: outgoing MIDI note state and fader position feedback.

This is a **reference**, not an integrated implementation. Any reuse must preserve compatible GPL licensing and attribution. We must inspect hardware/radio integration and reproduce the actual connection lifecycle rather than copying only the mixer MIDI parser.

## Proposed eight mixer strips
1 PAD master; 2 BASS; 3 LEAD; 4 DRUM master; 5 KICK; 6 SNARE; 7 HATS/PERC; 8 FX RETURN.
This is a provisional mapping to be tested with the real mixer; all eight strips have independent levels and mute/solo state.

## Required gates before flashing
1. Confirm FM1 hardware/bootloader, linker map, firmware container and recovery path.
2. Compile reproducibly with build logs, memory utilization and artifact checksums.
3. Test browser controls and protocol parser using recorded/constructed MIDI messages.
4. Verify no audio buffer overruns, BLE disabled/enabled, and repeated pairing/reconnect.
5. Validate on hardware using a reversible recovery procedure; no automatic flash.
6. Only then enable web flashing with explicit device and image verification.

## Browser companion
- Browser sequencer is currently a **prototype** with placeholder synthesis.
- Share parameter schema, preset schema and MIDI mapping definitions with firmware.
- Virtual mixer should function without BLE, and should not imply browser Bluetooth connection is working.
- Browser USB flashing remains disabled until a verified FM1 firmware artifact exists.

References:
- https://github.com/DeadActive/hortator/blob/main/docs/manual/12-bluetooth.md
- https://github.com/DeadActive/hortator/blob/main/firmware/src/smc.c
- https://github.com/alfonsogordon/sloop-BT
