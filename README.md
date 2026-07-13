# ⚡ PlasmaForge

A real-time plasma globe simulation, in the browser, that you can actually
touch. Click and hold on the glass and lightning bends toward your cursor —
not a canned animation, but an actual electric field simulation (Coulomb's
law, computed in compiled Cython) driving jagged, branching arcs rendered
live in Three.js.

**Stack:** Python simulation backend, Cython for the performance-critical
math, WebSocket streaming to a Three.js/JavaScript frontend.

**What it actually does, concretely:**
- Simulates real electric fields — filaments repel each other via inverse-
  square field math, so they spread out across the globe on their own
  instead of clustering, because the physics says so, not because of a
  scripted rule
- Grows lightning as jagged, occasionally-branching multi-segment paths,
  not straight lines
- Reads your cursor position on the glass (raycasting) and feeds it back
  into the simulation as a live attractor, so arcs visibly bend toward you
  in real time
- Runs the hot-path math (field calculation, particle integration,
  filament placement) in four compiled Cython modules instead of pure
  Python, and it's fast — handles thousands of particles well under a
  millisecond per tick
- Streams simulation state to the browser over WebSocket at 60Hz,
  independent of the physics tick rate

Built by two people as a side project. If you're new here — hi, welcome,
here's the map.

## Finding your way around

This has a lot of folders for what looks like "just a plasma ball." Here's
the mental model:

```
plasmaforge/
├── backend/        Python. The brain. Computes physics, has zero
│   │                idea what a pixel is.
│   └── plasmaforge/
│       ├── config/       the dials — constants.py is 90% of where
│       │                 you'll actually make changes
│       ├── physics/      the math. electric_field, vector_math,
│       │                 filament_growth, and particle_integration are
│       │                 Cython (.pyx) — compiled to real machine code,
│       │                 which is why this stays fast even at 80+
│       │                 simultaneous filaments
│       ├── simulation/   turns raw physics into an actual running
│       │                 simulation over time — spawning filaments,
│       │                 moving particles, one tick at a time
│       ├── server/       the ONLY part that knows a browser exists —
│       │                 sends simulation state out over WebSocket,
│       │                 receives your clicks back
│       ├── interaction/  empty on purpose — reserved for future hand-
│       │                 tracking, don't build here yet
│       └── rendering/    NOT the 3D renderer — that's frontend/. This
│                         is reserved for server-side things like video
│                         export, later
│
└── frontend/       JavaScript. The eyes. Draws whatever numbers the
    └── src/         backend sends it, has zero idea what a Coulomb
        ├── scene/        force is. THIS is where frontend work happens:
        │                 PlasmaGlobe.js (the globe + lightning + glass
        │                 material), SceneManager.js (camera, controls,
        │                 render loop), lighting.js
        ├── network/      SimulationClient.js — the WebSocket connection,
        │                 the only file that speaks the backend's "language"
        ├── config/       colors, camera settings — visual constants,
        │                 the frontend equivalent of constants.py
        └── utils/        small helpers (FPS counter, math helpers)
```

**The one rule that makes this make sense:** each folder only knows about
the folder directly "below" it. `physics/` doesn't know `simulation/`
exists. `simulation/` doesn't know `server/` exists. `server/` doesn't know
the frontend exists beyond "I send JSON over a socket, sometimes I get one
back." If you're ever unsure where something goes, ask "what does this
code actually need to know about?" and put it in the outermost layer that
still answers that honestly.

### If you're doing frontend work

You can do almost everything you want inside `frontend/src/`, especially
`scene/PlasmaGlobe.js`, without ever touching Python. The backend already
sends you everything you need over the WebSocket — particle positions,
filament line segments, all as plain arrays of numbers. If you want new
*data* from the backend (not just a new way of drawing existing data),
that's the one time you'll need to poke into `backend/plasmaforge/simulation/state.py`
to see what's being sent, and possibly `engine.py`/`classic_mode.py` to
add something new to send.

### If you're doing backend/physics work

Live in `backend/plasmaforge/physics/` and `simulation/`. `config/constants.py`
is where almost every "does this feel right" tweak lives — start there
before writing new code.

### Files you'll see that aren't "real" — build artifacts, ignore them

If you look in `backend/plasmaforge/physics/` you'll see more than just
the `.pyx` source files. Here's what everything is:

