# FM1 foundation selected for evaluation

**Primary candidate:** https://github.com/charlesvestal/fm1-base (MPL-2.0)

Confirmed from upstream README, DESIGN.md and template/fm1.toml:
- Hardware firmware, native host simulator and browser emulator share the same application.
- Device APIs cover FM1 screen, panel/keys, LEDs, audio, storage and MIDI.
- `ble = true` and `ble_central = true` enable Bluetooth MIDI host capabilities.
- Upstream template includes firmware packaging and installer workflows.
- The platform is beta; API changes are expected.

## Next implementation sequence
1. Vendor/fork pinned fm1-base and required felucca-bsp submodule; retain licence notices.
2. Build untouched upstream template for native host and browser, then FM1 (without flashing).
3. Replace template's voice with GrooveScape's ToneScape-inspired DSP, validate CPU and RAM.
4. Build a 240x240 FM1 UI for pad/bass/lead/drums, with single-knob Jarreth control.
5. Enable BLE central only after audio performance and recovery checks; implement SMC protocol separately.
6. Test the same firmware in browser and only then publish a hardware test image.

**Not yet complete:** pinned source integration, compiler builds, browser emulator, FM1 package, Bluetooth validation. The current GitHub Pages demo remains a separate HTML prototype.

**Licensing:** fm1-base MPL-2.0. Do not import Hortator GPL-3.0-only or Freaq FM CC BY-NC-SA source without a separate distribution/licence review.
