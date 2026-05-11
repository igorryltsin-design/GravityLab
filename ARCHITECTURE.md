# Архитектура GravityLab

## 1) Назначение приложения
`GravityLab` — desktop-приложение на `PyQt6` для визуальной симуляции 2D-задачи N-тел с акцентом на демонстрацию, пресеты, удобное управление камерой и учебную аналитику.

## 2) Общая структура
Проект разделен на 4 логических слоя:

1. `Entry/Bootstrap` — запуск приложения и настройка Qt-окружения.
2. `Application` — главное окно, orchestration и связывание UI с моделью.
3. `Domain/Simulation` — физическая модель, состояние симуляции, пресеты, snapshots.
4. `Presentation/UI` — виджеты интерфейса и отрисовка сцены.

## 3) Поток данных и управление
1. Точка входа создает `QApplication` и `MainWindow`.
2. `MainWindow` создает `GravitySim` и UI-компоненты.
3. `QTimer` (примерно 60 FPS) вызывает тик:
   - обновляет FPS,
   - выполняет шаг симуляции (`sim.step()`), если не пауза,
   - запрашивает `snapshot/stats`,
   - передает их в UI для перерисовки.
4. Действия пользователя (кнопки, слайдеры, чекбоксы, hotkeys) идут через Qt-сигналы в `MainWindow`, который вызывает методы `GravitySim` и обновляет UI.

## 4) Модули и ответственность

### 4.1 Точки входа и запуск
- `gravity_sim_study_pyqt.py`  
  Совместимый wrapper-скрипт: добавляет `src` в `sys.path`, вызывает `gravitylab.app.run()`.
- `src/gravitylab/__main__.py`  
  Пакетный entrypoint для `python -m gravitylab`.
- `src/gravitylab/app.py`  
  Создает `QApplication`, настраивает Qt plugin path, применяет тему, открывает `MainWindow`.
- `src/gravitylab/__init__.py`  
  Экспортирует `run`.

### 4.2 Главный слой приложения
- `src/gravitylab/main_window.py`  
  Центральный координатор приложения:
  - создает и композит UI (left panel + canvas + right panel + top/bottom bars),
  - связывает сигналы UI с методами симуляции,
  - управляет игровым/симуляционным циклом через `QTimer`,
  - реализует hotkeys,
  - управляет responsive-режимами (`compact/narrow/short`),
  - сохраняет/восстанавливает настройки через `QSettings`,
  - выполняет screenshot, about/help, переключение темы.

### 4.3 Модель симуляции (домен)
- `src/gravitylab/sim/model.py`  
  Ядро доменной логики:
  - dataclass-структуры: `Body`, `BodySnapshot`, `RenderOptions`, `SimulationSnapshot`, `SimulationStats`, `PresetDefinition` и др.,
  - класс `GravitySim`: состояние системы, шаг интеграции, вычисление ускорений,
  - переключатели режимов (`trails/grid/theory/labels/only_sun/paused/asteroid_belt`),
  - пресеты и их применение (`apply_named_preset`),
  - работа камеры с точки зрения состояния (`camera_mode`, `follow_target_index`),
  - истории метрик (distance/speed) для инспектора,
  - выдача immutable-снимков состояния (`snapshot`) для UI.

### 4.4 UI-слой
- `src/gravitylab/ui/canvas.py` (`SimulationCanvas`)  
  Отрисовка сцены: фон, сетка, тела, trails, подписи с анти-коллизией, camera/zoom, mouse interaction, screenshot export.
- `src/gravitylab/ui/top_bar.py` (`TopBar`)  
  Верхняя панель быстрых действий и отображения статуса/масштаба/G.
- `src/gravitylab/ui/bottom_strip.py` (`BottomStrip`)  
  Нижняя transport-панель: play/pause, step, reset, time scale, оперативные метки состояния.
- `src/gravitylab/ui/control_panel.py` (`ControlPanel`)  
  Левая панель конфигурации сцены: количество тел, G, time scale, плотность пояса, режимы отображения, пресеты.
- `src/gravitylab/ui/preset_browser.py` (`PresetBrowser`)  
  Выбор и применение готовых пресетов.
- `src/gravitylab/ui/inspector_panel.py` (`InspectorPanel`)  
  Правая аналитика: выбранное тело, быстрые действия (скорость/масса/follow/center), метрики, sparklines, теория.
- `src/gravitylab/ui/help_dialog.py` (`HelpDialog`)  
  Многостраничная справка: описание программы, физика, пресеты, управление.
- `src/gravitylab/ui/info_panel.py`  
  Совместимый alias: `InfoPanel -> InspectorPanel`.
- `src/gravitylab/ui/__init__.py`  
  Публичный экспорт UI-компонентов.

### 4.5 Тема и визуальный стиль
- `src/gravitylab/theme.py`  
  Определяет:
  - палитры `day/night`,
  - типографику,
  - генерацию глобального Qt stylesheet,
  - API переключения темы (`apply_theme`, `set_theme_mode`, `current_palette`).

### 4.6 Тесты
- `tests/test_model.py`  
  Проверки ядра симуляции: reset/step, границы, пресеты, астероидный пояс, snapshot/stats, clamp-логика, парсинг цветов темы.
- `tests/test_ui.py`  
  Qt smoke/interaction тесты: управление окнами и панелями, кнопки, чекбоксы, пресеты, responsive-поведение, help dialog, theme persistence.
- `tests/conftest.py`  
  Тестовые env-настройки Qt (`offscreen`, plugin path).

### 4.7 Сборка и окружение
- `pyproject.toml`  
  Зависимости, entrypoint `gravitylab`, настройки pytest.
- `scripts/build_macos.sh`  
  Сборка `.app` через PyInstaller (включая корректный Qt plugins bundle + codesign).
- `scripts/build_windows.bat`  
  Сборка `GravityLab.exe` через PyInstaller.
- `sitecustomize.py`  
  Глобальная fallback-настройка `QT_API` и plugin path при интерпретации Python.

## 5) Архитектурные принципы проекта
1. `MainWindow` — единственный orchestrator между UI и доменной моделью.
2. UI-компоненты максимально «тонкие»: рендер + сигналы, без физической логики.
3. `GravitySim` изолирует вычисления, режимы и формирование snapshot для представления.
4. Обмен между слоями через явные dataclass-снимки состояния, что упрощает тестирование и предотвращает случайные side effects в UI.
