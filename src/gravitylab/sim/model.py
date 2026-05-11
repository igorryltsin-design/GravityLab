from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import Literal


ColorRGB = tuple[int, int, int]
CameraMode = Literal["manual", "follow_selected", "follow_sun", "auto_frame"]
ModeName = Literal["trails", "grid", "theory", "labels", "only_sun", "paused", "asteroid_belt"]


@dataclass
class Body:
    name: str
    mass: float
    radius_px: int
    x: float
    y: float
    vx: float
    vy: float
    color: ColorRGB
    trail: deque[tuple[float, float]]
    is_asteroid: bool = False


@dataclass(frozen=True)
class BodySnapshot:
    index: int
    name: str
    mass: float
    radius_px: int
    x: float
    y: float
    vx: float
    vy: float
    color: ColorRGB
    trail: tuple[tuple[float, float], ...]
    is_asteroid: bool


@dataclass(frozen=True)
class BodySeed:
    name: str
    radius: float
    angle_deg: float
    speed_scale: float = 1.0
    radial_bias: float = 0.0
    angle_velocity_bias_deg: float = 0.0
    color: ColorRGB | None = None


@dataclass(frozen=True)
class SimulationConfig:
    g: float = 1.0
    dt: float = 0.02
    softening: float = 8.0
    sun_mass: float = 332946.0
    sun_radius_px: int = 35
    planet_mass: float = 1.0
    planet_radius_px: int = 7
    trail_len: int = 900
    default_planets: int = 3
    history_len: int = 240
    asteroid_belt_count: int = 96
    mass_to_sim_units: float = 5000.0 / 332946.0


@dataclass
class RenderOptions:
    show_grid: bool = True
    show_trails: bool = True
    show_theory: bool = True
    show_labels: bool = True
    clean_ui: bool = False
    cinematic_mode: bool = False
    follow_selected: bool = False
    show_sparklines: bool = True
    label_zoom_threshold: float = 0.6
    background_variant: str = "nebula"
    trail_alpha: int = 145
    zoom: float = 1.0


@dataclass(frozen=True)
class SimulationStats:
    fps: float
    sim_time: float
    step_count: int
    body_count: int
    selected_index: int
    selected_speed: float
    selected_radius: float


@dataclass(frozen=True)
class BodySeriesSnapshot:
    distance_history: tuple[float, ...]
    speed_history: tuple[float, ...]


@dataclass(frozen=True)
class PresetDefinition:
    id: str
    label: str
    description: str
    planet_count: int
    initial_state: tuple[BodySeed, ...]
    selected_index: int
    camera_mode: CameraMode
    render_defaults: RenderOptions
    gravity: float | None = None
    time_scale: float | None = None
    asteroid_belt_enabled: bool = False
    asteroid_belt_count: int | None = None
    asteroid_belt_inner_radius: float | None = None
    asteroid_belt_outer_radius: float | None = None


@dataclass(frozen=True)
class SimulationSnapshot:
    bodies: tuple[BodySnapshot, ...]
    selected_index: int
    num_planets: int
    g: float
    only_sun: bool
    paused: bool
    time_scale: float
    render_options: RenderOptions
    camera_mode: CameraMode
    follow_target_index: int | None
    active_preset: str | None
    asteroid_belt_enabled: bool
    asteroid_belt_count: int


