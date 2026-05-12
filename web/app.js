"use strict";

const canvas = document.getElementById("spaceCanvas");
const ctx = canvas.getContext("2d");
const sparkline = document.getElementById("sparkline");
const sparkCtx = sparkline.getContext("2d");

const controls = {
  preset: document.getElementById("preset"),
  prevPresetButton: document.getElementById("prevPresetButton"),
  nextPresetButton: document.getElementById("nextPresetButton"),
  cameraMode: document.getElementById("cameraMode"),
  gravity: document.getElementById("gravity"),
  gravityValue: document.getElementById("gravityValue"),
  timeScale: document.getElementById("timeScale"),
  timeScaleValue: document.getElementById("timeScaleValue"),
  trails: document.getElementById("toggleTrails"),
  grid: document.getElementById("toggleGrid"),
  labels: document.getElementById("toggleLabels"),
  pauseButton: document.getElementById("pauseButton"),
  resetButton: document.getElementById("resetButton"),
  helpButton: document.getElementById("helpButton"),
  closeHelpButton: document.getElementById("closeHelpButton"),
  exitPresentationButton: document.getElementById("exitPresentationButton"),
  musicButton: document.getElementById("musicButton"),
  inspectorToggle: document.getElementById("inspectorToggle"),
  closeInspectorButton: document.getElementById("closeInspectorButton"),
  showButton: document.getElementById("showButton"),
  experimentButton: document.getElementById("experimentButton"),
  cameraCycleButton: document.getElementById("cameraCycleButton"),
  nextTaskButton: document.getElementById("nextTaskButton"),
  bodyCount: document.getElementById("bodyCount"),
  activePreset: document.getElementById("activePreset"),
  simTime: document.getElementById("simTime"),
  energyState: document.getElementById("energyState"),
  sceneKicker: document.getElementById("sceneKicker"),
  sceneTitle: document.getElementById("sceneTitle"),
  sceneDescription: document.getElementById("sceneDescription"),
  sceneTransition: document.getElementById("sceneTransition"),
  transitionTitle: document.getElementById("transitionTitle"),
  experimentHint: document.getElementById("experimentHint"),
  studyTitle: document.getElementById("studyTitle"),
  studyText: document.getElementById("studyText"),
  toast: document.getElementById("toast"),
  selectedColor: document.getElementById("selectedColor"),
  selectedName: document.getElementById("selectedName"),
  selectedKind: document.getElementById("selectedKind"),
  selectedMass: document.getElementById("selectedMass"),
  selectedSpeed: document.getElementById("selectedSpeed"),
  selectedRadius: document.getElementById("selectedRadius"),
  selectedPosition: document.getElementById("selectedPosition"),
  massControl: document.getElementById("massControl"),
  massControlValue: document.getElementById("massControlValue"),
  speedControl: document.getElementById("speedControl"),
  speedControlValue: document.getElementById("speedControlValue"),
  editorHint: document.getElementById("editorHint"),
};

const colors = {
  sun: "#ffd36a",
  mercury: "#b8bec8",
  venus: "#efb16a",
  earth: "#5ab3ff",
  mars: "#ff735f",
  jupiter: "#d7b18c",
  saturn: "#e6d28d",
  teal: "#56d6c2",
  violet: "#a88cff",
  asteroid: "#9aa9c0",
};

const presetOrder = ["three-orbits", "single-orbit", "chaos", "binary-giants", "asteroid-belt"];
const showOrder = ["three-orbits", "chaos", "binary-giants", "asteroid-belt"];
const presetLabels = {
  "three-orbits": "Три орбиты",
  "single-orbit": "Одна планета",
  chaos: "Хаос",
  "binary-giants": "Два гиганта",
  "asteroid-belt": "Пояс астероидов",
};
const presetDescriptions = {
  "three-orbits": "Стабильные орбиты вокруг массивного центра.",
  "single-orbit": "Одна планета показывает базовый принцип круговой орбиты.",
  chaos: "Малое изменение траектории быстро меняет всю систему.",
  "binary-giants": "Два массивных тела создают сложное поле притяжения.",
  "asteroid-belt": "Множество малых тел движутся под влиянием планет.",
};
const studyTasks = [
  {
    title: "Создай орбиту",
    text: "Добавьте планету и попробуйте получить плавную траекторию вокруг Солнца.",
  },
  {
    title: "Увеличь массу",
    text: "Выберите планету и поднимите массу: траектория соседних тел изменится заметнее.",
  },
  {
    title: "Сравни скорость",
    text: "Измените скорость выбранной планеты и сравните, стала орбита шире или уже.",
  },
];

