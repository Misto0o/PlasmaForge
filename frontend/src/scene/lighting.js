// src/scene/lighting.js
//
// Split out from SceneManager.js because lighting for a glass/glow effect
// like a plasma globe tends to need iteration independent of camera/scene
// wiring — keeping it isolated means it can be tuned without touching
// scene setup code.

import * as THREE from "three";
import { COLORS } from "../config/constants.js";

export function setupLighting(scene) {
  // Restored back up — these were dimmed in an earlier pass on the
  // assumption an environment map would supply extra fill light, but
  // that environment map was later removed entirely (it caused a
  // different problem, blotchy blue reflections). Left dim afterward,
  // this scene had no meaningful light on it at all, which is why the
  // glass wasn't showing any shading/gradient — there was nothing to
  // shade it with.
  const ambient = new THREE.AmbientLight(COLORS.ambientLight, 0.5);
  scene.add(ambient);

  // A cool rim light from above-behind, to catch the edge of the glass
  // sphere without washing out the plasma glow inside it.
  const rim = new THREE.DirectionalLight(0x6688ff, 0.75);
  rim.position.set(-2, 3, -2);
  scene.add(rim);

  // A warm fill from the front so the glass surface reads as glass
  // rather than a flat silhouette.
  const fill = new THREE.DirectionalLight(0xffddaa, 0.35);
  fill.position.set(2, 1, 3);
  scene.add(fill);

  return { ambient, rim, fill };
}