# GrooveScape

GrooveScape is an in-development M-VAVE FM1 groovebox project, combining ToneScape-style evolving ambient pads with independent bass, lead and drum tracks.

## Status
- **GrooveScape Studio:** early four-track browser sequencer prototype in [index.html](index.html).
- **FM1 firmware:** native FM1 host build and DSP regression tests pass in CI; physical-device firmware has not been validated or approved for flashing.
- **Bluetooth SMC Mixer:** planned, drawing on Hortator's documented DAW-mode implementation; not yet integrated.
- **Web flasher:** not enabled until a validated firmware image and recovery path are available.

## Intended features
- Ambient pad engine; bass synth and sequencer; lead synth with chords, arp and latch; drum machine with patterns and fills.
- Shared tempo, scales, quantisation and transport.
- Online demo, preset companion and verified USB web flasher.
- SMC Mixer integration and consistent hardware/browser controls.

## Native FM1 emulator (build-gated)

The [native host and browser workflow](https://github.com/alfonsogordon/GrooveScape/actions/workflows/native-host.yml) compiles the real fm1-base application, runs audio/UI checks and publishes the browser output to [`/native/`](https://alfonsogordon.github.io/GrooveScape/native/) **only after all tests pass**. The link may be unavailable until the first passing build and GitHub Pages deployment. The current native application includes **four basic audio tracks (ToneScape pad, bass, lead and drums)**, live drum triggers and quantized drum A/B transport, but many menu pages, presets and browser/hardware interactions remain incomplete. Host compilation is not hardware validation. Bluetooth is deliberately disabled, and no hardware firmware is approved for flashing.

## Sound parity and real-time performance

The ToneScape-inspired pad uses 16 named environments, stereo four-voice textures, slow envelopes, pitch glide and diffusion wash. Its current implementation is a **port/approximation**, not a proven sample-identical reproduction of the original Android ToneScape engine. Original-vs-GrooveScape audio captures at matched pitch, environment, intensity, attack/release and output level are still required for a meaningful listening and spectral comparison.

The host CI now benchmarks eight simultaneous pad instances, four-pad configurations, and selectable two-, three-, and four-texture-voice settings. Each `gs_pad` occupies **35,792 bytes** on the host: eight instances require **286,336 bytes (~280 KiB)** and four require **143,168 bytes (~140 KiB)**, excluding bass, drums, lead, firmware, stack, and Bluetooth. In run 42504359202, four pads with three texture voices took **3.917 ms per 256-frame block**, while eight pads with four texture voices took **10.605 ms**; the 44.1 kHz block deadline is **5.805 ms**. CI host timings vary between runs, and no full-mix/embedded benchmark or free-memory measurement has been completed. Bluetooth support remains unimplemented and is not yet proven to fit.\n\nThe earlier eight-pad test is retained as a stress diagnostic.