const presets = {
  "single-orbit": [
    ["Солнце", 332946, 26, 0, 0, 0, 0, colors.sun],
    ["Земля", 1, 7, 220, 0, 0, 38.9, colors.earth],
  ],
  "three-orbits": [
    ["Солнце", 332946, 28, 0, 0, 0, 0, colors.sun],
    ["Меркурий", 0.055, 5, 132, 0, 0, 50.4, colors.mercury],
    ["Земля", 1, 7, 235, 0, 0, 37.6, colors.earth],
    ["Марс", 0.107, 6, 330, 0, 0, 31.5, colors.mars],
  ],
  chaos: [
    ["Солнце", 332946, 28, 0, 0, 0, 0, colors.sun],
    ["Венера", 0.815, 7, 165, 0, 0, 45.2, colors.venus],
    ["Земля", 1, 7, -245, 45, -5.5, -36.4, colors.earth],
    ["Марс", 0.107, 6, 85, -300, 33.2, 9.4, colors.mars],
    ["Юпитер", 317.8, 11, -430, -70, 4.2, -23.2, colors.jupiter],
  ],
  "binary-giants": [
    ["Солнце I", 220000, 24, -88, 0, 0, -24, colors.sun],
    ["Солнце II", 180000, 22, 108, 0, 0, 28, colors.violet],
    ["Земля", 1, 7, 0, 320, -38, 0, colors.earth],
    ["Марс", 0.107, 6, 0, -410, 33, 0, colors.mars],
  ],
  "asteroid-belt": [],
};

const state = {
  bodies: [],
  selected: 1,
  gravity: 1,
  timeScale: 0.5,
  paused: false,
  presentationMode: false,
  showMode: false,
  experimentMode: false,
  draggingNewBody: false,
  dragStartWorld: null,
  dragCurrentWorld: null,
  manualBodyCount: 0,
  studyTaskIndex: 0,
  showIndex: 0,
  showStartedAt: 0,
  showSceneStartedAt: 0,
  transitionUntil: 0,
  simTime: 0,
  lastFrame: 0,
  camera: { x: 0, y: 0, zoom: 1, initialized: false },
};

let toastTimer = 0;
let audioContext = null;
let musicNodes = null;

function makeBody(seed, asteroid = false) {
  const [name, mass, radius, x, y, vx, vy, color] = seed;
  return {
    name,
    mass,
    radius,
    x,
    y,
    vx,
    vy,
    color,
    asteroid,
    manual: false,
    trail: [],
    speedHistory: [],
  };
}

function asteroidBeltSeeds() {
  const seeds = [["Солнце", 332946, 28, 0, 0, 0, 0, colors.sun]];
  for (let i = 0; i < 72; i += 1) {
    const angle = (Math.PI * 2 * i) / 72 + Math.sin(i * 8.3) * 0.08;
    const radius = 285 + (i % 9) * 13 + Math.sin(i * 1.7) * 7;
    const speed = Math.sqrt((1 * 332946) / radius) * 1.15;
    seeds.push([
      `Астероид ${i + 1}`,
      0.0002,
      2,
      Math.cos(angle) * radius,
      Math.sin(angle) * radius,
      -Math.sin(angle) * speed,
      Math.cos(angle) * speed,
      colors.asteroid,
    ]);
  }
  seeds.push(["Юпитер", 317.8, 11, -520, 0, 0, -21.4, colors.jupiter]);
  return seeds;
}

function resetSimulation() {
  const preset = controls.preset.value;
  const seeds = preset === "asteroid-belt" ? asteroidBeltSeeds() : presets[preset];
  state.bodies = seeds.map((seed, index) => makeBody(seed, preset === "asteroid-belt" && index > 0 && index < seeds.length - 1));
  state.selected = Math.min(1, state.bodies.length - 1);
  state.simTime = 0;
  state.camera.initialized = false;
  state.manualBodyCount = 0;
  document.body.classList.remove("inspector-open");
  updateSceneCopy();
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * scale));
  canvas.height = Math.max(1, Math.floor(rect.height * scale));
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
}

function step(dt) {
  const bodies = state.bodies;
  const ax = new Array(bodies.length).fill(0);
  const ay = new Array(bodies.length).fill(0);
  const softening = 80;

  for (let i = 0; i < bodies.length; i += 1) {
    for (let j = i + 1; j < bodies.length; j += 1) {
      const a = bodies[i];
      const b = bodies[j];
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const distSq = dx * dx + dy * dy + softening;
      const dist = Math.sqrt(distSq);
      const force = state.gravity / (distSq * dist);
      ax[i] += dx * force * b.mass;
      ay[i] += dy * force * b.mass;
      ax[j] -= dx * force * a.mass;
      ay[j] -= dy * force * a.mass;
    }
  }

  for (let i = 0; i < bodies.length; i += 1) {
    const body = bodies[i];
    body.vx += ax[i] * dt;
    body.vy += ay[i] * dt;
    body.x += body.vx * dt;
    body.y += body.vy * dt;
    body.trail.push([body.x, body.y]);
    if (body.trail.length > (body.asteroid ? 80 : 420)) body.trail.shift();
    const speed = Math.hypot(body.vx, body.vy);
    body.speedHistory.push(speed);
    if (body.speedHistory.length > 96) body.speedHistory.shift();
  }

  state.simTime += dt;
}

