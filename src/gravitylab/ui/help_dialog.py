from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..sim.model import PresetDefinition
from ..theme import current_palette, qcolor


PRESET_GUIDE: dict[str, dict[str, str]] = {
    "single-orbit": {
        "goal": "Показать устойчивую орбиту при удачно подобранной скорости.",
        "observe": "Следите за почти постоянным расстоянием до Солнца и ровной траекторией.",
        "change": "Измените скорость и посмотрите, когда круг начинает вытягиваться в эллипс.",
        "conclusion": "Для устойчивой орбиты важен баланс между скоростью тела и притяжением звезды.",
    },
    "three-orbits": {
        "goal": "Сравнить движение нескольких тел на разных радиусах.",
        "observe": "Внутренние тела движутся быстрее, а внешние проходят орбиту медленнее.",
        "change": "Меняйте массу, скорость и G, чтобы увидеть, как система становится более или менее устойчивой.",
        "conclusion": "Чем ближе тело к Солнцу, тем быстрее оно должно двигаться для удержания орбиты.",
    },
    "solar-system": {
        "goal": "Показать упрощённую модель Солнечной системы и пояс астероидов между Марсом и Юпитером.",
        "observe": "Смотрите на разницу скоростей внутренних и внешних планет, а также на поведение астероидов.",
        "change": "Попробуйте менять плотность пояса, G и режим «Только притяжение Солнца».",
        "conclusion": "Даже упрощённая многотельная система показывает, что орбиты и возмущения зависят от взаимного влияния тел.",
    },
    "chaos": {
        "goal": "Показать, как небольшие изменения скоростей делают систему менее регулярной.",
        "observe": "Сравнивайте форму следов и степень расхождения орбит со временем.",
        "change": "Уменьшите или увеличьте скорость отдельных планет и наблюдайте усиление хаоса.",
        "conclusion": "Даже маленькие изменения начальных условий могут заметно изменить развитие системы.",
    },
    "close-approach": {
        "goal": "Показать влияние близкого пролёта тел на траекторию.",
        "observe": "Смотрите, как орбита вытягивается и меняется после сближения.",
        "change": "Измените массу и скорость выбранной планеты, чтобы усилить или ослабить эффект возмущения.",
        "conclusion": "При близком прохождении взаимное тяготение сильнее меняет направление и форму орбиты.",
    },
    "burst": {
        "goal": "Показать, как избыток начальной скорости меняет орбиту.",
        "observe": "Одна из планет заметно уходит на более вытянутую траекторию.",
        "change": "Снизьте скорость до более умеренного значения и сравните форму орбиты.",
        "conclusion": "Чем больше скорость относительно нужной круговой, тем сильнее орбита вытягивается.",
    },
    "near-escape": {
        "goal": "Показать состояние, близкое к вылету из системы.",
        "observe": "Следите, как тело уходит всё дальше и орбита становится почти открытой.",
        "change": "Немного уменьшите скорость и посмотрите, вернётся ли траектория к связанной орбите.",
        "conclusion": "При слишком большой скорости тело может почти покинуть систему.",
    },
    "spiral-in": {
        "goal": "Показать, что недостаток скорости ведёт к смещению орбиты ближе к Солнцу.",
        "observe": "Орбита становится более узкой и стремится внутрь.",
        "change": "Постепенно поднимайте скорость и сравнивайте переход от падения к устойчивой орбите.",
        "conclusion": "Если скорость мала, притяжение преобладает и тело смещается к центру системы.",
    },
    "gravity-showcase": {
        "goal": "Показать влияние параметра G на движение всей системы.",
        "observe": "С ростом G тела проходят орбиты быстрее и сильнее реагируют на возмущения.",
        "change": "Сравните этот пресет с обычным режимом при G = 1.0.",
        "conclusion": "При увеличении силы притяжения система становится более динамичной и чувствительной к массе тел.",
    },
    "binary-showcase": {
        "goal": "Показать компактную сцену с двумя близкими орбитами.",
        "observe": "Сравните скорости двух тел на близких радиусах.",
        "change": "Измените массу одного тела и посмотрите, как изменятся возмущения.",
        "conclusion": "Даже близкие по радиусу орбиты могут вести себя по-разному из-за скоростей и масс.",
    },
    "slingshot": {
        "goal": "Показать эффект гравитационного манёвра в учебно-упрощённом виде.",
        "observe": "Следите за изменением формы орбиты после прохождения рядом с другим телом.",
        "change": "Меняйте скорость и массу выбранной планеты, чтобы наблюдать усиление манёвра.",
        "conclusion": "Близкое прохождение рядом с массивным телом может заметно изменить траекторию.",
    },
}


