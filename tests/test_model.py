import math

import pytest

from gravitylab.sim.model import GravitySim, RenderOptions
from gravitylab.theme import qcolor


def test_reset_system_creates_expected_body_count():
    sim = GravitySim()
    for planets in range(1, 10):
        sim.reset_system(planets)
        assert sim.num_planets == planets
        assert len(sim.bodies) == planets + 1


def test_selected_planet_is_clamped():
    sim = GravitySim()
    sim.reset_system(3)
    sim.set_selected_planet(999)
    assert sim.selected_planet_idx == 3
    sim.set_selected_planet(-10)
    assert sim.selected_planet_idx == 1


def test_speed_scaling_changes_selected_velocity_magnitude():
    sim = GravitySim()
    sim.reset_system(3)
    body = sim.selected_body()
    speed_before = math.hypot(body.vx, body.vy)
    sim.set_speed_scale_for_selected(1.1)
    speed_after = math.hypot(body.vx, body.vy)
    assert speed_after > speed_before
    assert speed_after == pytest.approx(speed_before * 1.1)


def test_mass_scaling_changes_selected_body_mass():
    sim = GravitySim()
    sim.reset_system(3)
    body = sim.selected_body()
    mass_before = body.mass
    sim.set_mass_scale_for_selected(1.1)
    assert body.mass == pytest.approx(mass_before * 1.1)


def test_toggle_mode_only_changes_requested_flag():
    sim = GravitySim()
    before = (
        sim.render_options.show_grid,
        sim.render_options.show_trails,
        sim.render_options.show_theory,
        sim.only_sun,
    )
    sim.toggle_mode("grid")
    after = (
        sim.render_options.show_grid,
        sim.render_options.show_trails,
        sim.render_options.show_theory,
        sim.only_sun,
    )
    assert before[0] != after[0]
    assert before[1:] == after[1:]


def test_step_handles_min_and_max_system_sizes():
    sim = GravitySim()
    sim.reset_system(1)
    sim.step()
    sim.reset_system(9)
    sim.step()
    assert sim.step_count == 1


def test_snapshot_and_stats_expose_expected_fields():
    sim = GravitySim()
    sim.step()
    snapshot = sim.snapshot()
    stats = sim.stats()
    assert snapshot.selected_index == sim.selected_planet_idx
    assert stats.body_count == len(sim.bodies)
    assert stats.selected_speed > 0
    assert stats.selected_radius > 0
    assert hasattr(snapshot, "camera_mode")
    assert hasattr(snapshot, "active_preset")
    assert hasattr(snapshot.render_options, "show_labels")
    assert hasattr(snapshot.render_options, "clean_ui")
    assert hasattr(snapshot.render_options, "cinematic_mode")


def test_render_options_have_demo_flags():
    options = RenderOptions()
    assert options.show_labels is True
    assert options.clean_ui is False
    assert options.cinematic_mode is False
    assert options.follow_selected is False
    assert options.show_sparklines is True


def test_default_gravity_is_one():
    sim = GravitySim()
    assert sim.g == 1.0


def test_default_body_masses_match_earth_mass_units():
    sim = GravitySim()
    sim.reset_system(3)
    assert sim.bodies[0].mass == pytest.approx(332946.0)
    assert sim.bodies[1].mass == pytest.approx(0.0553)
    assert sim.bodies[2].mass == pytest.approx(0.815)
    assert sim.bodies[3].mass == pytest.approx(1.0)


def test_apply_named_preset_changes_active_state():
    sim = GravitySim()
    sim.apply_named_preset("spiral-in")
    snapshot = sim.snapshot()
    assert snapshot.active_preset == "Спираль к Солнцу"
    assert snapshot.selected_index == 1
    assert snapshot.camera_mode == "follow_selected"
    assert snapshot.g == 1.0


def test_planet_interactions_preset_makes_only_sun_difference_visible():
    sim = GravitySim()
    sim.apply_named_preset("planet-interactions")
    selected_index = sim.selected_planet_idx

    full_acc = sim.compute_accelerations()[selected_index]
    sim.set_mode("only_sun", True)
    sun_only_acc = sim.compute_accelerations()[selected_index]

    full_norm = math.hypot(*full_acc)
    sun_only_norm = math.hypot(*sun_only_acc)
    difference = math.hypot(full_acc[0] - sun_only_acc[0], full_acc[1] - sun_only_acc[1])

    assert full_norm > 0
    assert sun_only_norm > 0
    assert difference / full_norm > 0.07


def test_solar_system_preset_enables_inner_asteroid_belt():
    sim = GravitySim()
    sim.apply_named_preset("solar-system")
    snapshot = sim.snapshot()
    assert snapshot.active_preset == "Солнечная система"
    assert snapshot.asteroid_belt_enabled is True
    assert sim.bodies[5].name == "Юпитер"
    assert sim.bodies[5].mass == pytest.approx(317.8)
    mars_radius = math.hypot(sim.bodies[4].x, sim.bodies[4].y)
    jupiter_radius = math.hypot(sim.bodies[5].x, sim.bodies[5].y)
    asteroid_radii = [math.hypot(body.x, body.y) for body in sim.bodies if body.is_asteroid]
    assert asteroid_radii
    assert min(asteroid_radii) > mars_radius
    assert max(asteroid_radii) < jupiter_radius


def test_metrics_history_updates_after_steps():
    sim = GravitySim()
    before = len(sim.selected_body_series().distance_history)
    sim.step()
    sim.step()
    after = sim.selected_body_series()
    assert len(after.distance_history) >= before + 2
    assert len(after.speed_history) >= before + 2


def test_set_cinematic_mode_updates_state():
    sim = GravitySim()
    sim.set_cinematic_mode(True)
    assert sim.render_options.cinematic_mode is True
    assert sim.camera_mode in {"follow_selected", "manual"}


def test_time_scale_is_clamped_to_safe_upper_bound():
    sim = GravitySim()
    sim.set_time_scale(99.0)
    assert sim.time_scale == 50.0


def test_gravity_is_clamped_to_safe_upper_bound():
    sim = GravitySim()
    sim.set_g(99.0)
    assert sim.g == 12.0


def test_theme_qcolor_parses_rgba_strings():
    color = qcolor("rgba(142, 200, 255, 0.18)")
    assert color.red() == 142
    assert color.green() == 200
    assert color.blue() == 255
    assert color.alpha() > 0


def test_asteroid_belt_adds_extra_bodies_without_changing_planet_count():
    sim = GravitySim()
    base_body_count = len(sim.bodies)
    sim.set_asteroid_belt_enabled(True)
    assert sim.num_planets == 3
    assert len(sim.bodies) > base_body_count
    assert sim.snapshot().asteroid_belt_enabled is True
    planet_radii = [math.hypot(body.x, body.y) for body in sim.bodies[1:] if not body.is_asteroid]
    asteroid_radii = [math.hypot(body.x, body.y) for body in sim.bodies[1:] if body.is_asteroid]
    assert asteroid_radii
    assert max(asteroid_radii) < max(planet_radii)


def test_asteroid_belt_toggle_round_trips():
    sim = GravitySim()
    sim.set_asteroid_belt_enabled(True)
    with_belt = len(sim.bodies)
    sim.set_asteroid_belt_enabled(False)
    assert len(sim.bodies) < with_belt
    assert sim.snapshot().asteroid_belt_enabled is False
