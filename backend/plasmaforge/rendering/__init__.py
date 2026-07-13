"""
Rendering package (server-side).

Important: the actual 3D rendering happens client-side in Three.js
(frontend/src/scene/). This package is NOT a renderer — it's for
server-side concerns that are rendering-*adjacent*: preparing/optimizing
the data the frontend needs to render (e.g. decimating filament point
counts for bandwidth, or, later, generating video/frame exports for
recording a session offline). Named `rendering/` rather than
`export/` because "preparing visual data" is the more durable framing
as this package grows.
"""