class GravitySim:
    """Учебный 2D-симулятор N-тел с состоянием, удобным для UI."""

    USE_EXPLICIT_EULER = False
    BODY_NAMES = (
        "Солнце",
        "Меркурий",
        "Венера",
        "Земля",
        "Марс",
        "Юпитер",
        "Сатурн",
        "Уран",
        "Нептун",
        "Плутон",
    )
    BODY_MASSES_EARTH = {
        "Солнце": 332946.0,
        "Меркурий": 0.0553,
        "Венера": 0.815,
        "Земля": 1.0,
        "Марс": 0.107,
        "Юпитер": 317.8,
        "Юпитер I": 317.8,
        "Юпитер II": 317.8,
        "Сатурн": 95.16,
        "Уран": 14.54,
        "Нептун": 17.15,
        "Плутон": 0.00218,
    }
    ASTEROID_MASS_EARTH = 0.0002

    def __init__(
        self,
        config: SimulationConfig | None = None,
        render_options: RenderOptions | None = None,
    ) -> None:
        # Конфиг физики (dt, G, softening, массы) и флаги рендера задаются отдельно.
        self.config = config or SimulationConfig()
        self.render_options = render_options or RenderOptions()
        # Пресеты - готовые учебные сцены с начальными условиями.
        self.presets = self._build_presets()

        self.num_planets = self.config.default_planets
        self.selected_planet_idx = 1
        self.only_sun = False
        self.paused = False
        self.time_scale = 1.0
        self.step_count = 0
        self.sim_time = 0.0
        self.fps = 0.0
        self.camera_mode: CameraMode = "manual"
        self.follow_target_index: int | None = None
        self.active_preset: str | None = None
        self.asteroid_belt_enabled = False
        self.asteroid_belt_count = self.config.asteroid_belt_count
        self.bodies: list[Body] = []
        self._distance_history: dict[int, deque[float]] = {}
        self._speed_history: dict[int, deque[float]] = {}
        self._current_seeds: tuple[BodySeed, ...] = ()
        self._asteroid_belt_range_override: tuple[float, float] | None = None

        self.apply_named_preset("three-orbits")

    @property
    def g(self) -> float:
        return self.config.g

    @g.setter
    def g(self, value: float) -> None:
        # Ограничиваем G, чтобы симуляция оставалась устойчивой и управляемой.
        self.config = SimulationConfig(**{**self.config.__dict__, "g": max(0.0, min(12.0, value))})

    def reset_system(self, n_planets: int) -> None:
        self._create_default_system(max(1, min(9, int(n_planets))))
        self.active_preset = None
        self.camera_mode = "manual"
        self.follow_target_index = None
        self.render_options.follow_selected = False

    def apply_preset(self, preset_name: str) -> None:
        preset_map = {
            "1 planet": "single-orbit",
            "3 planets": "three-orbits",
            "5 planets": "chaos",
            "chaotic setup": "chaos",
        }
        preset_id = preset_map.get(preset_name.lower())
        if preset_id is None:
            raise ValueError(f"Unknown preset: {preset_name}")
        self.apply_named_preset(preset_id)

    def preset_definitions(self) -> tuple[PresetDefinition, ...]:
        return tuple(self.presets.values())

    def apply_named_preset(self, preset_id: str) -> None:
        if preset_id not in self.presets:
            raise ValueError(f"Unknown preset: {preset_id}")
        preset = self.presets[preset_id]

        # Пресет может менять "глобальные" параметры сцены.
        if preset.gravity is not None:
            self.set_g(preset.gravity)
        if preset.time_scale is not None:
            self.set_time_scale(preset.time_scale)

        self.asteroid_belt_enabled = preset.asteroid_belt_enabled
        if preset.asteroid_belt_count is not None:
            self.asteroid_belt_count = preset.asteroid_belt_count
        self._asteroid_belt_range_override = (
            (preset.asteroid_belt_inner_radius, preset.asteroid_belt_outer_radius)
            if preset.asteroid_belt_inner_radius is not None and preset.asteroid_belt_outer_radius is not None
            else None
        )

        self._apply_seeded_system(preset.initial_state)
        self.active_preset = preset.label
        self.set_selected_planet(preset.selected_index)

        # Пресет также задаёт стартовые визуальные режимы.
        self.render_options.show_grid = preset.render_defaults.show_grid
        self.render_options.show_trails = preset.render_defaults.show_trails
        self.render_options.show_theory = preset.render_defaults.show_theory
        self.render_options.show_labels = preset.render_defaults.show_labels
        self.render_options.show_sparklines = preset.render_defaults.show_sparklines
        self.render_options.label_zoom_threshold = preset.render_defaults.label_zoom_threshold
        self.render_options.cinematic_mode = preset.render_defaults.cinematic_mode
        self.render_options.follow_selected = preset.render_defaults.follow_selected

        self.camera_mode = preset.camera_mode
        if preset.camera_mode == "follow_sun":
            self.follow_target_index = 0
        elif preset.camera_mode == "follow_selected":
            self.follow_target_index = self.selected_planet_idx
        else:
            self.follow_target_index = None

    def set_num_planets(self, n_planets: int) -> None:
        self.reset_system(n_planets)

    def set_selected_planet(self, index: int) -> None:
        if not self.bodies:
            self.selected_planet_idx = 1
            return
        self.selected_planet_idx = max(1, min(self.num_planets, int(index)))
        if self.render_options.follow_selected or self.camera_mode == "follow_selected":
            self.follow_target_index = self.selected_planet_idx
            self.camera_mode = "follow_selected"

    def set_speed_scale_for_selected(self, factor: float) -> None:
        if len(self.bodies) <= self.selected_planet_idx:
            return
        body = self.bodies[self.selected_planet_idx]
        body.vx *= factor
        body.vy *= factor

    def set_mass_scale_for_selected(self, factor: float) -> None:
        if len(self.bodies) <= self.selected_planet_idx:
            return
        body = self.bodies[self.selected_planet_idx]
        body.mass = max(0.0001, min(1_000_000.0, body.mass * factor))

    def set_time_scale(self, scale: float) -> None:
        # Слишком большие значения делают модель "рваной", поэтому есть верхняя граница.
        self.time_scale = max(0.05, min(50.0, scale))

    def set_g(self, value: float) -> None:
        self.g = value

    def set_render_zoom(self, zoom: float) -> None:
        # Зум хранится в модели, чтобы UI и физическая сцена были синхронизированы.
        self.render_options.zoom = max(0.2, min(4.0, zoom))

    def set_clean_ui(self, enabled: bool) -> None:
        self.render_options.clean_ui = enabled

    def set_cinematic_mode(self, enabled: bool) -> None:
        self.render_options.cinematic_mode = enabled
        if enabled:
            if self.follow_target_index is None:
                self.set_follow_target(self.selected_planet_idx)
            if self.camera_mode == "manual":
                self.camera_mode = "follow_selected"
        else:
            self.camera_mode = "manual"
            self.render_options.follow_selected = False
            self.follow_target_index = None

    def set_follow_target(self, index: int | None) -> None:
        if index is None:
            self.follow_target_index = None
            self.render_options.follow_selected = False
            if self.render_options.cinematic_mode:
                self.camera_mode = "manual"
            return

        clamped = max(0, min(len(self.bodies) - 1, int(index))) if self.bodies else None
        if clamped is None:
            return
        self.follow_target_index = clamped
        self.render_options.follow_selected = clamped != 0
        self.camera_mode = "follow_sun" if clamped == 0 else "follow_selected"

    def set_camera_mode(self, mode: CameraMode) -> None:
        self.camera_mode = mode
        if mode == "manual":
            self.follow_target_index = None
            self.render_options.follow_selected = False
            return
        if mode == "follow_sun":
            self.follow_target_index = 0
            self.render_options.follow_selected = False
            return
        if mode == "follow_selected":
            self.follow_target_index = self.selected_planet_idx
            self.render_options.follow_selected = True
            return
        self.follow_target_index = None

    def set_fps(self, fps: float) -> None:
        self.fps = max(0.0, fps)

    def toggle_mode(self, mode: ModeName) -> None:
        if mode == "trails":
            self.render_options.show_trails = not self.render_options.show_trails
            if not self.render_options.show_trails:
                for body in self.bodies:
                    body.trail.clear()
            return
        if mode == "grid":
            self.render_options.show_grid = not self.render_options.show_grid
            return
        if mode == "theory":
            self.render_options.show_theory = not self.render_options.show_theory
            return
        if mode == "labels":
            self.render_options.show_labels = not self.render_options.show_labels
            return
        if mode == "only_sun":
            self.only_sun = not self.only_sun
            return
        if mode == "paused":
            self.paused = not self.paused
            return
        if mode == "asteroid_belt":
            self.set_asteroid_belt_enabled(not self.asteroid_belt_enabled)
            return
        raise ValueError(f"Unknown mode: {mode}")

    def set_mode(self, mode: ModeName, enabled: bool) -> None:
        current = self.get_mode(mode)
        if current != enabled:
            self.toggle_mode(mode)

    def get_mode(self, mode: ModeName) -> bool:
        if mode == "trails":
            return self.render_options.show_trails
        if mode == "grid":
            return self.render_options.show_grid
        if mode == "theory":
            return self.render_options.show_theory
        if mode == "labels":
            return self.render_options.show_labels
        if mode == "only_sun":
            return self.only_sun
        if mode == "paused":
            return self.paused
        if mode == "asteroid_belt":
            return self.asteroid_belt_enabled
        raise ValueError(f"Unknown mode: {mode}")

    def set_asteroid_belt_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self.asteroid_belt_enabled == enabled:
            return
        self.asteroid_belt_enabled = enabled
        # Пересобираем систему из тех же seed-ов, чтобы корректно добавить/убрать астероиды.
        selected_index = self.selected_planet_idx
        active_preset = self.active_preset
        self._apply_seeded_system(self._current_seeds)
        self.selected_planet_idx = max(1, min(self.num_planets, selected_index))
        self.active_preset = active_preset

    def set_asteroid_belt_density(self, count: int) -> None:
        # Плотность ограничена, чтобы не перегрузить рендер и тесты.
        clamped = max(0, min(240, int(count)))
        if self.asteroid_belt_count == clamped:
            return
        self.asteroid_belt_count = clamped
        if self.asteroid_belt_enabled:
            selected_index = self.selected_planet_idx
            active_preset = self.active_preset
            self._apply_seeded_system(self._current_seeds)
            self.selected_planet_idx = max(1, min(self.num_planets, selected_index))
            self.active_preset = active_preset

    def step(self, dt: float | None = None) -> None:
        # Реальный шаг интегрирования: базовый dt * пользовательский масштаб времени.
        step_dt = (dt if dt is not None else self.config.dt) * self.time_scale
        acc = self.compute_accelerations()

        if self.USE_EXPLICIT_EULER:
            # Классический явный Эйлер: сначала координаты, потом скорость.
            for i, body in enumerate(self.bodies):
                ax, ay = acc[i]
                body.x += body.vx * step_dt
                body.y += body.vy * step_dt
                body.vx += ax * step_dt
                body.vy += ay * step_dt
        else:
            # Полу-неявный вариант обычно устойчивее для орбитальных сцен.
            for i, body in enumerate(self.bodies):
                ax, ay = acc[i]
                body.vx += ax * step_dt
                body.vy += ay * step_dt
                body.x += body.vx * step_dt
                body.y += body.vy * step_dt

        if self.render_options.show_trails:
            # Следы хранятся как очередь фиксированной длины.
            for body in self.bodies:
                body.trail.append((body.x, body.y))

        self.step_count += 1
        self.sim_time += step_dt
        self.advance_metrics_history()

    def advance_metrics_history(self) -> None:
        if not self.bodies:
            return
        sun = self.bodies[0]
        for index, body in enumerate(self.bodies[1:], start=1):
            if body.is_asteroid:
                continue
            distance = math.hypot(body.x - sun.x, body.y - sun.y)
            speed = math.hypot(body.vx, body.vy)
            self._distance_history[index].append(distance)
            self._speed_history[index].append(speed)

    def selected_body_series(self) -> BodySeriesSnapshot:
        index = self.selected_planet_idx
        return BodySeriesSnapshot(
            distance_history=tuple(self._distance_history.get(index, deque())),
            speed_history=tuple(self._speed_history.get(index, deque())),
        )

    def compute_accelerations(self) -> list[tuple[float, float]]:
        n_bodies = len(self.bodies)
        ax = [0.0] * n_bodies
        ay = [0.0] * n_bodies

        if n_bodies <= 1:
            return list(zip(ax, ay))

        if self.only_sun:
            # Упрощённый учебный режим: каждая планета чувствует только Солнце.
            sun = self.bodies[0]
            for i in range(1, n_bodies):
                body = self.bodies[i]
                force_x, force_y = self._accel_from_to(body.x, body.y, sun.x, sun.y, sun.mass)
                ax[i] += force_x
                ay[i] += force_y
            return list(zip(ax, ay))

        # Полная N-body модель: суммируем вклад каждого тела для каждого тела.
        for i, body_i in enumerate(self.bodies):
            for j, body_j in enumerate(self.bodies):
                if i == j:
                    continue
                force_x, force_y = self._accel_from_to(
                    body_i.x,
                    body_i.y,
                    body_j.x,
                    body_j.y,
                    body_j.mass,
                )
                ax[i] += force_x
                ay[i] += force_y

        return list(zip(ax, ay))

    def selected_body(self) -> Body:
        return self.bodies[self.selected_planet_idx]

    def stats(self) -> SimulationStats:
        body = self.selected_body()
        speed = math.hypot(body.vx, body.vy)
        distance = math.hypot(body.x - self.bodies[0].x, body.y - self.bodies[0].y)
        return SimulationStats(
            fps=self.fps,
            sim_time=self.sim_time,
            step_count=self.step_count,
            body_count=len(self.bodies),
            selected_index=self.selected_planet_idx,
            selected_speed=speed,
            selected_radius=distance,
        )

    def snapshot(self, trail_points: int | None = None) -> SimulationSnapshot:
        # UI получает "снимок" (неживые данные), чтобы не мутировать модель напрямую.
        bodies = tuple(
            BodySnapshot(
                index=i,
                name=body.name,
                mass=body.mass,
                radius_px=body.radius_px,
                x=body.x,
                y=body.y,
                vx=body.vx,
                vy=body.vy,
                color=body.color,
                trail=self._trail_snapshot(body, trail_points),
                is_asteroid=body.is_asteroid,
            )
            for i, body in enumerate(self.bodies)
        )
        render = RenderOptions(
            show_grid=self.render_options.show_grid,
            show_trails=self.render_options.show_trails,
            show_theory=self.render_options.show_theory,
            show_labels=self.render_options.show_labels,
            clean_ui=self.render_options.clean_ui,
            cinematic_mode=self.render_options.cinematic_mode,
            follow_selected=self.render_options.follow_selected,
            show_sparklines=self.render_options.show_sparklines,
            label_zoom_threshold=self.render_options.label_zoom_threshold,
            background_variant=self.render_options.background_variant,
            trail_alpha=self.render_options.trail_alpha,
            zoom=self.render_options.zoom,
        )
        return SimulationSnapshot(
            bodies=bodies,
            selected_index=self.selected_planet_idx,
            num_planets=self.num_planets,
            g=self.g,
            only_sun=self.only_sun,
            paused=self.paused,
            time_scale=self.time_scale,
            render_options=render,
            camera_mode=self.camera_mode,
            follow_target_index=self.follow_target_index,
            active_preset=self.active_preset,
            asteroid_belt_enabled=self.asteroid_belt_enabled,
            asteroid_belt_count=self.asteroid_belt_count,
        )

    def _trail_snapshot(self, body: Body, trail_points: int | None) -> tuple[tuple[float, float], ...]:
        if not body.trail:
            return ()
        if trail_points is None:
            return tuple(body.trail)
        cap = max(24, int(trail_points))
        if body.is_asteroid:
            # Для астероидов ограничиваем хвост сильнее: их много и они мелкие.
            cap = min(cap // 4, 96)
        if len(body.trail) <= cap:
            return tuple(body.trail)
        return tuple(list(body.trail)[-cap:])

    def _create_default_system(self, n_planets: int) -> None:
        # Если тел несколько, радиусы раскладываются от центра к внешней орбите.
        seeds = tuple(
            BodySeed(name=self._body_name(i + 1), radius=200.0 if n_planets == 1 else 120.0 + 200.0 * i / max(1, n_planets - 1), angle_deg=(360.0 * i / n_planets))
            for i in range(n_planets)
        )
        self._apply_seeded_system(seeds)

    def _apply_seeded_system(self, seeds: tuple[BodySeed, ...]) -> None:
        # Полная пересборка сцены: Солнце + планеты (+ астероиды по режиму).
        self._current_seeds = tuple(seeds)
        self.num_planets = len(seeds)
        self.selected_planet_idx = 1 if self.num_planets else 0
        self.step_count = 0
        self.sim_time = 0.0
        self.bodies = []

        sun = Body(
            name=self.BODY_NAMES[0],
            mass=self.config.sun_mass,
            radius_px=self.config.sun_radius_px,
            x=0.0,
            y=0.0,
            vx=0.0,
            vy=0.0,
            color=(255, 213, 94),
            trail=deque(maxlen=self.config.trail_len),
        )
        self.bodies.append(sun)

        for index, seed in enumerate(seeds, start=1):
            angle = math.radians(seed.angle_deg)
            radius = seed.radius
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            # Базовая орбитальная скорость в учебных единицах.
            orbital_speed = math.sqrt(max(0.0, self.g * self._simulation_mass(self.config.sun_mass) / max(radius, 1e-9)))
            tangential_angle = angle + math.pi / 2 + math.radians(seed.angle_velocity_bias_deg)

            # Касательная скорость + небольшой радиальный сдвиг для "живых" пресетов.
            vx = orbital_speed * seed.speed_scale * math.cos(tangential_angle) + seed.radial_bias * math.cos(angle)
            vy = orbital_speed * seed.speed_scale * math.sin(tangential_angle) + seed.radial_bias * math.sin(angle)
            color = seed.color or self._planet_color(index - 1)
            self.bodies.append(
                Body(
                    name=seed.name,
                    mass=self._body_mass(seed.name),
                    radius_px=self.config.planet_radius_px,
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    color=color,
                    trail=deque(maxlen=self.config.trail_len),
                    is_asteroid=False,
                )
            )

        if self.asteroid_belt_enabled:
            self._append_asteroid_belt()

        self._reset_histories()
        self.advance_metrics_history()

    def _append_asteroid_belt(self) -> None:
        # Фиксированный seed => воспроизводимая сцена при одинаковых параметрах.
        rng = random.Random(17)
        belt_inner, belt_outer = self._asteroid_belt_range()
        for asteroid_index in range(self.asteroid_belt_count):
            radius = rng.uniform(belt_inner, belt_outer)
            angle = rng.uniform(0.0, math.tau)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            orbital_speed = math.sqrt(max(0.0, self.g * self._simulation_mass(self.config.sun_mass) / max(radius, 1e-9)))
            tangential_angle = angle + math.pi / 2 + rng.uniform(-0.08, 0.08)
            speed_scale = rng.uniform(0.96, 1.05)
            vx = orbital_speed * speed_scale * math.cos(tangential_angle)
            vy = orbital_speed * speed_scale * math.sin(tangential_angle)
            color_shift = 150 + (asteroid_index % 3) * 18
            self.bodies.append(
                Body(
                    name=f"Астероид {asteroid_index + 1}",
                    mass=self.ASTEROID_MASS_EARTH,
                    radius_px=2,
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    color=(color_shift, color_shift, 170),
                    trail=deque(maxlen=64),
                    is_asteroid=True,
                )
            )

    def _asteroid_belt_range(self) -> tuple[float, float]:
        if self._asteroid_belt_range_override is not None:
            return self._asteroid_belt_range_override
        radii = sorted(
            math.hypot(body.x, body.y)
            for body in self.bodies[1:]
            if not body.is_asteroid
        )
        if len(radii) >= 2:
            # Пытаемся найти самый большой зазор между соседними орбитами
            # и разместить пояс именно там (нагляднее для урока).
            left, right, gap = max(
                (
                    (radii[index], radii[index + 1], radii[index + 1] - radii[index])
                    for index in range(len(radii) - 1)
                ),
                key=lambda item: (item[2], item[0]),
            )
            if gap >= 55.0:
                center = (left + right) * 0.5
                half_width = max(12.0, gap * 0.16)
                return center - half_width, center + half_width

        outermost = radii[-1] if radii else 220.0
        inner = outermost * 1.12
        outer = outermost * 1.22
        return inner, outer

    def _reset_histories(self) -> None:
        self._distance_history = {
            index: deque(maxlen=self.config.history_len) for index in range(1, self.num_planets + 1)
        }
        self._speed_history = {
            index: deque(maxlen=self.config.history_len) for index in range(1, self.num_planets + 1)
        }

    def _build_presets(self) -> dict[str, PresetDefinition]:
        # Базовый набор визуальных флагов для "демо" режима и "кино" режима.
        demo_defaults = RenderOptions(
            show_grid=True,
            show_trails=True,
            show_theory=False,
            show_labels=True,
            show_sparklines=True,
            label_zoom_threshold=0.65,
        )
        cinematic_defaults = RenderOptions(
            show_grid=False,
            show_trails=True,
            show_theory=False,
            show_labels=True,
            cinematic_mode=True,
            follow_selected=True,
            show_sparklines=True,
            label_zoom_threshold=0.75,
        )
        presets = [
            PresetDefinition(
                id="single-orbit",
                label="Одиночная орбита",
                description="Чистая демонстрация одной стабильной орбиты.",
                planet_count=1,
                initial_state=(BodySeed(name="Меркурий", radius=220.0, angle_deg=25.0),),
                selected_index=1,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="three-orbits",
                label="Три орбиты",
                description="Базовый showcase трёх планет на разных радиусах.",
                planet_count=3,
                initial_state=(
                    BodySeed(name="Меркурий", radius=120.0, angle_deg=15.0),
                    BodySeed(name="Венера", radius=220.0, angle_deg=130.0),
                    BodySeed(name="Земля", radius=320.0, angle_deg=240.0),
                ),
                selected_index=2,
                camera_mode="manual",
                render_defaults=demo_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="solar-system",
                label="Солнечная система",
                description="Шесть планет и плотный пояс астероидов между Марсом и Юпитером.",
                planet_count=6,
                initial_state=(
                    BodySeed(name="Меркурий", radius=110.0, angle_deg=8.0, speed_scale=1.03),
                    BodySeed(name="Венера", radius=160.0, angle_deg=62.0, speed_scale=1.01),
                    BodySeed(name="Земля", radius=220.0, angle_deg=132.0, speed_scale=1.00),
                    BodySeed(name="Марс", radius=290.0, angle_deg=210.0, speed_scale=0.98),
                    BodySeed(name="Юпитер", radius=470.0, angle_deg=285.0, speed_scale=1.00),
                    BodySeed(name="Сатурн", radius=620.0, angle_deg=338.0, speed_scale=0.97),
                ),
                selected_index=3,
                camera_mode="auto_frame",
                render_defaults=demo_defaults,
                gravity=1.0,
                asteroid_belt_enabled=True,
                asteroid_belt_count=120,
                asteroid_belt_inner_radius=340.0,
                asteroid_belt_outer_radius=410.0,
            ),
            PresetDefinition(
                id="planet-interactions",
                label="Влияние планет",
                description="Тяжёлые планеты на близких орбитах для сравнения режима Солнце / все тела.",
                planet_count=4,
                initial_state=(
                    BodySeed(name="Юпитер I", radius=180.0, angle_deg=0.0, speed_scale=1.00, color=(255, 117, 156)),
                    BodySeed(name="Юпитер II", radius=192.0, angle_deg=4.0, speed_scale=0.98, radial_bias=-0.10, color=(196, 222, 126)),
                    BodySeed(name="Сатурн", radius=290.0, angle_deg=208.0, speed_scale=1.01),
                    BodySeed(name="Земля", radius=360.0, angle_deg=302.0, speed_scale=0.99),
                ),
                selected_index=1,
                camera_mode="auto_frame",
                render_defaults=demo_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="chaos",
                label="Хаос",
                description="Небольшие возмущения скорости для более живой сцены.",
                planet_count=5,
                initial_state=(
                    BodySeed(name="Меркурий", radius=120.0, angle_deg=0.0, speed_scale=1.15),
                    BodySeed(name="Венера", radius=170.0, angle_deg=72.0, speed_scale=0.92),
                    BodySeed(name="Земля", radius=220.0, angle_deg=144.0, speed_scale=1.08),
                    BodySeed(name="Марс", radius=270.0, angle_deg=216.0, speed_scale=0.89),
                    BodySeed(name="Юпитер", radius=320.0, angle_deg=288.0, speed_scale=1.04),
                ),
                selected_index=3,
                camera_mode="manual",
                render_defaults=demo_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="close-approach",
                label="Сближение",
                description="Близкий пролёт с подчёркнутой динамикой.",
                planet_count=3,
                initial_state=(
                    BodySeed(name="Меркурий", radius=140.0, angle_deg=18.0, speed_scale=1.18),
                    BodySeed(name="Венера", radius=190.0, angle_deg=40.0, speed_scale=0.86, radial_bias=-0.6),
                    BodySeed(name="Земля", radius=310.0, angle_deg=240.0, speed_scale=1.03),
                ),
                selected_index=2,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="burst",
                label="Резкое ускорение",
                description="Одна планета получает заметный запас скорости.",
                planet_count=3,
                initial_state=(
                    BodySeed(name="Меркурий", radius=130.0, angle_deg=20.0),
                    BodySeed(name="Венера", radius=220.0, angle_deg=130.0, speed_scale=1.35),
                    BodySeed(name="Земля", radius=310.0, angle_deg=250.0),
                ),
                selected_index=2,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="near-escape",
                label="Почти вылет",
                description="Почти гиперболическая траектория.",
                planet_count=2,
                initial_state=(
                    BodySeed(name="Меркурий", radius=140.0, angle_deg=0.0, speed_scale=1.48),
                    BodySeed(name="Венера", radius=280.0, angle_deg=185.0, speed_scale=1.02),
                ),
                selected_index=1,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="spiral-in",
                label="Спираль к Солнцу",
                description="Недостаток скорости даёт падение на более узкую траекторию.",
                planet_count=3,
                initial_state=(
                    BodySeed(name="Меркурий", radius=120.0, angle_deg=30.0, speed_scale=0.82),
                    BodySeed(name="Венера", radius=210.0, angle_deg=140.0, speed_scale=0.94),
                    BodySeed(name="Земля", radius=300.0, angle_deg=255.0),
                ),
                selected_index=1,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="gravity-showcase",
                label="Показ влияния G",
                description="Повышенное G делает траектории плотнее и динамичнее.",
                planet_count=4,
                initial_state=(
                    BodySeed(name="Меркурий", radius=120.0, angle_deg=15.0),
                    BodySeed(name="Венера", radius=180.0, angle_deg=95.0),
                    BodySeed(name="Земля", radius=250.0, angle_deg=190.0),
                    BodySeed(name="Марс", radius=320.0, angle_deg=280.0),
                ),
                selected_index=3,
                camera_mode="auto_frame",
                render_defaults=demo_defaults,
                gravity=1.6,
            ),
            PresetDefinition(
                id="binary-showcase",
                label="Двойная дуга",
                description="Две внутренние орбиты для компактного и эффектного кадра.",
                planet_count=2,
                initial_state=(
                    BodySeed(name="Меркурий", radius=150.0, angle_deg=0.0, speed_scale=1.12),
                    BodySeed(name="Венера", radius=165.0, angle_deg=180.0, speed_scale=0.96),
                ),
                selected_index=1,
                camera_mode="auto_frame",
                render_defaults=demo_defaults,
                gravity=1.0,
            ),
            PresetDefinition(
                id="slingshot",
                label="Гравитационный манёвр",
                description="Внешняя орбита получает дополнительный импульс и проходит близко к центру.",
                planet_count=4,
                initial_state=(
                    BodySeed(name="Меркурий", radius=120.0, angle_deg=0.0),
                    BodySeed(name="Венера", radius=180.0, angle_deg=75.0),
                    BodySeed(name="Земля", radius=240.0, angle_deg=160.0, speed_scale=1.2),
                    BodySeed(name="Марс", radius=320.0, angle_deg=250.0, speed_scale=0.92),
                ),
                selected_index=3,
                camera_mode="follow_selected",
                render_defaults=cinematic_defaults,
                gravity=1.0,
            ),
        ]
        return {preset.id: preset for preset in presets}

    def _planet_color(self, index: int) -> ColorRGB:
        palette = [
            (107, 195, 255),
            (148, 158, 255),
            (109, 229, 186),
            (246, 156, 105),
            (255, 117, 156),
            (196, 222, 126),
            (130, 202, 255),
            (255, 195, 110),
            (186, 135, 255),
        ]
        return palette[index % len(palette)]

    def _body_name(self, index: int) -> str:
        if 0 <= index < len(self.BODY_NAMES):
            return self.BODY_NAMES[index]
        return f"Планета {index}"

    def _body_mass(self, name: str) -> float:
        return self.BODY_MASSES_EARTH.get(name, self.config.planet_mass)

    def _simulation_mass(self, mass_earth: float) -> float:
        return mass_earth * self.config.mass_to_sim_units

    def _accel_from_to(
        self,
        xi: float,
        yi: float,
        xj: float,
        yj: float,
        mass_j: float,
    ) -> tuple[float, float]:
        dx = xj - xi
        dy = yj - yi
        # Softening добавляет "смягчение" вблизи нулевой дистанции, чтобы не было взрывных ускорений.
        r2 = dx * dx + dy * dy + self.config.softening * self.config.softening
        inv_r = 1.0 / math.sqrt(r2)
        inv_r3 = inv_r * inv_r * inv_r
        scaled_mass = self._simulation_mass(mass_j)
        ax = self.g * scaled_mass * dx * inv_r3
        ay = self.g * scaled_mass * dy * inv_r3
        return ax, ay
