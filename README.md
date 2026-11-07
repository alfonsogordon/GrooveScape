# GrooveScape

GrooveScape is an in-development M-VAVE FM1 groovebox project, combining ToneScape-style evolving ambient pads with independent bass, lead and drum tracks.

## Status
- **GrooveScape Studio:** early four-track browser sequencer prototype in [index.html](index.html).
- **FM1 firmware:** not yet built or verified.
- **Bluetooth SMC Mixer:** planned, drawing on Hortator's documented DAW-mode implementation; not yet integrated.
- **Web flasher:** not enabled until a validated firmware image and recovery path are available.

## Intended features
- Ambient pad engine; bass synth and sequencer; lead synth with chords, arp and latch; drum machine with patterns and fills.
- Shared tempo, scales, quantisation and transport.
- Online demo, preset companion and verified USB web flasher.
- SMC Mixer integration and consistent hardware/browser controls.

## Native FM1 emulator (build-gated)

The [native host and browser workflow](https://github.com/alfonsogordon/GrooveScape/actions/workflows/native-host.yml) compiles the real fm1-base application, runs audio/UI checks and publishes the browser output to [`/native/`](https://alfonsogordon.github.io/GrooveScape/native/) **only after all tests pass**. The link may be unavailable until the first passing build and GitHub Pages deployment. The current native application is a **single-pad integration prototype**, not the completed four-track groovebox. Bluetooth is deliberately disabled, and no hardware firmware is approved for flashing.

## Run the browser prototype
Open `index.html` in a modern browser or enable GitHub Pages with **Settings → Pages → Deploy from a branch → main → / (root)**. The prototype uses basic browser-generated sounds, **not** the actual ToneScape engine. It cannot flash the FM1.

## Sources and licensing
Potential references include [ToneScape](https://github.com/alfonsogordon/ToneScape), [SLOOP-BT](https://github.com/alfonsogordon/sloop-BT) and [Hortator](https://github.com/DeadActive/hortator). Hortator's SMC implementation is GPL-3.0-only; code reuse requires license compliance. No third-party firmware source has yet been copied into this repository.

**Do not flash any experimental firmware to hardware until verified.**
