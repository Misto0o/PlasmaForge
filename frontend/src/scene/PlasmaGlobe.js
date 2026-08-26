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
    this.midOffset = new THREE.Vector3(
      (Math.random() - 0.5) * 0.25,
      (Math.random() - 0.5) * 0.25,
      (Math.random() - 0.5) * 0.25
    );
  }

  get intensity() {
    const t = this.age / this.lifetime;
    if (t < 0.15) return t / 0.15;
    if (t > 0.8) return Math.max(0, 1 - (t - 0.8) / 0.2);
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

/**
 * Generates a small radial-gradient circle texture at runtime (no image
 * asset needed) for use as a soft particle sprite. Flat square dots read
 * as "debug visualization"; a soft glowing dot reads as "plasma motes" —
 * this is one of the cheapest visual upgrades available in Three.js.
 */
function createSoftCircleTexture() {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(
    size / 2, size / 2, 0,
    size / 2, size / 2, size / 2
  );
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.4, "rgba(255,255,255,0.6)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

/**
 * A dark radial-gradient texture (opposite of createSoftCircleTexture) —
 * used for the ground shadow ellipse beneath the globe.
 */
function createSoftShadowTexture() {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(
    size / 2, size / 2, 0,
    size / 2, size / 2, size / 2
  );
  gradient.addColorStop(0, "rgba(0,0,0,1)");
  gradient.addColorStop(0.6, "rgba(0,0,0,0.4)");
  gradient.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

export class PlasmaGlobe {
  constructor() {
    this.group = new THREE.Group();

    this._particleTexture = createSoftCircleTexture();

    this._buildGlassShell();
    this._buildRimGlow();
    this._buildGroundShadow();
    this._buildElectrode();
    this._buildElectrodeLight();
    this._buildFilaments();

    this._latestSimState = null;
  }

  /**
   * A soft dark ellipse beneath the globe, like a drop shadow on a
   * surface. This is a classic cheap trick for selling "this is a 3D
   * object floating in space" — without SOMETHING anchoring it
   * relative to an implied ground/surface, a sphere reads as a flat
   * circle far more easily than people expect, especially at a glance
   * before the eye has parsed the lighting.
   */
  _buildGroundShadow() {
    const geometry = new THREE.PlaneGeometry(GLOBE_RADIUS * 3.2, GLOBE_RADIUS * 3.2);
    const material = new THREE.MeshBasicMaterial({
      map: this._shadowTexture || (this._shadowTexture = createSoftShadowTexture()),
      transparent: true,
      opacity: 0.55,
      depthWrite: false,
      blending: THREE.NormalBlending, // darkens, unlike the additive glow elements
    });
    this.groundShadow = new THREE.Mesh(geometry, material);
    this.groundShadow.rotation.x = -Math.PI / 2; // lay flat, like a floor
    this.groundShadow.position.y = -GLOBE_RADIUS * 1.4;
    this.groundShadow.renderOrder = -1; // draw before everything else, it's furthest "back" conceptually
    this.group.add(this.groundShadow);
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

  /**
   * A slightly larger, very faint additive sphere just outside the main
   * glass shell — fakes a Fresnel-style rim glow (the edges of real
   * glass catch and scatter more light than the center) without the
   * complexity of a custom shader. Cheap, but reads as "this glass is
   * energized" rather than "this is a plain transparent sphere."
   */
  _buildRimGlow() {
    const geometry = new THREE.SphereGeometry(GLOBE_RADIUS * 1.03, 48, 48);
    const material = new THREE.MeshBasicMaterial({
      color: COLORS.globeGlass,
      transparent: true,
      opacity: 0.03,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.BackSide, // only visible at glancing angles, like a rim light
    });
    this.rimGlow = new THREE.Mesh(geometry, material);
    this.rimGlow.renderOrder = 11;
    this.group.add(this.rimGlow);
  }

  _buildElectrode() {
    const geometry = new THREE.SphereGeometry(ELECTRODE_RADIUS, 32, 32);
    // Emissive intensity kept LOW on purpose this time — a strong
    // emissive value is a constant color added regardless of surface
    // angle, which was actively fighting the whole point of switching
    // off MeshBasicMaterial: it was washing the angle-dependent
    // light/shadow gradient back out, landing right back at "looks
    // flat." Lower roughness + a touch of metalness instead produces a
    // tighter, brighter specular highlight, which reads as "this is a
    // 3D ball" far more obviously than a subtle diffuse gradient does
    // at this small a size on screen.
    const material = new THREE.MeshStandardMaterial({
      color: COLORS.electrode,
      emissive: new THREE.Color(COLORS.electrode),
      emissiveIntensity: 0.3,
      roughness: 0.15,
      metalness: 0.3,
    });
    this.electrode = new THREE.Mesh(geometry, material);
    this.group.add(this.electrode);

    const glowGeometry = new THREE.SphereGeometry(ELECTRODE_RADIUS * 1.6, 24, 24);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: COLORS.electrode,
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.electrodeGlow = new THREE.Mesh(glowGeometry, glowMaterial);
    this.group.add(this.electrodeGlow);
  }

  /**
   * A real THREE.PointLight at the electrode's position. Previously the
   * electrode only *looked* bright (MeshBasicMaterial ignores scene
   * lighting entirely) but never actually illuminated the glass around
   * it — the glass's specular highlights only ever came from the two
   * fixed directional lights in lighting.js. A point light here makes
   * the glass genuinely brighter near the electrode and dimmer at the
   * far side, which is what actually sells "there's a glowing thing
   * inside this glass" instead of "there's a sphere with lines on it."
   */
  _buildElectrodeLight() {
    // Intensity/decay tuned down from an earlier pass that was too
    // strong and washed out the glass — this should read as "a subtle
    // glow source," not "a flashlight inside the globe."
    this.electrodeLight = new THREE.PointLight(0xbb99ff, 0.2, GLOBE_RADIUS * 2.5, 1.5);
    this.electrodeLight.position.set(0, 0, 0);
    this.group.add(this.electrodeLight);
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

    // Glowing tip sprites: one soft circular sprite per filament, placed
    // at the current endpoint. This is what makes each arc look like it
    // has an actual spark landing on the glass, rather than just a line
    // that stops.
    this.filamentTipSprites = this.filaments.map(() => {
      const material = new THREE.SpriteMaterial({
        map: this._particleTexture,
        color: COLORS.filamentCore,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const sprite = new THREE.Sprite(material);
      sprite.scale.set(0.03, 0.03, 0.03);
      this.group.add(sprite);
      return sprite;
    });
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
   * Backend filaments now arrive as { main: [[x,y,z], ...], branches:
   * [[x,y,z], [x,y,z], ...] } — an ORDERED chain for the main path, and
   * flat start/end pairs for branch sparks (see SimulationState.to_dict()
   * and Filament.main_path_points/branch_segment_pairs on the Python
   * side).
   *
   * The main path is rendered as STRAIGHT segments directly through the
   * backend's jittered points — no spline smoothing. An earlier version
   * ran these through THREE.CatmullRomCurve3 to fix a "crunchy" look,
   * but that was the wrong instinct for lightning specifically: a spline
   * rounds off every sharp corner by design, which is exactly backwards
   * from what makes something read as electricity. Real lightning
   * renders (games, film) use straight jagged segments through
   * midpoint-displaced points — splines are for smooth magic/energy
   * trails, not bolts. Cranking backend jitter/segment constants can't
   * fix jaggedness while this smoothing step is still in the pipeline;
   * removing it is the actual fix, not a bigger jitter value.
   */
  _renderFilamentsFromState(filaments) {
    for (const line of this.filamentLines) {
      this.group.remove(line);
      line.geometry.dispose();
      line.material.dispose();
    }
    this.filamentLines = [];

    for (const sprite of this.filamentTipSprites || []) {
      this.group.remove(sprite);
    }
    this.filamentTipSprites = [];

    for (const filament of filaments) {
      const mainPoints = (filament.main || []).map(([x, y, z]) => new THREE.Vector3(x, y, z));
      const branchPoints = (filament.branches || []).map(([x, y, z]) => new THREE.Vector3(x, y, z));

      if (mainPoints.length >= 2) {
        const sampled = mainPoints; // straight segments through the raw points, no smoothing

        // Slight per-rebuild opacity flicker adds a subtle crackle —
        // filaments are rebuilt many times a second anyway, so this is
        // nearly free.
        const flicker = 0.8 + Math.random() * 0.2;

        // Length-based brightness fade: brighter near the electrode
        // (root), dimming toward the glass (tip) — matches how real
        // plasma streamers actually look, with glow concentrated near
        // the source rather than uniform along the whole arc. Done via
        // per-vertex colors rather than a shader: `vertexColors: true`
        // plus a plain white material color lets each point's color
        // carry both the hue AND the fade together, computed once here
        // rather than needing custom material code.
        const baseColor = new THREE.Color(COLORS.filament);
        const fadeColors = [];
        for (let i = 0; i < sampled.length; i++) {
          const t = sampled.length > 1 ? i / (sampled.length - 1) : 0;
          const brightness = 1.0 - t * 0.65; // never fades fully to black, just dims
          fadeColors.push(baseColor.r * brightness, baseColor.g * brightness, baseColor.b * brightness);
        }

        const coreGeometry = new THREE.BufferGeometry().setFromPoints(sampled);
        coreGeometry.setAttribute("color", new THREE.Float32BufferAttribute(fadeColors, 3));
        const coreMaterial = new THREE.LineBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 1.0 * flicker,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const coreLine = new THREE.Line(coreGeometry, coreMaterial);
        this.filamentLines.push(coreLine);
        this.group.add(coreLine);

        // Tip sprites shrunk significantly — at high filament counts
        // (e.g. 85), each one is a soft glowing blob, and 85 of them
        // was most of what was visually flooding the globe, not the
        // ambient dust particles as it might look at a glance.
        const tip = mainPoints[mainPoints.length - 1];
        const spriteMaterial = new THREE.SpriteMaterial({
          map: this._particleTexture,
          color: COLORS.filamentCore,
          transparent: true,
          opacity: 0.7,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.position.copy(tip);
        sprite.scale.set(0.022, 0.022, 0.022);
        this.filamentTipSprites.push(sprite);
        this.group.add(sprite);
      }

      if (branchPoints.length >= 2) {
        const branchGeometry = new THREE.BufferGeometry().setFromPoints(branchPoints);
        const branchMaterial = new THREE.LineBasicMaterial({
          color: COLORS.filament,
          transparent: true,
          opacity: 0.6, // branches read as secondary/subtler than the main arc
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const branchLine = new THREE.LineSegments(branchGeometry, branchMaterial);
        this.filamentLines.push(branchLine);
        this.group.add(branchLine);
      }
    }
  }

  /**
   * Renders backend particles as a single THREE.Points cloud using a
   * soft circular sprite texture (see createSoftCircleTexture) instead
   * of the default hard-edged square GL point — this is the single
   * biggest visual upgrade for "does this look like plasma dust or a
   * debug overlay."
   */
  _renderParticlesFromState(particlePositions) {
    if (!this.particlePoints) {
      const geometry = new THREE.BufferGeometry();
      const material = new THREE.PointsMaterial({
        color: COLORS.filamentCore,
        size: 0.015, // was 0.035 — noticeably smaller, cleaner "dust" instead of small moons
        map: this._particleTexture,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        sizeAttenuation: true,
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
      this._updatePlaceholderFilaments(dt);
    }
    this.group.rotation.y += dt * 0.05;
  }

  _updatePlaceholderFilaments(dt) {
    this.filaments.forEach((filament, i) => {
      filament.step(dt);
      const points = filament.getCurvePoints();
      const line = this.filamentLines[i];
      line.geometry.setFromPoints(points);
      line.material.opacity = filament.intensity;

      const tip = points[points.length - 1];
      const sprite = this.filamentTipSprites[i];
      if (sprite) {
        sprite.position.copy(tip);
        sprite.material.opacity = 0.9 * filament.intensity;
      }
    });
  }
}