function isMobileViewport() {
  return window.matchMedia("(max-width: 900px)").matches;
}

function lerp(current, target, amount) {
  return current + (target - current) * amount;
}

function cameraTargetForMode() {
  if (!state.bodies.length) return;
  const mode = controls.cameraMode.value;
  const selectedExperimentFocus = state.experimentMode && mode === "selected";
  const focusBody =
    mode === "selected"
      ? state.bodies[state.selected]
      : mode === "sun"
        ? state.bodies[0]
        : null;

  let targetX = 0;
  let targetY = 0;
  if (focusBody) {
    targetX = focusBody.x;
    targetY = focusBody.y;
  }

  const nonAsteroids = state.bodies.filter((body) => !body.asteroid);
  let maxRadius = 240;
  if (selectedExperimentFocus && focusBody) {
    maxRadius = 260;
  } else if (mode === "auto") {
    for (const body of nonAsteroids) {
      maxRadius = Math.max(maxRadius, Math.hypot(body.x, body.y) + 120);
    }
  } else {
    for (const body of nonAsteroids) {
      maxRadius = Math.max(maxRadius, Math.hypot(body.x - targetX, body.y - targetY) + 180);
    }
  }

  const width = canvas.clientWidth || 1;
  const height = canvas.clientHeight || 1;
  let zoom = Math.min(width, height) / (maxRadius * 2);
  zoom = Math.max(isMobileViewport() ? 0.34 : 0.45, Math.min(1.8, zoom));

  return { x: targetX, y: targetY, zoom };
}

function updateCamera() {
  const target = cameraTargetForMode();
  if (!target) return;
  if (!state.camera.initialized) {
    state.camera.x = target.x;
    state.camera.y = target.y;
    state.camera.zoom = target.zoom;
    state.camera.initialized = true;
    return;
  }

  const smooth = state.experimentMode ? 0.45 : state.showMode ? 0.035 : 0.08;
  state.camera.x = lerp(state.camera.x, target.x, smooth);
  state.camera.y = lerp(state.camera.y, target.y, smooth);
  state.camera.zoom = lerp(state.camera.zoom, target.zoom, smooth);
}

function worldToScreen(x, y) {
  return {
    x: canvas.clientWidth / 2 + (x - state.camera.x) * state.camera.zoom,
    y: canvas.clientHeight / 2 + (y - state.camera.y) * state.camera.zoom,
  };
}

function screenToWorld(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  return {
    x: (x - canvas.clientWidth / 2) / state.camera.zoom + state.camera.x,
    y: (y - canvas.clientHeight / 2) / state.camera.zoom + state.camera.y,
  };
}

function hexToRgb(hex) {
  const value = hex.replace("#", "");
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16),
  };
}

