# ⚡ PlasmaForge

**A real-time plasma globe simulation that runs in your browser.**

PlasmaForge uses physics-based calculations to create dynamic lightning that reacts to your cursor.

Built by two people as a side project.

## 🛠️ Tech Stack

* **Python** — simulation backend
* **Cython** — performance-critical physics
* **WebSockets** — real-time communication
* **JavaScript / Three.js** — 3D rendering
* **Vite** — frontend development

## ✨ Features

* Real-time electric field simulation
* Dynamic lightning arcs
* Branching lightning
* Cursor interaction
* Particle simulation
* WebSocket updates
* Cython-compiled physics
* Support for many simultaneous filaments

## 📁 Project Structure

```text
plasmaforge/
├── backend/
│   └── plasmaforge/
│       ├── config/        # Simulation settings
│       ├── physics/       # Cython physics
│       ├── simulation/    # Simulation logic
│       ├── server/        # WebSocket server
│       ├── interaction/   # Future interaction features
│       └── rendering/     # Future rendering features
│
├── frontend/
│   └── src/
│       ├── scene/         # Three.js globe and rendering
│       ├── network/       # WebSocket connection
│       ├── config/        # Visual settings
│       └── utils/         # Utility functions
│
├── tests/                 # Physics tests
└── benchmarks/            # Performance tests
```

## 💻 Setup

### Windows

Cython requires a C/C++ compiler.

Install **Microsoft C++ Build Tools** and select:

**Desktop development with C++**

Then restart your terminal or VS Code.

### Backend

```powershell
cd backend

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements-dev.txt

python setup.py build_ext --inplace

pytest

python -m plasmaforge.server.app
```

Keep the backend running.

### Frontend

Open another terminal:

```powershell
cd frontend

yarn install
yarn dev
```

Open the URL Vite provides, usually:

`http://localhost:5173`

## 🎛️ Configuration

Most simulation settings are located in:

`backend/plasmaforge/config/constants.py`

| Setting                       | Description                |
| ----------------------------- | -------------------------- |
| `DEFAULT_FILAMENT_COUNT`      | Number of lightning arcs   |
| `FILAMENT_PATH_SEGMENTS`      | Number of segments per arc |
| `FILAMENT_JITTER`             | Lightning jaggedness       |
| `FILAMENT_BRANCH_PROBABILITY` | Chance of branching        |
| `FILAMENT_MIN/MAX_LIFETIME_S` | Lightning lifetime         |
| `PARTICLE_MAX_AGE_S`          | Particle lifetime          |
| `DEFAULT_MAX_PARTICLES`       | Maximum particle count     |
| `ELECTRODE_RADIUS`            | Center electrode size      |

Higher filament counts and more segments increase rendering cost.

For example:

* `85 × 8` — good performance
* `150 × 15` — significantly heavier

## ⚙️ Cython Files

You may see additional files in the physics directory:

| File            | Description                |
| --------------- | -------------------------- |
| `.pyx` / `.pxd` | Cython source code         |
| `.c`            | Generated C code           |
| `.html`         | Cython optimization report |
| `.pyd` / `.so`  | Compiled extension         |
| `__pycache__/`  | Python cache               |
| `build/`        | Build files                |

The `.pyx` and `.pxd` files are the actual source code.

## 🤝 Contributing

* Use a separate branch for new features
* Rebuild and test after changing Cython code
* Keep configurable values in `constants.py`
* Avoid hardcoding tunable values
* Keep the backend and frontend separated

After changing a `.pyx` file:

```powershell
python setup.py build_ext --inplace
pytest
```

## 🚀 Roadmap

### Completed

* Real electric field physics
* Branching lightning
* Cursor interaction
* Particle despawning
* Cython physics modules

### Planned

* Improve frontend geometry performance
* Add another simulation mode
* Move more particle calculations into Cython
* GPU acceleration
* MediaPipe hand tracking