class PresetPreviewWidget(QWidget):
    def __init__(self, preset: PresetDefinition, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.preset = preset
        self.setMinimumSize(220, 150)

    def paintEvent(self, _event) -> None:
        palette = current_palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), qcolor(palette.card_alt))

        center_x = self.width() * 0.5
        center_y = self.height() * 0.55
        max_radius = max((seed.radius for seed in self.preset.initial_state), default=1.0)
        scale = min(self.width(), self.height()) * 0.32 / max_radius

        painter.setPen(QPen(qcolor(palette.grid_minor), 1))
        for seed in self.preset.initial_state:
            orbit_radius = seed.radius * scale
            painter.drawEllipse(
                int(center_x - orbit_radius),
                int(center_y - orbit_radius),
                int(orbit_radius * 2),
                int(orbit_radius * 2),
            )

        if self.preset.asteroid_belt_enabled:
            belt_inner = self.preset.asteroid_belt_inner_radius or max_radius * 0.62
            belt_outer = self.preset.asteroid_belt_outer_radius or max_radius * 0.72
            asteroid_count = self.preset.asteroid_belt_count or 80
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(qcolor("rgba(132, 156, 184, 0.70)"))
            for asteroid_index in range(min(asteroid_count, 140)):
                angle = asteroid_index * 0.41
                ratio = (asteroid_index % 11) / 10.0
                radius = (belt_inner + (belt_outer - belt_inner) * ratio) * scale
                x = center_x + math.cos(angle) * radius
                y = center_y + math.sin(angle) * radius
                painter.drawEllipse(int(x - 1), int(y - 1), 2, 2)

        sun_color = QColor(255, 207, 79)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(sun_color)
        painter.drawEllipse(int(center_x - 12), int(center_y - 12), 24, 24)

        for index, seed in enumerate(self.preset.initial_state, start=1):
            angle = math.radians(seed.angle_deg)
            x = center_x + math.cos(angle) * seed.radius * scale
            y = center_y + math.sin(angle) * seed.radius * scale
            color = QColor(*(seed.color or (76 + index * 20, 140 + index * 8, 220 - index * 10)))
            painter.setBrush(color)
            painter.drawEllipse(int(x - 5), int(y - 5), 10, 10)

        painter.end()


