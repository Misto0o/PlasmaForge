// src/utils/helpPanel.js
//
// Wires the "?" button (top-right, see index.html) to a simple toggled
// text panel explaining what PlasmaForge is, for a first-time visitor
// who has no context. Kept intentionally simple — plain text, no
// markdown rendering, no external content fetch — since this copy
// changes rarely and doesn't need machinery around it.

const HELP_TEXT = `⚡ What is this?

This is a plasma globe — like the glass lightning balls you've probably seen before — except it's real, running physics, not a video or animation.

Every arc of lightning is calculated using the same math that describes how real electric charges push and pull on each other. That's why no two moments ever look exactly the same, and why the lightning spreads itself out instead of overlapping — it's actually reacting to itself.

How to play with it:
• Drag anywhere to rotate the globe
• Scroll to zoom in and out
• Click and hold on the glass — the lightning will bend toward your cursor, just like touching a real plasma ball

That's it. Have fun.`;

export function setupHelpPanel() {
    const button = document.getElementById("help-button");
    const panel = document.getElementById("help-panel");
    if (!button || !panel) return; // markup not present — nothing to wire up

    panel.textContent = HELP_TEXT;

    button.addEventListener("click", (event) => {
        event.stopPropagation(); // don't let this click also register as a globe touch
        panel.classList.toggle("visible");
    });

    // Clicking anywhere outside the panel closes it — standard popover
    // behavior, and stops it from just sitting open indefinitely.
    document.addEventListener("click", (event) => {
        if (!panel.classList.contains("visible")) return;
        if (panel.contains(event.target) || event.target === button) return;
        panel.classList.remove("visible");
    });
}