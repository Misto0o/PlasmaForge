// src/scene/PlasmaGlobe.js
//
// The visual heart of the project: a glass sphere containing a glowing
// central electrode and animated plasma filaments arcing out to the
// glass surface.
//
// Two data sources drive this, chosen automatically:
//   1. Placeholder mode (default): a local procedural animation, active
//      whenever no SimulationState has arrived yet — keeps the globe
//      demoable with zero backend running.
//   2. Live mode: once applySimulationState() is called (see
//      SimulationClient in main.js), filament/particle geometry is
//      rebuilt from real backend data every frame instead.

import * as THREE from "three";
import { COLORS, ELECTRODE_RADIUS, GLOBE_RADIUS } from "../config/constants.js";
import { randomPointOnSphere } from "../utils/mathUtils.js";

const FILAMENT_COUNT = 6;
const FILAMENT_SEGMENTS = 24; // points per filament curve, for a smooth arc
const FILAMENT_MIN_LIFETIME = 0.4;
const FILAMENT_MAX_LIFETIME = 1.1;

class Filament {
  constructor() {
    this.age = 0;
    this.lifetime = 0;
    this._respawn();
  }

  _respawn() {
    this.age = 0;
    this.lifetime =
      FILAMENT_MIN_LIFETIME + Math.random() * (FILAMENT_MAX_LIFETIME - FILAMENT_MIN_LIFETIME);
    this.target = randomPointOnSphere(GLOBE_RADIUS * 0.95);
    // A mild random midpoint offset gives the arc a organic bow/branch
    // shape instead of a perfectly straight line from center to surface.
    this.midOffset = new THREE.Vector3(
      (Math.random() - 0.5) * 0.25,
      (Math.random() - 0.5) * 0.25,
      (Math.random() - 0.5) * 0.25
    );
  }

  /** Returns 0..1 opacity based on lifecycle position — fades in, holds,
   * flickers out. This is what gives the globe its restless look. */
  get intensity() {
    const t = this.age / this.lifetime;
    if (t < 0.15) return t / 0.15;
    if (t > 0.8) return Math.max(0, 1 - (t - 0.8) / 0.2);
    // Mid-life flicker: small random jitter around full brightness.
    return 0.85 + Math.random() * 0.15;
  }

  step(dt) {
    this.age += dt;
    if (this.age >= this.lifetime) this._respawn();
  }

  getCurvePoints() {
    const start = new THREE.Vector3(0, 0, 0);
    const end = new THREE.Vector3(this.target.x, this.target.y, this.target.z);
    const mid = start.clone().lerp(end, 0.5).add(this.midOffset);
    const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
    return curve.getPoints(FILAMENT_SEGMENTS);
  }
}

export class PlasmaGlobe {
  constructor() {
    this.group = new THREE.Group();

    this._buildGlassShell();
    this._buildElectrode();
    this._buildFilaments();

    // Real backend data target — populated by applySimulationState() once
    // the WebSocket client is wired up. Until then it stays null and the
    // globe runs on the procedural placeholder animation.
    this._latestSimState = null;
  }

  _buildGlassShell() {
    const geometry = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
    const material = new THREE.MeshPhysicalMaterial({
      color: COLORS.globeGlass,
      transparent: true,
      opacity: 0.35,
      roughness: 0.05,
      metalness: 0,
      transmission: 0.7,
      thickness: 0.4,
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      side: THREE.DoubleSide,
      // CRITICAL: without this, the glass — despite being visually
      // transparent — still writes to the depth buffer by default (a
      // common Three.js gotcha). Since this is one continuous sphere
      // mesh containing both its near and far faces, that depth write
      // makes the glass silently occlude everything drawn inside it
      // (filaments, particles), even though you can "see through" it.
      // This is why filaments were invisible — not a physics bug, a
      // rendering order bug.
      depthWrite: false,
    });
    this.glassShell = new THREE.Mesh(geometry, material);
    // Explicit render order (rather than relying on Three.js's automatic
    // distance-based transparent sort, which is unreliable for a single
    // sphere mesh containing both near/far faces): draw the glass LAST
    // among transparent objects, so it blends its tint over the plasma
    // content correctly instead of potentially drawing before it.
    this.glassShell.renderOrder = 10;
    this.group.add(this.glassShell);
  }

