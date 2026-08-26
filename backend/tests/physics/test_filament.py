import random
from plasmaforge.physics.filament import spawn_filament


def test_filament_grows_away_from_existing_tip():
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
        dot = end[0] * existing_tip[0] + end[1] * existing_tip[1] + end[2] * existing_tip[2]
        if dot < 0:
            opposite_count += 1
    assert opposite_count > trials * 0.6


def test_filament_with_no_other_tips_still_produces_valid_geometry():
    rng = random.Random(3)
    filament = spawn_filament(origin=(0.0, 0.0, 0.0), target_radius=1.0, other_tips=[], rng=rng)
    assert len(filament.segments) >= 1
    end = filament.target
    length = (end[0] ** 2 + end[1] ** 2 + end[2] ** 2) ** 0.5
    assert abs(length - 1.0) < 1e-6


def test_filament_locks_onto_active_touch_point():
    rng = random.Random(11)
    touch = (0.0, 1.0, 0.0)
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
    assert dot > 0.95


def test_main_path_points_form_continuous_chain_from_origin():
    rng = random.Random(5)
    origin = (0.0, 0.0, 0.0)
    filament = spawn_filament(origin=origin, target_radius=1.0, other_tips=[], rng=rng)
    main_points = filament.main_path_points
    assert main_points[0] == origin
    # last point should be very close to the target (allowing for the
    # small jitter that shrinks to ~0 approaching the target)
    last = main_points[-1]
    target = filament.target
    dist = sum((a - b) ** 2 for a, b in zip(last, target)) ** 0.5
    assert dist < 1e-6


def test_branch_segment_pairs_are_even_length():
    rng = random.Random(9)
    filament = spawn_filament(origin=(0.0, 0.0, 0.0), target_radius=1.0, other_tips=[], rng=rng)
    # Every branch contributes exactly one (start, end) pair -> even length
    assert len(filament.branch_segment_pairs) % 2 == 0
