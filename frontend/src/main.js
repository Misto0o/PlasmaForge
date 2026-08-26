import * as THREE from "three";
import { SceneManager } from "./scene/SceneManager.js";
import { PlasmaGlobe } from "./scene/PlasmaGlobe.js";
import { SimulationClient } from "./network/SimulationClient.js";
import { FPSCounter } from "./utils/fpscounter.js";
import { setupHelpPanel } from "./utils/helpPanel.js";

const container = document.getElementById("app");
const sceneManager = new SceneManager(container);

const globe = new PlasmaGlobe();
sceneManager.add(globe.group);
sceneManager.onUpdate((dt) => globe.update(dt));

const fpsCounter = new FPSCounter(document.getElementById("fps-counter"));
sceneManager.onUpdate((dt) => fpsCounter.update(dt));

setupHelpPanel();

sceneManager.start();

const client = new SimulationClient({
  onState: (state) => globe.applySimulationState(state),
  onConnect: () => console.log("[PlasmaForge] connected to simulation server"),
  onDisconnect: () => console.log("[PlasmaForge] disconnected, reconnecting..."),
});
client.connect();

const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let isPointerDown = false;

function updatePointerNDC(event) {
  const rect = sceneManager.renderer.domElement.getBoundingClientRect();
  pointerNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointerNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

function sendTouchFromPointer(event) {
  updatePointerNDC(event);
  raycaster.setFromCamera(pointerNDC, sceneManager.camera);
  const hits = raycaster.intersectObject(globe.glassShell, false);
  if (hits.length === 0) {
    sceneManager.controls.enabled = true;
    return;
  }
  sceneManager.controls.enabled = false;
  const localPoint = globe.group.worldToLocal(hits[0].point.clone());
  client.send({ type: "set_touch", position: [localPoint.x, localPoint.y, localPoint.z] });
}

const canvas = sceneManager.renderer.domElement;
canvas.addEventListener("pointerdown", (event) => {
  isPointerDown = true;
  sendTouchFromPointer(event);
});
window.addEventListener("pointermove", (event) => {
  if (!isPointerDown) return;
  sendTouchFromPointer(event);
});
window.addEventListener("pointerup", () => {
  if (!isPointerDown) return;
  isPointerDown = false;
  sceneManager.controls.enabled = true;
  client.send({ type: "clear_touch" });
});