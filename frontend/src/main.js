// src/main.js
//
// Application entrypoint. Wires SceneManager + PlasmaGlobe together,
// starts the render loop, and connects the "touch the glass" interaction
// (click/hold + drag on the glass sphere sends a raycast-derived point to
// the backend, which pulls filaments toward it — see
// backend/plasmaforge/simulation/modes/classic_mode.py's touch_target
// handling). This file stays composition/wiring only.

import * as THREE from "three";
import { SceneManager } from "./scene/SceneManager.js";
import { PlasmaGlobe } from "./scene/PlasmaGlobe.js";
import { SimulationClient } from "./network/SimulationClient.js";
import { FPSCounter } from "./utils/fpsCounter.js";

const container = document.getElementById("app");
const sceneManager = new SceneManager(container);

const globe = new PlasmaGlobe();
sceneManager.add(globe.group);
sceneManager.onUpdate((dt) => globe.update(dt));

const fpsCounter = new FPSCounter(document.getElementById("fps-counter"));
sceneManager.onUpdate((dt) => fpsCounter.update(dt));

sceneManager.start();

const client = new SimulationClient({
  onState: (state) => globe.applySimulationState(state),
  onConnect: () => console.log("[PlasmaForge] connected to simulation server"),
  onDisconnect: () => console.log("[PlasmaForge] disconnected, reconnecting..."),
});
client.connect();

// --- Touch-the-glass interaction -----------------------------------------
// Raycasts from the pointer through the camera against the glass shell.
// While the pointer is held down AND over the glass, we send the
// intersection point (converted into the globe's own local/unrotated
// coordinate space, since the group spins independently of the camera)
// to the backend as a "set_touch" control message every frame it moves.
// Releasing the pointer sends "clear_touch" so filaments go back to
// normal repulsion-based spawning.

const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let isPointerDown = false;
let isTouchingGlass = false; // decided once at pointerdown, not re-evaluated mid-drag

function updatePointerNDC(event) {
  const rect = sceneManager.renderer.domElement.getBoundingClientRect();
  pointerNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointerNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

function raycastGlass(event) {
  updatePointerNDC(event);
  raycaster.setFromCamera(pointerNDC, sceneManager.camera);
  const hits = raycaster.intersectObject(globe.glassShell, false);
  return hits.length > 0 ? hits[0] : null;
}

function sendTouchFromPointer(event) {
  // Once we're in touch mode, if the ray happens to slip off the sphere
  // mid-drag (e.g. dragging fast near the silhouette edge) we simply
  // skip that frame's update rather than dropping out of touch mode —
  // isTouchingGlass was already decided at pointerdown and doesn't
  // change until pointerup.
  const hit = raycastGlass(event);
  if (!hit) return;
  const localPoint = globe.group.worldToLocal(hit.point.clone());
  client.send({ type: "set_touch", position: [localPoint.x, localPoint.y, localPoint.z] });
}

const canvas = sceneManager.renderer.domElement;
canvas.addEventListener("pointerdown", (event) => {
  isPointerDown = true;
  const hit = raycastGlass(event);
  isTouchingGlass = hit !== null;

  if (isTouchingGlass) {
    // Decided once for the whole drag — this is what prevents the
    // "fighting" behavior where orbit and touch toggled back and forth
    // as the cursor wobbled near the sphere's edge mid-drag.
    sceneManager.controls.enabled = false;
    const localPoint = globe.group.worldToLocal(hit.point.clone());
    client.send({ type: "set_touch", position: [localPoint.x, localPoint.y, localPoint.z] });
  }
});
window.addEventListener("pointermove", (event) => {
  if (!isPointerDown || !isTouchingGlass) return;
  sendTouchFromPointer(event);
});
window.addEventListener("pointerup", () => {
  if (!isPointerDown) return;
  isPointerDown = false;
  if (isTouchingGlass) {
    isTouchingGlass = false;
    sceneManager.controls.enabled = true;
    client.send({ type: "clear_touch" });
  }
});