function drawGrid() {
  if (!controls.grid.checked) return;
  const stepSize = 80 * state.camera.zoom;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.strokeStyle = "rgba(143, 169, 209, 0.10)";
  ctx.lineWidth = 1;
  for (let x = (width / 2) % stepSize; x < width; x += stepSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = (height / 2) % stepSize; y < height; y += stepSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawBackground() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  const gradient = ctx.createRadialGradient(width * 0.48, height * 0.44, 0, width * 0.5, height * 0.5, Math.max(width, height));
  gradient.addColorStop(0, "#182033");
  gradient.addColorStop(0.52, "#0a0f19");
  gradient.addColorStop(1, "#05070c");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

}

function drawTrails() {
  if (!controls.trails.checked) return;
  for (const body of state.bodies) {
    if (body.trail.length < 2) continue;
    const rgb = hexToRgb(body.color);
    const step = body.asteroid ? 3 : 1;
    for (let i = step; i < body.trail.length; i += step) {
      const prev = worldToScreen(body.trail[i - step][0], body.trail[i - step][1]);
      const point = worldToScreen(body.trail[i][0], body.trail[i][1]);
      const age = i / body.trail.length;
      const alpha = body.asteroid ? 0.04 + age * 0.18 : 0.05 + age * 0.58;
      ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
      ctx.lineWidth = (body.asteroid ? 0.8 : 1.1 + age * 2.2) * Math.max(0.7, state.camera.zoom);
      ctx.beginPath();
      ctx.moveTo(prev.x, prev.y);
      ctx.lineTo(point.x, point.y);
      ctx.stroke();
    }
  }
}

function drawBodies() {
  for (let i = 0; i < state.bodies.length; i += 1) {
    const body = state.bodies[i];
    const point = worldToScreen(body.x, body.y);
    const radius = Math.max(1.4, body.radius * state.camera.zoom);
    if (i === 0 || body.mass > 100000) {
      const halo = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, radius * 7.5);
      halo.addColorStop(0, `${body.color}70`);
      halo.addColorStop(0.4, `${body.color}22`);
      halo.addColorStop(1, `${body.color}00`);
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(point.x, point.y, radius * 7.5, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.save();
    ctx.shadowColor = body.color;
    ctx.shadowBlur = i === state.selected ? 34 : body.asteroid ? 4 : 22;
    ctx.fillStyle = body.color;
    ctx.beginPath();
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    if (i === state.selected) {
      const pulse = 1 + Math.sin(state.simTime * 3.2) * 0.16;
      ctx.strokeStyle = "rgba(86, 214, 194, 0.92)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(point.x, point.y, radius + 8 * pulse, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (controls.labels.checked && (!body.asteroid || i === state.selected)) {
      ctx.fillStyle = "rgba(238, 244, 255, 0.86)";
      ctx.font = "12px system-ui, sans-serif";
      ctx.fillText(body.name, point.x + radius + 8, point.y - radius - 4);
    }
  }
}

function drawExperimentDraft() {
  if (!state.experimentMode || !state.dragStartWorld || !state.dragCurrentWorld) return;
  const start = worldToScreen(state.dragStartWorld.x, state.dragStartWorld.y);
  const end = worldToScreen(state.dragCurrentWorld.x, state.dragCurrentWorld.y);
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const distance = Math.hypot(dx, dy);
  const radius = Math.max(5, 7 * state.camera.zoom);
  const draftVelocity = velocityFromDrag(state.dragStartWorld, state.dragCurrentWorld);
  const draftSpeed = Math.hypot(draftVelocity.vx, draftVelocity.vy);

  ctx.save();
  ctx.strokeStyle = "rgba(168, 140, 255, 0.9)";
  ctx.fillStyle = "rgba(168, 140, 255, 0.92)";
  ctx.lineWidth = 2;
  ctx.setLineDash([7, 6]);
  ctx.beginPath();
  ctx.arc(start.x, start.y, radius + 4, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  if (distance > 8) {
    const angle = Math.atan2(dy, dx);
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(end.x, end.y);
    ctx.lineTo(end.x - Math.cos(angle - 0.45) * 14, end.y - Math.sin(angle - 0.45) * 14);
    ctx.lineTo(end.x - Math.cos(angle + 0.45) * 14, end.y - Math.sin(angle + 0.45) * 14);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgba(238, 244, 255, 0.92)";
    ctx.font = "700 12px system-ui, sans-serif";
    ctx.fillText(`v=${draftSpeed.toFixed(0)}`, end.x + 10, end.y - 10);
  }
  ctx.restore();
}

function renderSparkline(body) {
  const width = sparkline.width;
  const height = sparkline.height;
  sparkCtx.clearRect(0, 0, width, height);
  sparkCtx.fillStyle = "rgba(255, 255, 255, 0.035)";
  sparkCtx.fillRect(0, 0, width, height);
  const data = body?.speedHistory || [];
  if (data.length < 2) return;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  sparkCtx.strokeStyle = "#56d6c2";
  sparkCtx.lineWidth = 3;
  sparkCtx.beginPath();
  data.forEach((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - 12 - ((value - min) / span) * (height - 24);
    if (index === 0) sparkCtx.moveTo(x, y);
    else sparkCtx.lineTo(x, y);
  });
  sparkCtx.stroke();
}

function updateSceneCopy() {
  const presetId = controls.preset.value;
  controls.sceneTitle.textContent = presetLabels[presetId] || presetId;
  controls.sceneDescription.textContent = presetDescriptions[presetId] || "";
  controls.sceneKicker.textContent = state.showMode ? "Шоу-режим" : "Демонстрация";
  controls.transitionTitle.textContent = presetLabels[presetId] || presetId;
}

function showToast(message) {
  window.clearTimeout(toastTimer);
  controls.toast.textContent = message;
  controls.toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => controls.toast.classList.remove("is-visible"), 2600);
}

function startMusic() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) {
    showToast("Музыка не поддерживается этим браузером");
    return;
  }

  audioContext = audioContext || new AudioContext();
  if (audioContext.state === "suspended") {
    audioContext.resume();
  }

  const now = audioContext.currentTime;
  const master = audioContext.createGain();
  const padFilter = audioContext.createBiquadFilter();
  const melodyFilter = audioContext.createBiquadFilter();
  const delay = audioContext.createDelay(4);
  const feedback = audioContext.createGain();
  const wet = audioContext.createGain();
  const melodyOutput = audioContext.createGain();
  const padOscillators = [
    { frequency: 55.0, gain: 0.035, detune: -4 },
    { frequency: 82.41, gain: 0.028, detune: 5 },
    { frequency: 110.0, gain: 0.024, detune: -8 },
  ].map((config) => {
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = config.frequency;
    oscillator.detune.value = config.detune;
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(config.gain, now + 2.5);
    oscillator.connect(gain).connect(padFilter);
    oscillator.start(now);
    return { oscillator, gain };
  });
  const melodyNotes = [220, 277.18, 329.63, 415.3, 369.99, 329.63, 277.18, 246.94, 220, 329.63, 493.88, 415.3];
  const noteLength = 0.72;

  padFilter.type = "lowpass";
  padFilter.frequency.setValueAtTime(540, now);
  padFilter.Q.value = 0.5;
  melodyFilter.type = "lowpass";
  melodyFilter.frequency.setValueAtTime(1500, now);
  melodyFilter.Q.value = 0.7;
  delay.delayTime.value = 0.42;
  feedback.gain.value = 0.22;
  wet.gain.value = 0.28;
  master.gain.setValueAtTime(0, now);
  master.gain.linearRampToValueAtTime(0.38, now + 1.6);

  padFilter.connect(master);
  melodyOutput.connect(melodyFilter);
  melodyFilter.connect(master);
  melodyFilter.connect(delay);
  delay.connect(feedback).connect(delay);
  delay.connect(wet).connect(master);
  master.connect(audioContext.destination);

  let noteIndex = 0;
  function scheduleMelodyNote() {
    if (!musicNodes) return;
    const start = audioContext.currentTime + 0.03;
    const end = start + noteLength * 0.62;
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "triangle";
    oscillator.frequency.setValueAtTime(melodyNotes[noteIndex % melodyNotes.length], start);
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(0.105, start + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.006, end);
    gain.gain.setValueAtTime(0, end + 0.03);
    oscillator.connect(gain).connect(melodyOutput);
    oscillator.start(start);
    oscillator.stop(end + 0.08);
    noteIndex += 1;
  }

  musicNodes = {
    master,
    padOscillators,
    melodyTimer: window.setInterval(scheduleMelodyNote, noteLength * 1000),
  };
  scheduleMelodyNote();
  controls.musicButton.classList.add("is-active");
  controls.musicButton.textContent = "Звук вкл.";
  showToast("Мелодия включена");
}

