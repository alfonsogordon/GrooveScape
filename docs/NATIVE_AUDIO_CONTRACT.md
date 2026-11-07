# Native integration notes — confirmed platform contract

Upstream: https://github.com/charlesvestal/fm1-base (MPL-2.0).
Source inspected: `template/app.c`, `template/app.h`, `template/README.md`, `template/fm1.toml`.

## Confirmed FM1 audio interface
```c
void app_render(int32_t *lr, uint32_t n, uint32_t master_q12);
```
- Interleaved stereo output, signed 24-bit range in `int32_t`.
- Sample rate **44,100 Hz**, not 48,000.
- App block default **256 frames**.
- Called in audio interrupt. Avoid allocation, blocking, locks, filesystem and Bluetooth calls here.
- `app_panic` must silence voices immediately.
- `app_init`, `app_ui_init`, `app_frame`, `app_input_only` implement lifecycle/UI.

## Porting gap
Current `firmware/audio/PadVoice.hpp` is C++ and uses `std::array`, `std::clamp`, `std::pow` and `std::tanh`; upstream's firmware app is compiled in a C unity build. **It cannot be included directly in `template/app.c`.** Choose either a freestanding C DSP implementation with a C API or add a separately compiled C++ unit and C ABI wrapper to the build. Avoid blindly mixing languages.

The pad's sample rate has been corrected to 44,100. It is not yet FM1-compiled, benchmarked or connected to `app_render`.

## Baseline build
`scripts/bootstrap_fm1_base.sh` clones upstream with submodules and invokes host/web baseline builds. This script has **not** run successfully in the assistant environment (network DNS unavailable); do not infer a working browser bundle from its presence.

## Priorities
1. Get upstream host/web baseline building in CI or a network-enabled machine.
2. Add a minimal C audio renderer with block-based note and master handling.
3. Measure FM1 CPU/RAM/flash budget before enabling 4-track DSP.
4. Move one environment and Jarreth control to the shared app, verify emulator input/audio.
5. Add BLE central SMC MIDI behind an off-by-default switch and resource tests.

No user hardware flashing until the built package and recovery route are verified.