class PresetCard(QFrame):
    def __init__(self, preset: PresetDefinition, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel(preset.label)
        title.setObjectName("sectionTitle")
        title.setWordWrap(True)
        text = QLabel(preset.description)
        text.setObjectName("mutedText")
        text.setWordWrap(True)
        notes = PRESET_GUIDE.get(
            preset.id,
            {
                "goal": "Готовая сцена для наблюдения за движением тел.",
                "observe": "Следите за формой орбит, скоростью и расстоянием до Солнца.",
                "change": "Меняйте скорость, массу и G, чтобы исследовать поведение системы.",
                "conclusion": "Параметры движения и притяжения напрямую влияют на форму траектории.",
            },
        )
        meta = QLabel(
            f"Тел: {preset.planet_count}\n"
            f"Камера: {preset.camera_mode}\n"
            f"G: {preset.gravity if preset.gravity is not None else 1.00:.2f}\n"
            f"Время: {preset.time_scale if preset.time_scale is not None else 1.0:.2f}x\n"
            f"Пояс: {'да' if preset.asteroid_belt_enabled else 'нет'}"
        )
        meta.setWordWrap(True)
        teaching = QLabel(
            f"<b>Что показывает</b><br>{notes['goal']}<br><br>"
            f"<b>На что смотреть</b><br>{notes['observe']}<br><br>"
            f"<b>Что попробовать изменить</b><br>{notes['change']}<br><br>"
            f"<b>Какой вывод можно сделать</b><br>{notes['conclusion']}"
        )
        teaching.setObjectName("mutedText")
        teaching.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(PresetPreviewWidget(preset))
        layout.addWidget(text)
        layout.addWidget(meta)
        layout.addWidget(teaching)


class HelpDialog(QDialog):
    def __init__(self, presets: tuple[PresetDefinition, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Справка GravityLab")
        self.resize(980, 760)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Справка GravityLab")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Подробное описание программы, физической модели, готовых сцен и способов использования GravityLab на уроке и при самостоятельном изучении."
        )
        subtitle.setObjectName("mutedText")
        subtitle.setWordWrap(True)
        self.author_label = self._author_block()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._overview_tab(), "Программа")
        self.tabs.addTab(self._physics_tab(), "Физика")
        self.tabs.addTab(self._presets_tab(presets), "Пресеты")
        self.tabs.addTab(self._shortcuts_tab(), "Управление")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.author_label)
        layout.addWidget(self.tabs, 1)

    def _overview_tab(self) -> QWidget:
        return self._html_browser(
            """
            <h2>Что делает GravityLab</h2>
            <p><b>GravityLab</b> — это интерактивная 2D-модель гравитационной системы, в которой можно наблюдать орбиты тел вокруг Солнца,
            сравнивать разные режимы движения и изучать влияние скорости, массы и силы притяжения на форму траектории.</p>

            <h3>Назначение программы</h3>
            <ul>
              <li>Наглядно показывать движение тел под действием гравитации.</li>
              <li>Давать возможность быстро проводить учебные эксперименты без сложных вычислений вручную.</li>
              <li>Помогать сравнивать разные сценарии: устойчивые орбиты, хаос, почти вылет, падение к Солнцу, пояс астероидов.</li>
              <li>Служить цифровой лабораторной работой или демонстрацией на уроке физики и астрономии.</li>
            </ul>

            <h3>Из чего состоит интерфейс</h3>
            <ul>
              <li><b>Левая панель</b> — настройки самой сцены: число тел, G, масштаб времени, отображение и готовые пресеты.</li>
              <li><b>Центральная область</b> — главная сцена с телами, следами, сеткой, подписями и управлением камерой.</li>
              <li><b>Правая панель</b> — подробные параметры выбранного тела, его масса, скорость, расстояние до Солнца и история изменений.</li>
              <li><b>Верхняя панель</b> — быстрые действия: пауза, сброс, подгонка сцены, снимок, тема, справка и режим камеры.</li>
              <li><b>Нижняя панель</b> — управление ходом эксперимента и быстрый выбор масштаба времени.</li>
            </ul>

            <h3>Что можно менять</h3>
            <ul>
              <li>Количество основных планет.</li>
              <li>Силу притяжения <b>G</b>.</li>
              <li>Масштаб времени.</li>
              <li>Скорость и массу выбранного тела.</li>
              <li>Наличие и плотность пояса астероидов.</li>
              <li>Режим <b>Только притяжение Солнца</b>, который отключает взаимное влияние планет.</li>
            </ul>

            <h3>Что наблюдать</h3>
            <ul>
              <li>Форму орбит: круговая, вытянутая, спиральная, почти открытая.</li>
              <li>Изменение расстояния до Солнца.</li>
              <li>Изменение скорости тела на разных участках траектории.</li>
              <li>Влияние массы и взаимного притяжения на соседние тела.</li>
              <li>Разницу между спокойной системой и хаотическим режимом.</li>
            </ul>

            <h3>Как использовать на уроке</h3>
            <p>GravityLab удобно применять как демонстрацию или как мини-лабораторную работу. Учитель может выбрать пресет,
            поставить вопрос, предложить изменить один параметр и попросить учеников сформулировать вывод по наблюдаемым изменениям.</p>

            <h3>Ограничения модели</h3>
            <ul>
              <li>Это учебная, а не профессиональная астрономическая модель.</li>
              <li>Расстояния и скорости нормализованы для удобства наблюдения.</li>
              <li>Параметр <b>G</b> используется в учебном масштабе и служит для экспериментов, а не для прямого воспроизведения системы SI.</li>
              <li>Орбиты рассчитаны так, чтобы быть наглядными и устойчивыми в интерфейсе.</li>
              <li>Массы тел показываются в массах Земли, чтобы их было удобно сравнивать между собой.</li>
            </ul>

            <h3>Автор</h3>
            <p><b>Рыльцин Тимур</b>, 10А, МОУ СОШ №22.</p>
            """
        )

    def _physics_tab(self) -> QWidget:
        return self._html_browser(
            """
            <h2>Физическая модель</h2>
            <p>В основе GravityLab лежит учебная модель движения тел под действием гравитации. Она достаточно проста, чтобы быть понятной,
            и при этом достаточно выразительна, чтобы показывать реальные закономерности орбитального движения.</p>

            <h3>Основные формулы</h3>
            <p>Система подчиняется закону всемирного тяготения Ньютона:</p>
            <pre>F = G * m1 * m2 / r²</pre>
            <p>Для кругового движения вокруг центрального тела можно ориентироваться на орбитальную скорость:</p>
            <pre>v_orb = sqrt(G * M / r)</pre>

            <h3>Как интерпретировать параметры</h3>
            <ul>
              <li><b>G</b> — учебно-нормализованная сила притяжения. Чем она выше, тем сильнее тела ускоряются к Солнцу и друг к другу.</li>
              <li><b>Масса</b> — задаётся в <b>массах Земли (M⊕)</b>. Это позволяет удобно сравнивать планеты между собой.</li>
              <li><b>Масса Солнца</b> тоже выражена в массах Земли, поэтому в справке и инспекторе все тела показаны в одной системе единиц.</li>
              <li><b>Расстояние</b> в сцене показано в учебных единицах, а не в километрах или астрономических единицах.</li>
              <li><b>Масштаб времени</b> ускоряет или замедляет развитие сцены без изменения её структуры.</li>
              <li><b>Следы</b> помогают видеть форму траектории и сравнивать разные режимы.</li>
            </ul>

            <h3>Что происходит при изменении скорости</h3>
            <p>Если скорость увеличить, орбита становится более вытянутой. Если скорость уменьшить, тело смещается ближе к Солнцу.
            При очень большой скорости траектория может стать почти открытой, и тело начнёт уходить из системы.</p>

            <h3>Что происходит при изменении массы</h3>
            <p>Если увеличить массу планеты, её гравитационное влияние на другие тела становится сильнее. Это особенно хорошо заметно
            в сценах с несколькими планетами и в режиме с поясом астероидов. Масса влияет не только на само тело, но и на возмущения системы.</p>

            <h3>Что происходит при изменении G</h3>
            <p>Рост параметра G усиливает притяжение и делает движение более быстрым и более чувствительным к начальному положению тел.
            При уменьшении G система становится спокойнее, а орбиты меняются медленнее.</p>

            <h3>Что показывает режим Только притяжение Солнца</h3>
            <p>В этом режиме все тела притягиваются только к Солнцу. Взаимное влияние планет и астероидов друг на друга отключается.
            Этот режим полезен, чтобы сравнить идеализированную «простую» систему с полной многотельной моделью.</p>

            <h3>Что важно помнить</h3>
            <p>GravityLab не подменяет строгий курс небесной механики. Это учебная модель, которая помогает увидеть причинно-следственные связи:
            как масса, скорость, расстояние и сила притяжения влияют на форму орбиты и поведение всей системы.</p>
            """
        )

    def _presets_tab(self, presets: tuple[PresetDefinition, ...]) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        intro = QLabel(
            "Каждый пресет — это готовая учебная сцена. Ниже можно посмотреть, что именно показывает каждый сценарий, "
            "на что обратить внимание и какие параметры полезно менять во время урока или самостоятельной работы."
        )
        intro.setObjectName("mutedText")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for index, preset in enumerate(presets):
            row = index // 2
            column = index % 2
            grid.addWidget(PresetCard(preset), row, column)

        container = QWidget()
        container.setLayout(grid)
        layout.addWidget(container)
        layout.addStretch(1)
        return self._wrap_scroll(widget)

    def _shortcuts_tab(self) -> QWidget:
        return self._html_browser(
            """
            <h2>Управление и навигация</h2>

            <h3>Управление мышью</h3>
            <ul>
              <li><b>Клик по телу</b> — выбрать планету.</li>
              <li><b>Колесо мыши</b> — изменить масштаб сцены.</li>
              <li><b>Drag по пустому месту</b> — двигать камеру.</li>
              <li><b>Двойной клик по Солнцу</b> — сбросить камеру.</li>
            </ul>

            <h3>Горячие клавиши</h3>
            <ul>
              <li><b>Space</b> — старт / пауза.</li>
              <li><b>R</b> — сброс системы.</li>
              <li><b>[</b> и <b>]</b> — переключение выбранного тела.</li>
              <li><b>-</b> и <b>=</b> — уменьшить или увеличить скорость выбранной планеты.</li>
              <li><b>Shift по интерфейсу не требуется</b>: основные действия доступны кнопками и чекбоксами.</li>
              <li><b>PgUp / PgDown</b> — увеличить или уменьшить G.</li>
              <li><b>T</b> — следы, <b>G</b> — сетка, <b>L</b> — подписи, <b>C</b> — теория.</li>
              <li><b>O</b> — режим только притяжения Солнца.</li>
              <li><b>F</b> — следование за выбранным телом.</li>
              <li><b>U</b> — чистый UI.</li>
            </ul>

            <h3>Быстрые действия</h3>
            <ul>
              <li><b>Пауза</b> — остановить сцену и рассмотреть текущее положение тел.</li>
              <li><b>Сброс</b> — вернуть выбранную сцену в начальное состояние.</li>
              <li><b>Подогнать</b> — показать всю систему в окне.</li>
              <li><b>Снимок</b> — сохранить текущий кадр.</li>
              <li><b>Справка</b> — открыть подробное учебное описание программы.</li>
            </ul>

            <h3>Изменение параметров</h3>
            <ul>
              <li>Слева можно менять число планет, G, масштаб времени и плотность пояса астероидов.</li>
              <li>Там же включаются режимы отображения: следы, сетка, подписи, теория и только притяжение Солнца.</li>
              <li>В правой панели можно менять скорость и массу выбранного тела.</li>
              <li>Через пресеты можно быстро загружать готовые учебные сцены без ручной настройки.</li>
            </ul>

            <h3>Как читать правую панель</h3>
            <p>Правая панель показывает параметры выбранного тела: координаты, массу, скорость, расстояние до Солнца и историю изменения параметров во времени.
            Это особенно полезно, когда нужно сравнить две сцены или зафиксировать результат эксперимента.</p>

            <h3>Как использовать в учебной работе</h3>
            <p>Удобный сценарий такой: выбрать пресет, выдвинуть гипотезу, изменить только один параметр, понаблюдать изменения и сформулировать вывод.
            Тогда программа превращается не просто в демонстрацию, а в полноценный учебный инструмент.</p>
            """
        )

    def _html_browser(self, html: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(html)
        return browser

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(widget)
        return area

    def _author_block(self) -> QLabel:
        author = QLabel("Автор: Рыльцин Тимур, 10А, МОУ СОШ №22")
        author.setObjectName("mutedText")
        author.setWordWrap(True)
        return author