function stopMusic() {
  if (!musicNodes || !audioContext) return;
  const now = audioContext.currentTime;
  musicNodes.master.gain.cancelScheduledValues(now);
  musicNodes.master.gain.setValueAtTime(musicNodes.master.gain.value, now);
  musicNodes.master.gain.linearRampToValueAtTime(0, now + 0.7);
  for (const { oscillator } of musicNodes.padOscillators) {
    oscillator.stop(now + 0.8);
  }
  window.clearInterval(musicNodes.melodyTimer);
  musicNodes = null;
  controls.musicButton.classList.remove("is-active");
  controls.musicButton.textContent = "Музыка";
  showToast("Музыка выключена");
}

function toggleMusic() {
  if (musicNodes) {
    stopMusic();
  } else {
    startMusic();
  }
}

function flashTransition(presetId, timestamp) {
  controls.transitionTitle.textContent = presetLabels[presetId] || presetId;
  controls.sceneTransition.classList.add("is-active");
  state.transitionUntil = timestamp + 1500;
}

function updateShow(timestamp) {
  if (!state.showMode) return;
  const sceneDuration = 13000;
  if (timestamp - state.showSceneStartedAt < sceneDuration) return;
  state.showIndex = (state.showIndex + 1) % showOrder.length;
  const nextPreset = showOrder[state.showIndex];
  setPreset(nextPreset);
  state.showSceneStartedAt = timestamp;
  flashTransition(nextPreset, timestamp);
}

function startShow(timestamp = performance.now()) {
  setExperimentMode(false, true);
  state.showMode = true;
  state.showIndex = 0;
  state.showStartedAt = timestamp;
  state.showSceneStartedAt = timestamp;
  state.paused = false;
  controls.timeScale.value = "0.7";
  state.timeScale = 0.7;
  controls.cameraMode.value = "auto";
  setPresentationMode(true);
  setPreset(showOrder[state.showIndex]);
  flashTransition(showOrder[state.showIndex], timestamp);
}