| File type | What it is | Do you need it? |
|---|---|---|
| `*.pyx`, `*.pxd` | Actual Cython source code | Yes — this is the real code |
| `*.c` | Auto-generated C code from compiling the `.pyx` | No — regenerated every build, ignore it |
| `*.html` | Cython's "how well did I optimize this" report | No — purely diagnostic, safe to delete |
| `*.pyd` (Windows) / `*.so` (Mac/Linux) | The actual compiled binary your Python imports | **Yes** — this is what makes it fast, don't delete |
| `__pycache__/` | Python's bytecode cache | No — auto-regenerated, meaningless |
| `build/` | Leftover scratch folder from the build process | No — safe to delete anytime |

All of the "No" ones are already covered by `.gitignore`, so if you push
this to GitHub none of it shows up there anyway — this table is just so
you're not confused seeing them locally.

`tests/` and `benchmarks/` are real, checked-in code — but you don't need
to touch or even open them unless you're changing backend physics. They
exist to catch "did my change accidentally break the math," not to run
the app.

## Setup (Windows)

This is what we're both running, so it's first.

Cython compiles to real machine code, which means you need an actual C
compiler installed — this is the one step that WILL trip you up if skipped:

1. Grab **[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)**
2. Check **"Desktop development with C++"** in the installer — the default
   selection under that workload is fine
3. Let it install, then **fully close and reopen your terminal / VS Code**
   — this step is not optional, Windows won't pick up the compiler otherwise
4. Test it:
   ```powershell
   cd backend
   python setup.py build_ext --inplace
   ```
   `error: Microsoft Visual C++ 14.0 or greater is required` means the
   Build Tools install didn't take — recheck that box (Visual Studio
   Installer → Modify).

Once that succeeds:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python setup.py build_ext --inplace
pytest                              # optional — confirms the physics is correct
python -m plasmaforge.server.app    # leave this running
```

New terminal:

```powershell
cd frontend
yarn install
yarn dev
```

Open the URL Vite prints (usually `http://localhost:5173`).

<details>
<summary>Setup (macOS / Linux)</summary>

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python setup.py build_ext --inplace
pytest
python -m plasmaforge.server.app

# separate terminal
cd frontend
yarn install
yarn dev
```

macOS needs Xcode Command Line Tools (`xcode-select --install`); most
Linux distros already ship `gcc`. If `build_ext` fails with a
missing-compiler error, that's the fix.

</details>

## Tuning the plasma

Everything about how this *feels* lives in one file:
**`backend/plasmaforge/config/constants.py`**. Plain Python, not Cython —
no rebuild needed, just save and restart `python -m plasmaforge.server.app`.

| Constant | What it does |
|---|---|
| `DEFAULT_FILAMENT_COUNT` | how many arcs exist at once |
| `FILAMENT_PATH_SEGMENTS` | kinks per arc — more = more detailed jagged shape |
| `FILAMENT_JITTER` | how far each kink wobbles — the main "jaggedness" dial |
| `FILAMENT_BRANCH_PROBABILITY` | odds of a little spark branching off |
| `FILAMENT_MIN/MAX_LIFETIME_S` | how long an arc lives before flickering out |
| `PARTICLE_MAX_AGE_S` | how long ambient dots drift before disappearing |
| `DEFAULT_MAX_PARTICLES` | hard cap on particle count |
| `ELECTRODE_RADIUS` | size of the glowing center ball |

Also: `TOUCH_BIAS_PROBABILITY` (`simulation/modes/classic_mode.py`) — what
fraction of arcs chase your cursor vs. stay near the center while touching.

**⚠️ Learned the hard way:** `DEFAULT_FILAMENT_COUNT` and
`FILAMENT_PATH_SEGMENTS` multiply together for render cost, because the
frontend rebuilds all lightning geometry from scratch every frame. `150 x 15`
tanks FPS. `85 x 8` runs great. Don't push both at once without watching
the FPS counter.

## Contributing

- Branch per feature/experiment instead of committing straight to `main`
- If you touch a `.pyx` file, rebuild AND test before calling it done:
  `python setup.py build_ext --inplace && pytest` — a Cython file can
  compile clean and still silently produce wrong numbers
- New tunable value → goes in `constants.py`, not hardcoded inline
- If you're both about to tune `constants.py` at the same time, say so —
  it turns into merge-conflict soup otherwise
- The layering rule (see "Finding your way around") is the one thing
  worth actually defending — everything else is fair game to bend

## Roadmap

**Done:** real field physics, branching lightning, touch interaction,
particle despawn, 4 compiled Cython modules.

**Reasonable next steps:**
- Update `PlasmaGlobe.js`'s geometry in place instead of rebuilding every
  frame — this is the actual cap on how far filament count can scale
- A second simulation mode (interface already supports it)
- More of `ParticleSystem`'s bookkeeping moved into Cython

**Someday:**
- GPU acceleration (a config switch is already reserved for this)
- MediaPipe hand tracking (an empty folder is already waiting for this)