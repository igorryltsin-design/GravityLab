"use strict";

const canvas = document.getElementById("spaceCanvas");
const ctx = canvas.getContext("2d");
const sparkline = document.getElementById("sparkline");
const sparkCtx = sparkline.getContext("2d");

const controls = {
  preset: document.getElementById("preset"),
  gravity: document.getElementById("gravity"),
  gravityValue: document.getElementById("gravityValue"),
  timeScale: document.getElementById("timeScale"),
  timeScaleValue: document.getElementById("timeScaleValue"),
  trails: document.getElementById("toggleTrails"),
  grid: document.getElementById("toggleGrid"),
  labels: document.getElementById("toggleLabels"),
  pauseButton: document.getElementById("pauseButton"),
  resetButton: document.getElementById("resetButton"),
  bodyCount: document.getElementById("bodyCount"),
  simTime: document.getElementById("simTime"),
  energyState: document.getElementById("energyState"),
  selectedColor: document.getElementById("selectedColor"),
  selectedName: document.getElementById("selectedName"),
  selectedKind: document.getElementById("selectedKind"),
  selectedMass: document.getElementById("selectedMass"),
  selectedSpeed: document.getElementById("selectedSpeed"),
  selectedRadius: document.getElementById("selectedRadius"),
  selectedPosition: document.getElementById("selectedPosition"),
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
  timeScale: 1,
  paused: false,
  simTime: 0,
  lastFrame: 0,
  camera: { x: 0, y: 0, zoom: 1 },
};

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

function updateCamera() {
  if (!state.bodies.length) return;
  const nonAsteroids = state.bodies.filter((body) => !body.asteroid);
  let maxRadius = 240;
  for (const body of nonAsteroids) {
    maxRadius = Math.max(maxRadius, Math.hypot(body.x, body.y) + 120);
  }
  const width = canvas.clientWidth || 1;
  const height = canvas.clientHeight || 1;
  state.camera.zoom = Math.min(width, height) / (maxRadius * 2);
  state.camera.zoom = Math.max(0.45, Math.min(1.6, state.camera.zoom));
}

function worldToScreen(x, y) {
  return {
    x: canvas.clientWidth / 2 + (x - state.camera.x) * state.camera.zoom,
    y: canvas.clientHeight / 2 + (y - state.camera.y) * state.camera.zoom,
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

  ctx.fillStyle = "rgba(238, 244, 255, 0.55)";
  for (let i = 0; i < 130; i += 1) {
    const x = (Math.sin(i * 91.7) * 0.5 + 0.5) * width;
    const y = (Math.sin(i * 43.2 + 4) * 0.5 + 0.5) * height;
    const r = (i % 5 === 0 ? 1.4 : 0.8) * (window.devicePixelRatio || 1);
    ctx.globalAlpha = 0.25 + ((i * 17) % 50) / 100;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawTrails() {
  if (!controls.trails.checked) return;
  for (const body of state.bodies) {
    if (body.trail.length < 2) continue;
    ctx.strokeStyle = body.asteroid ? "rgba(154, 169, 192, 0.22)" : `${body.color}99`;
    ctx.lineWidth = body.asteroid ? 1 : 1.5;
    ctx.beginPath();
    for (let i = 0; i < body.trail.length; i += 1) {
      const point = worldToScreen(body.trail[i][0], body.trail[i][1]);
      if (i === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    }
    ctx.stroke();
  }
}

function drawBodies() {
  for (let i = 0; i < state.bodies.length; i += 1) {
    const body = state.bodies[i];
    const point = worldToScreen(body.x, body.y);
    const radius = Math.max(1.4, body.radius * state.camera.zoom);
    ctx.save();
    ctx.shadowColor = body.color;
    ctx.shadowBlur = body.asteroid ? 4 : 18;
    ctx.fillStyle = body.color;
    ctx.beginPath();
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    if (i === state.selected) {
      ctx.strokeStyle = "rgba(86, 214, 194, 0.92)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(point.x, point.y, radius + 8, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (controls.labels.checked && (!body.asteroid || i === state.selected)) {
      ctx.fillStyle = "rgba(238, 244, 255, 0.86)";
      ctx.font = "12px system-ui, sans-serif";
      ctx.fillText(body.name, point.x + radius + 8, point.y - radius - 4);
    }
  }
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

function updateUi() {
  const body = state.bodies[state.selected] || state.bodies[0];
  controls.gravityValue.value = Number(state.gravity).toFixed(2);
  controls.timeScaleValue.value = `${Number(state.timeScale).toFixed(1)}x`;
  controls.pauseButton.textContent = state.paused ? "Старт" : "Пауза";
  controls.bodyCount.textContent = `${state.bodies.length} тел`;
  controls.simTime.textContent = `t=${state.simTime.toFixed(1)}`;
  controls.energyState.textContent = state.paused ? "paused" : "running";

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
  renderSparkline(body);
}

function render() {
  updateCamera();
  drawBackground();
  drawGrid();
  drawTrails();
  drawBodies();
  updateUi();
}

function tick(timestamp) {
  const elapsed = Math.min(48, timestamp - (state.lastFrame || timestamp));
  state.lastFrame = timestamp;
  if (!state.paused) {
    const dt = 0.018 * state.timeScale * elapsed;
    const substeps = Math.max(1, Math.ceil(state.timeScale * 2));
    for (let i = 0; i < substeps; i += 1) step(dt / substeps);
  }
  render();
  requestAnimationFrame(tick);
}

function selectAt(clientX, clientY) {
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
  if (best >= 0) state.selected = best;
}

controls.preset.addEventListener("change", resetSimulation);
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
canvas.addEventListener("click", (event) => selectAt(event.clientX, event.clientY));
window.addEventListener("resize", resizeCanvas);
window.addEventListener("keydown", (event) => {
  if (event.code === "Space") {
    event.preventDefault();
    state.paused = !state.paused;
  }
  if (event.key.toLowerCase() === "r") resetSimulation();
});

resizeCanvas();
resetSimulation();
requestAnimationFrame(tick);