function stopShow() {
  state.showMode = false;
  controls.sceneTransition.classList.remove("is-active");
  state.transitionUntil = 0;
  updateSceneCopy();
}

function toggleShow() {
  if (state.showMode) {
    stopShow();
    setPresentationMode(false);
  } else {
    startShow();
  }
}

function setExperimentMode(enabled, silent = false) {
  state.experimentMode = enabled;
  state.draggingNewBody = false;
  state.dragStartWorld = null;
  state.dragCurrentWorld = null;
  document.body.classList.toggle("experiment-mode", enabled);
  if (enabled) {
    if (state.showMode) stopShow();
    setPresentationMode(false);
    state.paused = false;
    controls.cameraMode.value = "auto";
    state.camera.initialized = false;
    if (!silent) showToast("Кликните по пустому месту, чтобы добавить планету");
  }
}

function toggleExperimentMode() {
  setExperimentMode(!state.experimentMode);
}

function updateStudyTask() {
  const task = studyTasks[state.studyTaskIndex];
  controls.studyTitle.textContent = task.title;
  controls.studyText.textContent = task.text;
}

function shiftStudyTask() {
  state.studyTaskIndex = (state.studyTaskIndex + 1) % studyTasks.length;
  updateStudyTask();
}

function cameraModeLabel(mode) {
  if (mode === "sun") return "Солнце";
  if (mode === "selected") return "Планета";
  return "Авто";
}

function updateCameraCycleButton() {
  controls.cameraCycleButton.textContent = `Камера: ${cameraModeLabel(controls.cameraMode.value)}`;
}

function cycleCameraMode() {
  const modes = ["auto", "sun", "selected"];
  const currentIndex = Math.max(0, modes.indexOf(controls.cameraMode.value));
  controls.cameraMode.value = modes[(currentIndex + 1) % modes.length];
  state.camera.initialized = false;
  updateCameraCycleButton();
}

function canEditBody(body) {
  return Boolean(body && !body.asteroid && state.selected !== 0);
}

function syncEditorControls(body) {
  const editable = canEditBody(body);
  const speed = body ? Math.hypot(body.vx, body.vy) : 0;
  controls.massControl.disabled = !editable;
  controls.speedControl.disabled = !editable;
  controls.massControl.value = String(Math.min(Number(controls.massControl.max), Math.max(Number(controls.massControl.min), body?.mass || 1)));
  controls.speedControl.value = String(Math.min(Number(controls.speedControl.max), Math.max(Number(controls.speedControl.min), speed)));
  controls.massControlValue.value = body ? body.mass.toLocaleString("ru-RU", { maximumFractionDigits: 1 }) : "0";
  controls.speedControlValue.value = speed.toFixed(1);
  controls.editorHint.textContent = editable
    ? "Чем больше масса и скорость, тем сильнее меняется траектория."
    : "Для Солнца и астероидов редактирование отключено.";
}

function updateUi() {
  const body = state.bodies[state.selected] || state.bodies[0];
  controls.gravityValue.value = Number(state.gravity).toFixed(2);
  controls.timeScaleValue.value = `${Number(state.timeScale).toFixed(1)}x`;
  controls.pauseButton.textContent = state.paused ? "Старт" : "Пауза";
  controls.showButton.textContent = state.showMode ? "Стоп" : "Шоу";
  controls.experimentButton.textContent = state.experimentMode ? "Стоп эксп." : "Эксперимент";
  updateCameraCycleButton();
  controls.experimentHint.textContent = state.draggingNewBody
    ? "Протяните и отпустите, чтобы задать начальную скорость"
    : "Кликните по пустому месту, чтобы добавить планету";
  controls.bodyCount.textContent = `${state.bodies.length} тел`;
  controls.activePreset.textContent = presetLabels[controls.preset.value] || controls.preset.value;
  controls.simTime.textContent = `t=${state.simTime.toFixed(1)}`;
  controls.energyState.textContent = state.showMode ? "шоу" : state.paused ? "пауза" : "идет";
  if (state.transitionUntil && performance.now() > state.transitionUntil) {
    controls.sceneTransition.classList.remove("is-active");
    state.transitionUntil = 0;
  }

  if (!body) return;
  const speed = Math.hypot(body.vx, body.vy);
  const radius = Math.hypot(body.x, body.y);
  controls.selectedColor.style.background = body.color;
  controls.selectedColor.style.color = body.color;
  controls.selectedName.textContent = body.name;
  controls.selectedKind.textContent = body.asteroid ? "астероид" : state.selected === 0 ? "звезда" : "планета";
  controls.selectedMass.textContent = body.mass.toLocaleString("ru-RU", { maximumFractionDigits: 4 });
  controls.selectedSpeed.textContent = speed.toFixed(2);
  controls.selectedRadius.textContent = radius.toFixed(1);
  controls.selectedPosition.textContent = `${body.x.toFixed(0)}, ${body.y.toFixed(0)}`;
  syncEditorControls(body);
  renderSparkline(body);
}

