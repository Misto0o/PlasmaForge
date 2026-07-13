// src/scene/SceneManager.js
//
// Owns the Three.js renderer, camera, and scene lifecycle (resize
// handling, animation loop). Deliberately does NOT know anything about
// plasma-specific visuals — that's PlasmaGlobe's job. SceneManager is
// the reusable "here's a resizable 3D canvas with a camera" boilerplate,
// kept separate so it could host a different visual object without
// modification if the project ever needed that.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CAMERA } from "../config/constants.js";
import { setupLighting } from "./lighting.js";

export class SceneManager {
  constructor(container) {
    this.container = container;

    this.scene = new THREE.Scene();
    // Background is left null (not a solid THREE.Color) so the page's
    // CSS radial-gradient vignette (see index.html) shows through the
    // canvas instead of being painted over by a flat fill — requires
    // the renderer's alpha:true below to actually be transparent.

    this.camera = new THREE.PerspectiveCamera(
      CAMERA.fov,
      container.clientWidth / container.clientHeight,
      CAMERA.near,
      CAMERA.far
    );
    this.camera.position.set(0, 0, CAMERA.initialDistance);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(this.renderer.domElement);

    setupLighting(this.scene);

    // Mouse/touch drag-to-orbit + scroll-to-zoom. Without this, the
    // scene renders but is completely static from the user's
    // perspective — this is what makes the globe feel like an object
    // you can pick up and turn, rather than a video playing.
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 1.6;
    this.controls.maxDistance = 8;
    this.controls.enablePan = false; // panning a single centered object adds confusion, not value

    this._resizeHandler = this._onResize.bind(this);
    window.addEventListener("resize", this._resizeHandler);

    this._clock = new THREE.Clock();
    this._updateCallbacks = [];
  }

  /** Registers a per-frame update callback of the form (dt) => void.
   * PlasmaGlobe.update is registered this way from main.js, keeping
   * SceneManager ignorant of what it's animating. */
  onUpdate(callback) {
    this._updateCallbacks.push(callback);
  }

  add(object3D) {
    this.scene.add(object3D);
  }

  start() {
    this.renderer.setAnimationLoop(() => {
      const dt = this._clock.getDelta();
      this.controls.update(); // required every frame when damping is enabled
      for (const cb of this._updateCallbacks) cb(dt);
      this.renderer.render(this.scene, this.camera);
    });
  }

  _onResize() {
    const { clientWidth, clientHeight } = this.container;
    this.camera.aspect = clientWidth / clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(clientWidth, clientHeight);
  }

  dispose() {
    window.removeEventListener("resize", this._resizeHandler);
    this.renderer.setAnimationLoop(null);
    this.renderer.dispose();
  }
}