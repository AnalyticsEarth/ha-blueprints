# Changelog

## 2026-11-08 (Philips Hue)

### Added

- **Philips Hue dimmer switch RWL020 / RWL021 (Hue Bridge)**: On (with Hue
  app-style scene cycling), Up / Down tap and hold dimming, Off, On hold for
  full brightness, per-gesture scene and custom action overrides, mirroring
  across switches. Responds on press by default to avoid the bridge's ~1 s
  event batching, and uses queued mode so bunched taps all run. Tested
  against a capture from a real RWL021.

## 2026-11-08 (real-device testing)

### Fixed

- All remote blueprints: the first press on a button that had never been used
  (entity state `unknown`) was ignored. Only `unavailable` is filtered now.

### Changed

- BILRESA scroll wheel: *Brightness per notch* default raised from 5 % to
  10 %. Real hardware sends one event per notch on slow turns and drops fast
  spins of more than 8 notches.
- Docs: added recorded event sequences for STYRBAR ("Remote Control N2"), the
  scroll wheel entity labels, and RODRET support in the dual button blueprint.
- Tests: replay real event captures (`tests/test_real_capture.py`).

## 2026-11-08

### Added

- **IKEA BILRESA dual button (Matter)**: on/off, hold to dim, double press for
  scene cycle or full/minimum brightness, per-gesture scene and custom action
  overrides, mirroring across multiple remotes.
- **IKEA BILRESA scroll wheel (Matter)**: one automation per channel; rotation
  controls brightness, colour temperature or a scene cycle, scaled by notches;
  press toggles, double press goes to full brightness; triple press and hold
  available for scenes and custom actions.
- **IKEA STYRBAR remote (Matter via DIRIGERA)**: up/down on/off and hold to
  dim, left/right scene cycle or colour temperature, duplicate-event debounce.