function render() {
  updateCamera();
  drawBackground();
  drawGrid();
  drawTrails();
  drawBodies();
  drawExperimentDraft();
  updateUi();
}

function tick(timestamp) {
  const elapsed = Math.min(48, timestamp - (state.lastFrame || timestamp));
  state.lastFrame = timestamp;
  updateShow(timestamp);
  if (!state.paused) {
    const dt = 0.018 * state.timeScale * elapsed;
    const substeps = Math.max(1, Math.ceil(state.timeScale * 2));
    for (let i = 0; i < substeps; i += 1) step(dt / substeps);
  }
  render();
  requestAnimationFrame(tick);
}

function velocityFromDrag(start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const limitVelocity = (velocity) => {
    const speed = Math.hypot(velocity.vx, velocity.vy);
    const maxSpeed = 45;
    if (speed <= maxSpeed) return velocity;
    const scale = maxSpeed / speed;
    return { vx: velocity.vx * scale, vy: velocity.vy * scale };
  };
  if (Math.hypot(dx, dy) > 18) {
    return limitVelocity({ vx: dx * 0.05, vy: dy * 0.05 });
  }
  const radius = Math.max(120, Math.hypot(start.x, start.y));
  const speed = Math.sqrt((state.gravity * 332946) / radius) * 1.08;
  return limitVelocity({
    vx: (-start.y / radius) * speed,
    vy: (start.x / radius) * speed,
  });
}

function addManualPlanet(start, end) {
  const velocity = velocityFromDrag(start, end);
  state.manualBodyCount += 1;
  const body = makeBody(
    [
      `Планета ${state.manualBodyCount}`,
      1,
      7,
      start.x,
      start.y,
      velocity.vx,
      velocity.vy,
      state.manualBodyCount % 2 ? colors.violet : colors.teal,
    ],
    false,
  );
  body.manual = true;
  state.bodies.push(body);
  state.selected = state.bodies.length - 1;
  state.camera.initialized = false;
  state.paused = true;
  document.body.classList.add("inspector-open");
  showToast("Планета добавлена. Измените массу или скорость в инспекторе");
  window.setTimeout(() => {
    if (state.experimentMode && state.bodies.includes(body) && state.paused) {
      state.paused = false;
    }
  }, 1200);
}

function handleExperimentPointerDown(event) {
  if (!state.experimentMode) return false;
  event.preventDefault();
  const existingBodyIndex = bodyIndexAt(event.clientX, event.clientY);
  if (existingBodyIndex >= 0) {
    state.selected = existingBodyIndex;
    state.camera.initialized = false;
    document.body.classList.add("inspector-open");
    showToast(canEditBody(state.bodies[existingBodyIndex]) ? "Планета выбрана. Меняйте массу и скорость в инспекторе" : "Это тело можно смотреть, но нельзя редактировать");
    return true;
  }
  canvas.setPointerCapture?.(event.pointerId);
  const world = screenToWorld(event.clientX, event.clientY);
  state.draggingNewBody = true;
  state.dragStartWorld = world;
  state.dragCurrentWorld = world;
  return true;
}

function handleExperimentPointerMove(event) {
  if (!state.experimentMode || !state.draggingNewBody) return false;
  event.preventDefault();
  state.dragCurrentWorld = screenToWorld(event.clientX, event.clientY);
  return true;
}

function handleExperimentPointerUp(event) {
  if (!state.experimentMode || !state.draggingNewBody) return false;
  event.preventDefault();
  canvas.releasePointerCapture?.(event.pointerId);
  const end = screenToWorld(event.clientX, event.clientY);
  addManualPlanet(state.dragStartWorld, end);
  state.draggingNewBody = false;
  state.dragStartWorld = null;
  state.dragCurrentWorld = null;
  return true;
}

function bodyIndexAt(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  let best = -1;
  let bestDistance = Infinity;
  state.bodies.forEach((body, index) => {
    const point = worldToScreen(body.x, body.y);
    const distance = Math.hypot(point.x - x, point.y - y);
    if (distance < bestDistance && distance < Math.max(14, body.radius * state.camera.zoom + 10)) {
      best = index;
      bestDistance = distance;
    }
  });
  return best;
}

function selectAt(clientX, clientY) {
  const best = bodyIndexAt(clientX, clientY);
  if (best >= 0) state.selected = best;
}

function setPreset(presetId) {
  if (!presetOrder.includes(presetId)) return;
  setExperimentMode(false, true);
  controls.preset.value = presetId;
  resetSimulation();
}