  _buildElectrode() {
    const geometry = new THREE.SphereGeometry(ELECTRODE_RADIUS, 32, 32);
    const material = new THREE.MeshBasicMaterial({ color: COLORS.electrode });
    this.electrode = new THREE.Mesh(geometry, material);
    this.group.add(this.electrode);

    // A soft glow halo around the electrode using an additive-blended
    // larger sphere — cheap substitute for real bloom post-processing,
    // which can be layered on later without removing this.
    const glowGeometry = new THREE.SphereGeometry(ELECTRODE_RADIUS * 2.2, 24, 24);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.electrode,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.electrodeGlow = new THREE.Mesh(glowGeometry, glowMaterial);
    this.group.add(this.electrodeGlow);
  }

  _buildFilaments() {
    this.filaments = [];
    this.filamentLines = [];

    for (let i = 0; i < FILAMENT_COUNT; i++) {
      const filament = new Filament();
      this.filaments.push(filament);

      const points = filament.getCurvePoints();
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: COLORS.filament,
        transparent: true,
        opacity: 1,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const line = new THREE.Line(geometry, material);
      this.filamentLines.push(line);
      this.group.add(line);
    }
  }

  /**
   * Feeds a real SimulationState snapshot (from SimulationClient) into
   * the globe. Called on every WebSocket message once connected — see
   * main.js. This replaces the procedural placeholder with the actual
   * filament/particle positions the backend engine computed.
   */
  applySimulationState(state) {
    this._latestSimState = state;
    this._renderFilamentsFromState(state.filaments || []);
    this._renderParticlesFromState(state.particles || []);
  }

  /**
   * Backend filaments arrive as a flat points array where every
   * consecutive pair [start, end, start, end, ...] is one independent
   * segment (see SimulationState.to_dict() on the Python side) — this
   * now includes branch segments that do NOT continue the main chain,
   * since filament.py generates jagged, occasionally-branching paths.
   * THREE.LineSegments (not THREE.Line/LineStrip) is the correct
   * primitive for that: it draws each consecutive pair as its own
   * disconnected segment instead of chaining every point together,
   * which would incorrectly connect branch tips back into the main path.
   */
  _renderFilamentsFromState(filaments) {
    for (const line of this.filamentLines) {
      this.group.remove(line);
      line.geometry.dispose();
      line.material.dispose();
    }
    this.filamentLines = [];

    for (const filament of filaments) {
      const points = filament.map(([x, y, z]) => new THREE.Vector3(x, y, z));
      if (points.length < 2) continue;
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const material = new THREE.LineBasicMaterial({
        color: COLORS.filament,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const line = new THREE.LineSegments(geometry, material);
      this.filamentLines.push(line);
      this.group.add(line);
    }
  }

  /**
   * Renders backend particles as a single THREE.Points cloud rather than
   * one Mesh per particle — at particle counts in the thousands (see
   * config.constants.DEFAULT_MAX_PARTICLES on the backend), individual
   * meshes would tank frame rate. A shared BufferAttribute updated in
   * place is the standard Three.js pattern for this.
   */
  _renderParticlesFromState(particlePositions) {
    if (!this.particlePoints) {
      const geometry = new THREE.BufferGeometry();
      const material = new THREE.PointsMaterial({
        color: COLORS.filamentCore,
        size: 0.015,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      this.particlePoints = new THREE.Points(geometry, material);
      this.group.add(this.particlePoints);
    }

    const flat = new Float32Array(particlePositions.length * 3);
    particlePositions.forEach(([x, y, z], i) => {
      flat[i * 3] = x;
      flat[i * 3 + 1] = y;
      flat[i * 3 + 2] = z;
    });
    this.particlePoints.geometry.setAttribute("position", new THREE.BufferAttribute(flat, 3));
  }

  update(dt) {
    if (!this._latestSimState) {
      // No backend data yet (or not connected) — keep the demo alive on
      // the procedural placeholder.
      this._updatePlaceholderFilaments(dt);
    }
    // Real filament/particle geometry is pushed in from applySimulationState()
    // whenever a WebSocket message arrives, not here — this just keeps the
    // globe visibly alive (rotating) regardless of data source.
    this.group.rotation.y += dt * 0.05;
  }

  _updatePlaceholderFilaments(dt) {
    this.filaments.forEach((filament, i) => {
      filament.step(dt);
      const points = filament.getCurvePoints();
      const line = this.filamentLines[i];
      line.geometry.setFromPoints(points);
      line.material.opacity = filament.intensity;
    });
  }
}