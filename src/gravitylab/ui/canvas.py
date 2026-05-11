from __future__ import annotations

import math
import random

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QBrush,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QRadialGradient,
    QWheelEvent,
)
from PyQt6.QtWidgets import QToolTip, QWidget

from ..sim.model import BodySnapshot, SimulationSnapshot
from ..theme import current_palette, qcolor


class SimulationCanvas(QWidget):
    """Канвас сцены: отрисовка системы, камера и взаимодействие мышью."""

    body_selected = pyqtSignal(int)
    zoom_changed = pyqtSignal(float)
    manual_camera_interacted = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumWidth(620)
        self.snapshot_data: SimulationSnapshot | None = None
        # offset_* задаёт сдвиг камеры в мировых координатах.
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0
        # zoom и target_zoom используются для плавного перехода в cinematic-режимах.
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.drag_active = False
        self.last_drag_pos = QPoint()
        self._stars = self._build_stars()
        self._camera_initialized = False

    def set_snapshot(self, snapshot: SimulationSnapshot) -> None:
        # На каждом кадре получаем новый "снимок" сцены из модели.
        self.snapshot_data = snapshot
        self._update_camera_targets(snapshot)
        self._advance_camera(snapshot)
        self.update()

    def reset_view(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0
        self.set_zoom(1.0)

    def fit_to_scene(self) -> None:
        if not self.snapshot_data or not self.snapshot_data.bodies:
            self.reset_view()
            return
        self._set_fit_targets(self.snapshot_data)
        self.offset_x = self.target_offset_x
        self.offset_y = self.target_offset_y
        self.set_zoom(self.target_zoom)

    def center_on_body_index(self, index: int) -> None:
        if not self.snapshot_data or index >= len(self.snapshot_data.bodies):
            return
        body = self.snapshot_data.bodies[index]
        self.offset_x = -body.x
        self.offset_y = -body.y
        self.target_offset_x = self.offset_x
        self.target_offset_y = self.offset_y
        self.update()

    def export_screenshot(self, path: str) -> bool:
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        return pixmap.save(path, "PNG")

    def world_to_screen(self, x: float, y: float) -> QPointF:
        # Перевод из физических координат в пиксели окна.
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
        return QPointF(center_x + (x + self.offset_x) * self.zoom, center_y + (y + self.offset_y) * self.zoom)

    def screen_to_world(self, point: QPointF) -> tuple[float, float]:
        # Обратное преобразование: из пикселей обратно в координаты модели.
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
        world_x = (point.x() - center_x) / self.zoom - self.offset_x
        world_y = (point.y() - center_y) / self.zoom - self.offset_y
        return world_x, world_y

    def body_screen_point(self, index: int) -> QPoint:
        if not self.snapshot_data or index >= len(self.snapshot_data.bodies):
            return QPoint()
        point = self.world_to_screen(self.snapshot_data.bodies[index].x, self.snapshot_data.bodies[index].y)
        return QPoint(int(point.x()), int(point.y()))

    def set_zoom(self, zoom: float, emit_signal: bool = True) -> None:
        clamped = max(0.2, min(4.0, zoom))
        self.zoom = clamped
        self.target_zoom = clamped
        if emit_signal:
            self.zoom_changed.emit(clamped)
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        # Порядок рендера важен: фон -> сетка -> следы -> тела -> оверлеи.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._paint_background(painter)
        if self.snapshot_data is None:
            painter.end()
            return
        if self.snapshot_data.render_options.show_grid:
            self._paint_grid(painter)
        self._paint_orbit_hint(painter)
        if self.snapshot_data.render_options.show_trails:
            self._paint_trails(painter)
        self._paint_bodies(painter)
        if self.snapshot_data.render_options.clean_ui:
            self._paint_clean_badge(painter)
        painter.end()

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 1.12 if delta > 0 else 0.9
        # Масштабируем относительно курсора, а не центра экрана.
        mouse_world_before = self.screen_to_world(event.position())
        self.set_zoom(self.zoom * factor)
        mouse_world_after = self.screen_to_world(event.position())
        self.offset_x += mouse_world_after[0] - mouse_world_before[0]
        self.offset_y += mouse_world_after[1] - mouse_world_before[1]
        self.target_offset_x = self.offset_x
        self.target_offset_y = self.offset_y
        self.manual_camera_interacted.emit()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            body = self._body_at_point(event.position())
            if body:
                # Клик по телу меняет выделение в главном окне.
                self.body_selected.emit(body.index)
                return
            # Клик по пустому месту запускает ручной "drag camera".
            self.drag_active = True
            self.last_drag_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag_active:
            # При перетаскивании двигаем камеру в мировых координатах.
            delta = event.pos() - self.last_drag_pos
            self.offset_x += delta.x() / self.zoom
            self.offset_y += delta.y() / self.zoom
            self.target_offset_x = self.offset_x
            self.target_offset_y = self.offset_y
            self.last_drag_pos = event.pos()
            self.manual_camera_interacted.emit()
            self.update()
            return

        body = self._body_at_point(event.position())
        if body:
            # Всплывающая подсказка для быстрого чтения параметров тела.
            distance = math.hypot(body.x, body.y)
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"{body.name}\nСкорость: {math.hypot(body.vx, body.vy):.2f}\nРасстояние до Солнца: {distance:.1f} ед.",
                self,
            )
        else:
            QToolTip.hideText()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_active = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        body = self._body_at_point(event.position())
        if body and body.index == 0:
            self.reset_view()

    def _build_stars(self) -> list[tuple[float, float, float, float]]:
        rng = random.Random(7)
        return [
            (rng.random(), rng.random(), rng.uniform(0.5, 1.9), rng.uniform(0.10, 0.50))
            for _ in range(116)
        ]

    def _update_camera_targets(self, snapshot: SimulationSnapshot) -> None:
        if not self._camera_initialized:
            # При первом кадре синхронизируемся с zoom из модели.
            self.target_zoom = snapshot.render_options.zoom
            self.zoom = snapshot.render_options.zoom
            self._camera_initialized = True

        if snapshot.camera_mode == "follow_sun":
            self.target_offset_x = -snapshot.bodies[0].x
            self.target_offset_y = -snapshot.bodies[0].y
            return
        if snapshot.camera_mode == "follow_selected" and snapshot.follow_target_index is not None:
            target = snapshot.bodies[snapshot.follow_target_index]
            self.target_offset_x = -target.x
            self.target_offset_y = -target.y
            return
        if snapshot.camera_mode == "auto_frame":
            self._set_fit_targets(snapshot)

    def _set_fit_targets(self, snapshot: SimulationSnapshot) -> None:
        # Рассчитываем прямоугольник, который покрывает все тела.
        xs = [body.x for body in snapshot.bodies]
        ys = [body.y for body in snapshot.bodies]
        if not xs or not ys:
            self.target_offset_x = 0.0
            self.target_offset_y = 0.0
            self.target_zoom = snapshot.render_options.zoom
            return
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5
        width = max(1.0, max_x - min_x)
        height = max(1.0, max_y - min_y)
        self.target_offset_x = -center_x
        self.target_offset_y = -center_y
        margin = 180.0
        avail_w = max(80.0, self.width() - margin)
        avail_h = max(80.0, self.height() - margin)
        # Ограничиваем zoom, чтобы не получить слишком "далеко" или слишком "близко".
        self.target_zoom = max(0.35, min(2.6, min(avail_w / width, avail_h / height)))

    def _advance_camera(self, snapshot: SimulationSnapshot) -> None:
        if snapshot.render_options.cinematic_mode or snapshot.camera_mode != "manual":
            # Плавное приближение к target-координатам камеры (easing).
            blend = 0.16
            self.offset_x += (self.target_offset_x - self.offset_x) * blend
            self.offset_y += (self.target_offset_y - self.offset_y) * blend
            self.zoom += (self.target_zoom - self.zoom) * 0.12
        else:
            self.target_zoom = snapshot.render_options.zoom

    def _paint_background(self, painter: QPainter) -> None:
        palette = current_palette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, qcolor(palette.canvas_top))
        gradient.setColorAt(0.36, qcolor(palette.canvas_mid))
        gradient.setColorAt(1.0, qcolor(palette.canvas_bottom))
        painter.fillRect(self.rect(), gradient)

        left_nebula = QRadialGradient(self.width() * 0.16, self.height() * 0.22, self.width() * 0.48)
        left_nebula.setColorAt(0.0, qcolor(palette.canvas_nebula_left))
        left_nebula.setColorAt(0.42, qcolor(palette.canvas_nebula_left_soft))
        left_nebula.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), left_nebula)

        right_nebula = QRadialGradient(self.width() * 0.74, self.height() * 0.18, self.width() * 0.56)
        right_nebula.setColorAt(0.0, qcolor(palette.canvas_nebula_right))
        right_nebula.setColorAt(0.45, qcolor(palette.canvas_nebula_right_soft))
        right_nebula.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), right_nebula)

        horizon_glow = QRadialGradient(self.width() * 0.50, self.height() * 0.86, self.width() * 0.72)
        horizon_glow.setColorAt(0.0, QColor(255, 255, 255, 34) if palette.canvas_top.startswith("#e") else QColor(96, 163, 235, 26))
        horizon_glow.setColorAt(0.36, QColor(255, 255, 255, 16) if palette.canvas_top.startswith("#e") else QColor(96, 163, 235, 12))
        horizon_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), horizon_glow)

        top_mist = QLinearGradient(0, 0, 0, self.height() * 0.32)
        top_mist.setColorAt(0.0, QColor(255, 255, 255, 18) if palette.canvas_top.startswith("#e") else QColor(255, 255, 255, 6))
        top_mist.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(QRectF(0, 0, self.width(), self.height() * 0.36), top_mist)

        vignette = QRadialGradient(self.width() * 0.50, self.height() * 0.50, self.width() * 0.78)
        vignette.setColorAt(0.72, QColor(0, 0, 0, 0))
        vignette.setColorAt(1.0, QColor(8, 12, 20, 36) if not palette.canvas_top.startswith("#e") else QColor(70, 110, 160, 32))
        painter.fillRect(self.rect(), vignette)

        for x_ratio, y_ratio, radius, alpha in self._stars:
            color = qcolor(palette.canvas_star)
            color.setAlpha(int(alpha * 155))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(self.width() * x_ratio, self.height() * y_ratio), radius, radius)
            if radius > 1.72:
                halo = QColor(color)
                halo.setAlpha(max(8, int(color.alpha() * 0.22)))
                painter.setBrush(halo)
                painter.drawEllipse(QPointF(self.width() * x_ratio, self.height() * y_ratio), radius * 1.55, radius * 1.55)

    def _paint_grid(self, painter: QPainter) -> None:
        if not self.snapshot_data:
            return
        world_step = self._adaptive_grid_step()
        left_world, top_world = self.screen_to_world(QPointF(0.0, 0.0))
        right_world, bottom_world = self.screen_to_world(QPointF(self.width(), self.height()))
        start_x = math.floor(left_world / world_step) * world_step
        start_y = math.floor(top_world / world_step) * world_step

        palette = current_palette()
        painter.setPen(QPen(qcolor(palette.grid_minor), 1))
        x = start_x
        while x <= right_world:
            point = self.world_to_screen(x, 0.0)
            painter.drawLine(int(point.x()), 0, int(point.x()), self.height())
            x += world_step
        y = start_y
        while y <= bottom_world:
            point = self.world_to_screen(0.0, y)
            painter.drawLine(0, int(point.y()), self.width(), int(point.y()))
            y += world_step

        painter.setPen(QPen(qcolor(palette.grid_major), 1))
        origin = self.world_to_screen(0.0, 0.0)
        painter.drawLine(int(origin.x()), 0, int(origin.x()), self.height())
        painter.drawLine(0, int(origin.y()), self.width(), int(origin.y()))

    def _paint_orbit_hint(self, painter: QPainter) -> None:
        if not self.snapshot_data:
            return
        selected = self.snapshot_data.bodies[self.snapshot_data.selected_index]
        if len(selected.trail) < 12:
            return
        points = [self.world_to_screen(x, y) for x, y in selected.trail[-28:]]
        painter.setPen(QPen(QColor(108, 188, 255, 156), 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for index in range(1, len(points)):
            painter.drawLine(points[index - 1], points[index])

    def _paint_trails(self, painter: QPainter) -> None:
        if not self.snapshot_data:
            return
        max_alpha = self.snapshot_data.render_options.trail_alpha
        for body in self.snapshot_data.bodies:
            if len(body.trail) < 2:
                continue
            render_points = body.trail
            if len(render_points) > 280:
                # Для длинных хвостов делаем прореживание, чтобы не перегружать кадр.
                stride = 2 if body.index == self.snapshot_data.selected_index else 3
                render_points = render_points[::stride]
            points = [self.world_to_screen(x, y) for x, y in render_points]
            base_width = 1.22 if body.index == self.snapshot_data.selected_index else 0.78
            draw_glow = body.index == self.snapshot_data.selected_index and not body.is_asteroid
            for index in range(1, len(points)):
                trail_progress = index / len(points)
                alpha = max(8, int(max_alpha * (trail_progress ** 1.55)))
                color = QColor(*body.color)
                color.setAlpha(alpha)
                width = base_width + trail_progress * (0.28 if body.index == self.snapshot_data.selected_index else 0.18)
                if draw_glow:
                    glow = QColor(color)
                    glow.setAlpha(max(5, int(alpha * 0.18)))
                    painter.setPen(QPen(glow, width * 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    painter.drawLine(points[index - 1], points[index])
                painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(points[index - 1], points[index])

    def _paint_bodies(self, painter: QPainter) -> None:
        if not self.snapshot_data:
            return
        occupied_label_rects: list[QRectF] = []
        bodies = list(self.snapshot_data.bodies)
        # Сначала подписываем важные тела, чтобы им проще было найти место без пересечений.
        label_bodies = sorted(
            [body for body in bodies[1:] if not body.is_asteroid],
            key=lambda body: (
                body.index != self.snapshot_data.selected_index,
                math.hypot(self.world_to_screen(body.x, body.y).x() - self.width() * 0.5, self.world_to_screen(body.x, body.y).y() - self.height() * 0.5),
            ),
        )

        for body in bodies:
            center = self.world_to_screen(body.x, body.y)
            radius = max(3.2, body.radius_px * self.zoom * 0.34)

            if body.index == self.snapshot_data.selected_index and not body.is_asteroid:
                self._paint_glow(painter, body, center)

            if body.index == 0:
                solar_glow_far = QRadialGradient(center, radius * 5.4)
                solar_glow_far.setColorAt(0.0, QColor(255, 233, 168, 80))
                solar_glow_far.setColorAt(0.32, QColor(255, 196, 116, 46))
                solar_glow_far.setColorAt(1.0, QColor(255, 144, 0, 0))
                painter.setBrush(QBrush(solar_glow_far))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, radius * 4.2, radius * 4.2)

                solar_glow = QRadialGradient(center, radius * 3.9)
                solar_glow.setColorAt(0.0, QColor(255, 243, 196, 240))
                solar_glow.setColorAt(0.36, QColor(255, 201, 112, 128))
                solar_glow.setColorAt(1.0, QColor(255, 144, 0, 0))
                painter.setBrush(QBrush(solar_glow))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, radius * 3.4, radius * 3.4)

                solar_core = QRadialGradient(center, radius * 1.15)
                solar_core.setColorAt(0.0, QColor(255, 251, 232, 255))
                solar_core.setColorAt(0.42, QColor(255, 228, 124, 252))
                solar_core.setColorAt(1.0, QColor(244, 184, 42, 255))
                painter.setBrush(QBrush(solar_core))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, radius * 1.03, radius * 1.03)

                painter.setBrush(QColor(255, 255, 255, 52))
                painter.drawEllipse(QPointF(center.x() - radius * 0.22, center.y() - radius * 0.22), radius * 0.30, radius * 0.30)
                continue

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(*body.color)))
            painter.drawEllipse(center, radius, radius)

            if body.index == self.snapshot_data.selected_index and not body.is_asteroid:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 230), 1.8))
                painter.drawEllipse(center, radius + 7, radius + 7)

        if self.zoom >= self.snapshot_data.render_options.label_zoom_threshold and self.snapshot_data.render_options.show_labels:
            for body in label_bodies:
                center = self.world_to_screen(body.x, body.y)
                radius = max(3.2, body.radius_px * self.zoom * 0.34)
                self._paint_body_label(painter, body, center, radius, occupied_label_rects)

    def _paint_glow(self, painter: QPainter, body: BodySnapshot, center: QPointF) -> None:
        radius = max(12.0, body.radius_px * self.zoom * 0.9)
        glow = QRadialGradient(center, radius * 2.6)
        glow.setColorAt(0.0, QColor(108, 188, 255, 125))
        glow.setColorAt(1.0, QColor(108, 188, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(center, radius * 2.2, radius * 2.2)

    def _paint_clean_badge(self, painter: QPainter) -> None:
        if not self.snapshot_data:
            return
        palette = current_palette()
        badge_rect = QRectF(18.0, 18.0, 300.0, 44.0)
        painter.setBrush(qcolor(palette.clean_badge_bg))
        painter.setPen(QPen(qcolor(palette.clean_badge_border), 1))
        painter.drawRoundedRect(badge_rect, 16, 16)
        painter.setPen(qcolor(palette.clean_badge_text))
        painter.drawText(
            badge_rect.adjusted(14.0, 0.0, -14.0, 0.0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"{'Пауза' if self.snapshot_data.paused else 'Live'}  |  {self.snapshot_data.active_preset or 'Свободная сцена'}",
        )

    def _adaptive_grid_step(self) -> float:
        candidate_steps = (25, 50, 100, 150, 200, 400, 800)
        for step in candidate_steps:
            pixels = step * self.zoom
            if 42 <= pixels <= 130:
                return float(step)
        return 800.0

    def _body_at_point(self, point: QPointF) -> BodySnapshot | None:
        if not self.snapshot_data:
            return None
        for body in reversed(self.snapshot_data.bodies):
            if body.is_asteroid:
                continue
            center = self.world_to_screen(body.x, body.y)
            radius = max(10.0, body.radius_px * self.zoom * 0.58)
            if math.hypot(point.x() - center.x(), point.y() - center.y()) <= radius:
                return body
        return None

    def _paint_body_label(
        self,
        painter: QPainter,
        body: BodySnapshot,
        center: QPointF,
        radius: float,
        occupied_rects: list[QRectF],
    ) -> None:
        if self.snapshot_data is None or not painter.isActive():
            return
        palette = current_palette()
        label_font = QFont(painter.font())
        label_font.setPointSize(9 if self.zoom < 1.25 else 10)
        label_font.setWeight(QFont.Weight.DemiBold if body.index == self.snapshot_data.selected_index else QFont.Weight.Medium)
        painter.setFont(label_font)

        metrics = painter.fontMetrics()
        label = body.name
        padding_x = 11
        padding_y = 4
        label_width = metrics.horizontalAdvance(label) + padding_x * 2
        label_height = metrics.height() + padding_y * 2
        rect = self._label_rect(center, radius, label_width, label_height, occupied_rects)

        anchor_x = rect.x() if rect.center().x() > center.x() else rect.x() + rect.width()
        line_start = QPointF(center.x(), center.y())
        line_mid = QPointF(center.x() + (anchor_x - center.x()) * 0.34, center.y())
        line_end = QPointF(anchor_x, rect.center().y())
        connector = qcolor(palette.label_connector)
        if body.index == self.snapshot_data.selected_index:
            connector.setAlpha(min(255, connector.alpha() + 46))
        painter.setPen(QPen(connector, 1.35 if body.index == self.snapshot_data.selected_index else 1.0))
        painter.drawLine(line_start, line_mid)
        painter.drawLine(line_mid, line_end)
        painter.setBrush(connector)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 1.8, 1.8)

        shadow_rect = rect.translated(0.0, 2.0)
        painter.setBrush(QColor(0, 0, 0, 18 if palette.canvas_top.startswith("#e") else 42))
        painter.drawRoundedRect(shadow_rect, 10, 10)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        border = qcolor(palette.border_strong if body.index == self.snapshot_data.selected_index else palette.border)
        border.setAlpha(min(255, border.alpha() + 18))
        painter.setPen(QPen(border, 1.0))
        bg = qcolor(palette.label_bg_selected if body.index == self.snapshot_data.selected_index else palette.label_bg)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, 10, 10)

        painter.setPen(
            qcolor(palette.label_text_selected if body.index == self.snapshot_data.selected_index else palette.label_text)
        )
        text_rect = rect.adjusted(padding_x - 1, 0, -(padding_x - 1), 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, label)
        occupied_rects.append(rect.adjusted(-8, -5, 8, 5))

    def _label_rect(
        self,
        center: QPointF,
        radius: float,
        label_width: float,
        label_height: float,
        occupied_rects: list[QRectF],
    ) -> QRectF:
        gap = 14.0
        right_x = center.x() + radius + gap
        left_x = center.x() - radius - gap - label_width
        top_y = center.y() - radius - gap - label_height
        bottom_y = center.y() + radius + gap
        mid_y = center.y() - label_height * 0.5

        prefer_left = center.x() > self.width() * 0.56
        prefer_top = center.y() > self.height() * 0.52

        candidates = []
        if prefer_left:
            candidates.extend(
                [
                    QRectF(left_x, mid_y, label_width, label_height),
                    QRectF(left_x, top_y, label_width, label_height),
                    QRectF(left_x, bottom_y, label_width, label_height),
                ]
            )
        else:
            candidates.extend(
                [
                    QRectF(right_x, mid_y, label_width, label_height),
                    QRectF(right_x, top_y, label_width, label_height),
                    QRectF(right_x, bottom_y, label_width, label_height),
                ]
            )

        if prefer_top:
            candidates.append(QRectF(center.x() - label_width * 0.5, top_y, label_width, label_height))
            candidates.append(QRectF(center.x() - label_width * 0.5, bottom_y, label_width, label_height))
        else:
            candidates.append(QRectF(center.x() - label_width * 0.5, bottom_y, label_width, label_height))
            candidates.append(QRectF(center.x() - label_width * 0.5, top_y, label_width, label_height))

        for rect in candidates:
            fitted = self._clamp_rect(rect)
            # Берём первое положение подписи, которое не пересекается с уже занятыми.
            if not any(fitted.intersects(existing) for existing in occupied_rects):
                return fitted

        fallback = self._clamp_rect(candidates[0])
        shift_step = label_height + 10.0
        for direction in (-1, 1, -2, 2, -3, 3):
            shifted = self._clamp_rect(fallback.translated(0.0, direction * shift_step))
            if not any(shifted.intersects(existing) for existing in occupied_rects):
                return shifted
        return fallback

    def _clamp_rect(self, rect: QRectF) -> QRectF:
        margin = 12.0
        x = min(max(rect.x(), margin), max(margin, self.width() - rect.width() - margin))
        y = min(max(rect.y(), margin), max(margin, self.height() - rect.height() - margin))
        return QRectF(x, y, rect.width(), rect.height())