function shiftPreset(direction) {
  const currentIndex = Math.max(0, presetOrder.indexOf(controls.preset.value));
  const nextIndex = (currentIndex + direction + presetOrder.length) % presetOrder.length;
  setPreset(presetOrder[nextIndex]);
}

function setPresentationMode(enabled) {
  if (!enabled && state.showMode) {
    stopShow();
  }
  state.presentationMode = enabled;
  document.body.classList.toggle("presentation-mode", enabled);
  document.body.classList.remove("inspector-open");
  updateSceneCopy();
  window.setTimeout(resizeCanvas, 60);
}

function toggleInspector() {
  if (window.matchMedia("(max-width: 900px)").matches) {
    document.body.classList.toggle("inspector-open");
  }
}

function setHelpMode(enabled) {
  document.body.classList.toggle("help-mode", enabled);
  document.getElementById("helpOverlay").setAttribute("aria-hidden", enabled ? "false" : "true");
}

controls.preset.addEventListener("change", () => setPreset(controls.preset.value));
controls.prevPresetButton.addEventListener("click", () => shiftPreset(-1));
controls.nextPresetButton.addEventListener("click", () => shiftPreset(1));
controls.cameraMode.addEventListener("change", () => {
  state.camera.initialized = false;
  updateCameraCycleButton();
});
controls.gravity.addEventListener("input", () => {
  state.gravity = Number(controls.gravity.value);
});
controls.timeScale.addEventListener("input", () => {
  state.timeScale = Number(controls.timeScale.value);
});
controls.pauseButton.addEventListener("click", () => {
  state.paused = !state.paused;
});
controls.resetButton.addEventListener("click", resetSimulation);
controls.helpButton.addEventListener("click", () => setHelpMode(true));
controls.closeHelpButton.addEventListener("click", () => setHelpMode(false));
controls.exitPresentationButton.addEventListener("click", () => setPresentationMode(false));
controls.musicButton.addEventListener("click", toggleMusic);
controls.inspectorToggle.addEventListener("click", toggleInspector);
controls.closeInspectorButton.addEventListener("click", () => document.body.classList.remove("inspector-open"));
controls.showButton.addEventListener("click", toggleShow);
controls.experimentButton.addEventListener("click", toggleExperimentMode);
controls.cameraCycleButton.addEventListener("click", cycleCameraMode);
controls.nextTaskButton.addEventListener("click", shiftStudyTask);
controls.massControl.addEventListener("input", () => {
  const body = state.bodies[state.selected];
  if (!canEditBody(body)) return;
  body.mass = Number(controls.massControl.value);
  controls.massControlValue.value = body.mass.toLocaleString("ru-RU", { maximumFractionDigits: 1 });
});
controls.speedControl.addEventListener("input", () => {
  const body = state.bodies[state.selected];
  if (!canEditBody(body)) return;
  const targetSpeed = Number(controls.speedControl.value);
  const currentSpeed = Math.hypot(body.vx, body.vy);
  if (currentSpeed > 0.001) {
    const scale = targetSpeed / currentSpeed;
    body.vx *= scale;
    body.vy *= scale;
  } else {
    body.vx = targetSpeed;
    body.vy = 0;
  }
  controls.speedControlValue.value = targetSpeed.toFixed(1);
});
canvas.addEventListener("pointerdown", handleExperimentPointerDown);
canvas.addEventListener("pointermove", handleExperimentPointerMove);
canvas.addEventListener("pointerup", handleExperimentPointerUp);
canvas.addEventListener("pointercancel", handleExperimentPointerUp);
canvas.addEventListener("click", (event) => {
  if (!state.experimentMode) selectAt(event.clientX, event.clientY);
});
window.addEventListener("resize", () => {
  if (!window.matchMedia("(max-width: 900px)").matches) {
    document.body.classList.remove("inspector-open");
  }
  resizeCanvas();
});
window.addEventListener("keydown", (event) => {
  if (event.code === "Space") {
    event.preventDefault();
    state.paused = !state.paused;
  }
  if (event.key.toLowerCase() === "r") resetSimulation();
  if (event.key.toLowerCase() === "p") setHelpMode(!document.body.classList.contains("help-mode"));
  if (event.key.toLowerCase() === "s") toggleShow();
  if (event.key === "ArrowLeft") shiftPreset(-1);
  if (event.key === "ArrowRight") shiftPreset(1);
  if (event.key === "Escape") {
    setHelpMode(false);
    stopShow();
    setExperimentMode(false, true);
    setPresentationMode(false);
    document.body.classList.remove("inspector-open");
  }
});

resizeCanvas();
resetSimulation();
updateStudyTask();
updateCameraCycleButton();
startShow();
requestAnimationFrame(tick);
