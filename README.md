# GravityLab

GravityLab — это desktop-приложение на PyQt6, которое превращает простой учебный скрипт по задаче N-тел в эффектный canvas-first showcase. Физическая модель намеренно остаётся лёгкой, а основной акцент сделан на визуальной выразительности, демо-пресетах, кинематографичной камере и компактной аналитике.

## Что изменилось

- Код проекта теперь разложен по пакету `src/gravitylab`, а не живёт в одном скрипте.
- Интерфейс перестроен в `canvas-first` layout: крупная сцена, компактная левая control-панель, узкий inspector, верхний top bar и нижний transport strip.
- Добавлены demo-пресеты, cinematic camera, clean UI mode и follow-режим для выбранного тела.
- Canvas получил более богатый sci-fi фон, мягкие halo, усиленные trails, подписи тел с анти-коллизией и ручной camera override.
- Inspector показывает выбранное тело, быстрые действия и sparkline-историю расстояния/скорости.
- В приложении появились сохранение новых UI-режимов, расширенные hotkeys и более явный сценарий для скриншотов и демо.
- Модель и главное окно покрыты unit-тестами и Qt smoke-тестами.

## Запуск

```bash
python3 -m pip install -e ".[dev]"
gravitylab
```

Можно также запустить совместимый обёрточный скрипт:

```bash
python3 gravity_sim_study_pyqt.py
```

### Web-версия

В проекте есть легкая статическая web-версия без сборки и дополнительных зависимостей:

```bash
python3 -m http.server 8080 --directory web
```

После запуска откройте:

```text
http://127.0.0.1:8080/
```

### Публикация на GitHub Pages

После push в ветку `main` GitHub Actions публикует папку `web/` на GitHub Pages.
В настройках репозитория откройте `Settings -> Pages` и выберите источник `GitHub Actions`.

Адрес сайта для этого репозитория:

```text
https://igorryltsin-design.github.io/GravityLab/
```

## Сборка

Собирать нужно отдельно на каждой целевой системе. Кросс-сборку для `macOS` и `Windows` этот проект не настраивает.

### macOS

Из корня проекта:

```bash
bash scripts/build_macos.sh
```

Результат сборки:

- `dist/GravityLab.app`

### Windows

Из корня проекта:

```bat
scripts\build_windows.bat
```

Результат сборки:

- `dist\GravityLab\GravityLab.exe`

Оба скрипта сами:

- ставят `PyInstaller`
- устанавливают проект локально через `pip install -e .`
- собирают desktop-приложение в оконном режиме без консоли

Если хотите собирать вручную без скриптов, базовая команда одинаковая по смыслу:

```bash
python3 -m PyInstaller --noconfirm --clean --windowed --name GravityLab --paths src gravity_sim_study_pyqt.py
```

На Windows вместо `python3` обычно используется `py`.

## Горячие клавиши

- `1..9`: пересобрать систему с `N` планетами
- `[` / `]`: выбрать предыдущую или следующую планету
- `-` / `=`: изменить скорость выбранной планеты
- `PgUp` / `PgDn`: увеличить или уменьшить `G`
- `O`: переключить режим “только Солнце”
- `T`, `G`, `C`, `L`: переключить следы, сетку, теорию и подписи
- `F`: включить слежение за выбранным телом
- `U`: переключить чистый UI
- `Space`: старт или пауза
- `R`: сбросить текущую систему
- `Esc`: выход

## Структура

- `src/gravitylab/app.py`: запуск приложения
- `src/gravitylab/main_window.py`: главное окно, меню и связка состояния
- `src/gravitylab/sim/model.py`: конфиг симуляции, пресеты, состояние камеры, история метрик и снимки
- `src/gravitylab/ui/canvas.py`: отрисовка сцены, подписи, камера и взаимодействие мышью
- `src/gravitylab/ui/top_bar.py`: верхний overlay bar
- `src/gravitylab/ui/bottom_strip.py`: нижний transport/control strip
- `src/gravitylab/ui/control_panel.py`: компактная левая панель быстрых настроек
- `src/gravitylab/ui/inspector_panel.py`: узкий инспектор выбранного тела и sparkline-графики
- `src/gravitylab/ui/preset_browser.py`: браузер демо-пресетов
- `src/gravitylab/theme.py`: палитра, размеры и Qt-стили
- `tests/`: тесты модели и Qt smoke-тесты

## Скриншоты

После локального запуска можно добавить скриншоты для портфолио:

- Canvas-first layout с top bar и bottom strip
- Кинематографичный пресет с включённой следящей камерой
- Clean UI режим для портфолио-скриншота без боковых панелей
