// src/scene/lighting.js
//
// Split out from SceneManager.js because lighting for a glass/glow effect
// like a plasma globe tends to need iteration independent of camera/scene
// wiring — keeping it isolated means it can be tuned without touching
// scene setup code.

import * as THREE from "three";
import { COLORS } from "../config/constants.js";

export function setupLighting(scene) {
  const ambient = new THREE.AmbientLight(COLORS.ambientLight, 0.6);
  scene.add(ambient);

  // A cool rim light from above-behind, to catch the edge of the glass
  // sphere without washing out the plasma glow inside it.
  const rim = new THREE.DirectionalLight(0x6688ff, 0.8);
  rim.position.set(-2, 3, -2);
  scene.add(rim);

  // A warm fill from the front so the glass surface reads as glass
  // rather than a flat silhouette.
  const fill = new THREE.DirectionalLight(0xffddaa, 0.3);
  fill.position.set(2, 1, 3);
  scene.add(fill);

  return { ambient, rim, fill };
}
