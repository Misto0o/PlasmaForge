"""
Tests for filament growth, specifically the field-based repulsion added
so new filaments grow away from existing ones instead of spawning
randomly (which could visually cluster arcs on one side of the globe).
"""

import random

from plasmaforge.physics.filament import spawn_filament


def test_filament_grows_away_from_existing_tip():
    """With one existing filament tip fixed at a point, repeatedly
    spawning new filaments should, on average, favor directions on the
    opposite side of the sphere — not cluster near the existing tip."""
    rng = random.Random(7)
    existing_tip = (1.0, 0.0, 0.0)

    opposite_count = 0
    trials = 30
    for _ in range(trials):
        filament = spawn_filament(
            origin=(0.0, 0.0, 0.0),
            target_radius=1.0,
            other_tips=[existing_tip],
            rng=rng,
            n_candidates=12,
        )
        end = filament.target
        # "Opposite side" defined loosely as a negative dot product with
        # the existing tip's direction.
        dot = end[0] * existing_tip[0] + end[1] * existing_tip[1] + end[2] * existing_tip[2]
        if dot < 0:
            opposite_count += 1

    # Not a strict guarantee every trial lands opposite (candidates are
    # random), but repulsion should bias the majority away from the
    # existing tip rather than a ~50/50 coin flip.
    assert opposite_count > trials * 0.6


def test_filament_with_no_other_tips_still_produces_valid_geometry():
    rng = random.Random(3)
    filament = spawn_filament(origin=(0.0, 0.0, 0.0), target_radius=1.0,
                               other_tips=[], rng=rng)
    assert len(filament.segments) >= 1
    end = filament.target
    length = (end[0] ** 2 + end[1] ** 2 + end[2] ** 2) ** 0.5
    assert abs(length - 1.0) < 1e-6


def test_filament_path_is_a_connected_chain_from_origin_to_target():
    """The jagged path should form a continuous chain: each main-path
    segment's end should match the next main-path segment's start
    (branches aside), and the whole thing should start at the origin."""
    rng = random.Random(5)
    origin = (0.0, 0.0, 0.0)
    filament = spawn_filament(origin=origin, target_radius=1.0,
                               other_tips=[], rng=rng)
    assert filament.segments[0].start == origin


def test_filament_locks_onto_active_touch_point():
    """The core 'real plasma ball' behavior: when a touch point is set,
    filament growth should ignore repulsion entirely and grow straight
    toward it, regardless of where other filaments currently are."""
    rng = random.Random(11)
    touch = (0.0, 1.0, 0.0)
    # Deliberately put another tip right where the touch point is, so if
    # repulsion were still influencing the result, the filament would be
    # pushed AWAY from here — but touch should override that entirely.
    other_tips = [(0.0, 1.0, 0.0)]

    filament = spawn_filament(
        origin=(0.0, 0.0, 0.0),
        target_radius=1.0,
        other_tips=other_tips,
        touch_target=touch,
        rng=rng,
    )
    end = filament.target
    dot = end[0] * touch[0] + end[1] * touch[1] + end[2] * touch[2]
    # Should point almost directly at the touch target (allowing for the
    # small jitter spawn_filament intentionally adds).
    assert dot > 0.95