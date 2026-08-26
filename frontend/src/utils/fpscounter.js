// src/utils/fpsCounter.js
//
// Lightweight FPS counter, no dependencies. Deliberately NOT using
// instantaneous 1/dt (which jitters wildly frame to frame) — instead
// keeps a rolling average over the last SAMPLE_WINDOW frames and only
// updates the displayed number a few times a second, so it's actually
// readable instead of flickering digits.

const SAMPLE_WINDOW = 30;
const DISPLAY_UPDATE_INTERVAL_S = 0.25;

export class FPSCounter {
  constructor(domElement) {
    this.domElement = domElement;
    this._samples = [];
    this._timeSinceDisplayUpdate = 0;
  }

  /** Call once per frame with the frame's delta time in seconds. */
  update(dt) {
    if (dt <= 0) return;
    this._samples.push(1 / dt);
    if (this._samples.length > SAMPLE_WINDOW) this._samples.shift();

    this._timeSinceDisplayUpdate += dt;
    if (this._timeSinceDisplayUpdate < DISPLAY_UPDATE_INTERVAL_S) return;
    this._timeSinceDisplayUpdate = 0;

    const avg = this._samples.reduce((a, b) => a + b, 0) / this._samples.length;
    if (this.domElement) {
      this.domElement.textContent = `${Math.round(avg)} FPS`;
    }
  }
}
