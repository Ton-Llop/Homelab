const POLL_MS = 10_000;
const HISTORY_MS = 60_000; // el servidor guarda una muestra por minuto
const TIMEOUT_MS = 8_000;
const HISTORY_HOURS = 24;
const HISTORY_POINTS = 180;

const els = {
  body: document.body,
  status: document.getElementById("status-text"),
  power: document.getElementById("power"),
  range: document.getElementById("range"),
  stats: document.getElementById("stats"),
  todayKwh: document.getElementById("today-kwh"),
  todayCost: document.getElementById("today-cost"),
  todayRuntime: document.getElementById("today-runtime"),
  monthKwh: document.getElementById("month-kwh"),
  monthCost: document.getElementById("month-cost"),
  yearKwh: document.getElementById("year-kwh"),
  yearCost: document.getElementById("year-cost"),
  yearRuntime: document.getElementById("year-runtime"),
  monthRuntime: document.getElementById("month-runtime"),
  yearKwh: document.getElementById("year-kwh"),
  yearCost: document.getElementById("year-cost"),
  yearRuntime: document.getElementById("year-runtime"),
  canvas: document.getElementById("chart"),
  frame: document.querySelector(".plot__frame"),
  empty: document.getElementById("plot-empty"),
  tip: document.getElementById("tip"),
  tipValue: document.getElementById("tip-value"),
  tipTime: document.getElementById("tip-time"),
  viewToggle: document.getElementById("view-toggle"),
  tableView: document.getElementById("tableview"),
  tableBody: document.getElementById("table-body"),
};

const css = getComputedStyle(document.documentElement);
const theme = {
  surface: css.getPropertyValue("--surface").trim(),
  line: css.getPropertyValue("--line").trim(),
  muted: css.getPropertyValue("--text-3").trim(),
  accent: css.getPropertyValue("--accent").trim(),
};

function decimals(min, max) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  });
}

const fmtPower = decimals(1, 1);
const fmtEnergySmall = decimals(3, 3);
const fmtEnergyMid = decimals(2, 2);
const fmtEnergyLarge = decimals(0, 0);
const fmtWhole = decimals(0, 0);
const fmtCostSmall = decimals(3, 3);
const fmtCost = decimals(2, 2);
const fmtClock = new Intl.DateTimeFormat("es-ES", {
  hour: "2-digit",
  minute: "2-digit",
});

// Tres decimales tienen sentido en 0,019 kWh y son falsa precision en 224,500.
function formatEnergy(value) {
  if (value < 10) return fmtEnergySmall.format(value);
  if (value < 100) return fmtEnergyMid.format(value);
  return fmtEnergyLarge.format(value);
}

function formatCost(value) {
  // Con centimos sueltos, 2 decimales se quedarian en "0,00": bajamos a 3.
  return (value < 1 ? fmtCostSmall : fmtCost).format(value);
}

// Formato corto: la tipografia pixel es ancha y la celda no da para "7 h 11 min".
function formatRuntime(minutes) {
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const rest = minutes % 60;
    return rest === 0 ? `${hours}h` : `${hours}h ${rest}m`;
  }

  const days = Math.floor(hours / 24);
  const rest = hours % 24;
  return rest === 0 ? `${days}d` : `${days}d ${rest}h`;
}

// --- Historico: lo sirve el backend desde SQLite ----------------------------

let samples = [];
let selected = null; // indice bajo el cursor o el foco de teclado

// --- Grafica ---------------------------------------------------------------

const ctx = els.canvas.getContext("2d");
const PAD = { top: 8, right: 8, bottom: 4, left: 8 };

// Pasos 1/1,25/1,5/2... en vez de potencias de 10: con un pico de 108 W el
// techo queda en 125 y no en 200, que aplastaba la serie contra el suelo.
const NICE_STEPS = [1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];

function niceCeil(value) {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  return (NICE_STEPS.find((step) => normalized <= step + 1e-9) ?? 10) * magnitude;
}

function plotGeometry() {
  const { width, height } = els.canvas.getBoundingClientRect();
  const values = samples.map(([, w]) => w);
  const yMax = niceCeil(Math.max(...values, 1) * 1.15);
  const x0 = PAD.left;
  const x1 = width - PAD.right;
  const y0 = PAD.top;
  const y1 = height - PAD.bottom;

  return {
    width,
    yMax,
    x0,
    x1,
    y0,
    y1,
    xOf: (i) => (samples.length < 2 ? x1 : x0 + ((x1 - x0) * i) / (samples.length - 1)),
    yOf: (w) => y1 - (y1 - y0) * (w / yMax),
  };
}

function drawMarker(g, index, radius) {
  const [, watts] = samples[index];
  const x = g.xOf(index);
  const y = g.yOf(watts);

  // Anillo de 2px en el color de superficie para que el punto no se pierda.
  ctx.beginPath();
  ctx.arc(x, y, radius + 2, 0, Math.PI * 2);
  ctx.fillStyle = theme.surface;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fillStyle = theme.accent;
  ctx.fill();
}

function drawCrosshair(g, index) {
  const x = Math.round(g.xOf(index)) + 0.5;
  ctx.strokeStyle = theme.muted;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, g.y0);
  ctx.lineTo(x, g.y1);
  ctx.stroke();
  drawMarker(g, index, 4);
}

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const { width, height } = els.canvas.getBoundingClientRect();
  if (width === 0 || height === 0) return;

  els.canvas.width = Math.round(width * dpr);
  els.canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const enough = samples.length >= 2;
  els.empty.hidden = enough;
  if (!enough) return;

  const g = plotGeometry();

  // Rejilla: lineas solidas de 1px, un paso por encima de la superficie.
  ctx.strokeStyle = theme.line;
  ctx.lineWidth = 1;
  for (const fraction of [0, 0.5, 1]) {
    const y = Math.round(g.yOf(g.yMax * fraction)) + 0.5;
    ctx.beginPath();
    ctx.moveTo(g.x0, y);
    ctx.lineTo(g.x1, y);
    ctx.stroke();
  }

  const path = new Path2D();
  samples.forEach(([, w], i) => {
    const x = g.xOf(i);
    const y = g.yOf(w);
    if (i === 0) path.moveTo(x, y);
    else path.lineTo(x, y);
  });

  // Relleno de area: la serie al ~10 %, difuminado hasta cero.
  const fill = new Path2D(path);
  fill.lineTo(g.xOf(samples.length - 1), g.y1);
  fill.lineTo(g.xOf(0), g.y1);
  fill.closePath();

  const gradient = ctx.createLinearGradient(0, g.y0, 0, g.y1);
  gradient.addColorStop(0, "rgba(0, 168, 132, 0.10)");
  gradient.addColorStop(1, "rgba(0, 168, 132, 0)");
  ctx.fillStyle = gradient;
  ctx.fill(fill);

  // Trazo de 2px con halo: el neon sale del glow, no de subir la luminosidad.
  ctx.save();
  ctx.strokeStyle = theme.accent;
  ctx.lineWidth = 2;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.shadowColor = "rgba(0, 168, 132, 0.55)";
  ctx.shadowBlur = 10;
  ctx.stroke(path);
  ctx.restore();

  drawMarker(g, samples.length - 1, 4);
  if (selected !== null && selected !== samples.length - 1) drawCrosshair(g, selected);
}

// --- Capa de hover y teclado -----------------------------------------------

function nearestIndex(clientX) {
  const rect = els.canvas.getBoundingClientRect();
  const g = plotGeometry();
  const x = clientX - rect.left;
  let best = 0;
  let bestDistance = Infinity;

  samples.forEach((_, i) => {
    const distance = Math.abs(g.xOf(i) - x);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = i;
    }
  });

  return best;
}

function showTip(index) {
  if (samples.length < 2) return;
  selected = index;

  const g = plotGeometry();
  const [time, watts] = samples[index];

  els.tipValue.textContent = `${fmtPower.format(watts)} W`;
  els.tipTime.textContent = fmtClock.format(new Date(time));
  els.tip.hidden = false;

  els.tip.style.left = `${Math.min(Math.max(g.xOf(index), 44), g.width - 44)}px`;
  els.tip.style.top = `${Math.max(g.yOf(watts) - 10, 32)}px`;
  draw();
}

function hideTip() {
  selected = null;
  els.tip.hidden = true;
  draw();
}

els.canvas.addEventListener("pointermove", (event) => showTip(nearestIndex(event.clientX)));
els.canvas.addEventListener("pointerleave", hideTip);
els.canvas.addEventListener("blur", hideTip);

els.canvas.addEventListener("focus", () => {
  if (samples.length >= 2) showTip(samples.length - 1);
});

els.canvas.addEventListener("keydown", (event) => {
  if (samples.length < 2) return;
  const current = selected ?? samples.length - 1;

  if (event.key === "ArrowLeft") showTip(Math.max(current - 1, 0));
  else if (event.key === "ArrowRight") showTip(Math.min(current + 1, samples.length - 1));
  else if (event.key === "Escape") hideTip();
  else return;

  event.preventDefault();
});

// --- Vista de tabla: el gemelo accesible de la grafica ----------------------

function renderTable() {
  els.tableBody.replaceChildren();

  for (const [time, watts] of [...samples].reverse()) {
    const row = document.createElement("tr");
    const when = document.createElement("td");
    const value = document.createElement("td");

    when.textContent = fmtClock.format(new Date(time));
    value.textContent = `${fmtPower.format(watts)} W`;

    row.append(when, value);
    els.tableBody.append(row);
  }
}

els.viewToggle.addEventListener("click", () => {
  const showTable = els.body.dataset.view !== "table";

  els.body.dataset.view = showTable ? "table" : "chart";
  els.tableView.hidden = !showTable;
  els.viewToggle.textContent = showTable ? "gráfica" : "tabla";
  els.viewToggle.setAttribute("aria-pressed", String(showTable));

  if (showTable) renderTable();
  else draw();
});

// --- Render y ciclo de sondeo ----------------------------------------------

// Guarda por si el backend aun no envia la proyeccion: mejor un guion que un NaN.
function maybe(value, format) {
  return Number.isFinite(value) ? format(value) : "—";
}

function renderSummary(data) {
  els.power.textContent = fmtPower.format(data.power_w);
  els.todayKwh.textContent = formatEnergy(data.today_kwh);
  els.monthKwh.textContent = formatEnergy(data.month_kwh);
  els.todayCost.textContent = formatCost(data.today_cost_eur);
  els.monthCost.textContent = formatCost(data.month_cost_eur);
  els.todayRuntime.textContent = formatRuntime(data.today_runtime_min);
  els.monthRuntime.textContent = formatRuntime(data.month_runtime_min);
  els.yearKwh.textContent = maybe(data.year_kwh, formatEnergy);
  els.yearCost.textContent = maybe(data.year_cost_eur, formatCost);
  els.yearRuntime.textContent = maybe(data.year_runtime_min, formatRuntime);
  // El runtime anual lo mide este servicio, no el enchufe: dejamos claro
  // desde cuando, porque los primeros dias sera mucho menor que el consumo.
  els.yearRuntime.title = data.measuring_since
    ? `Medido desde el ${new Date(data.measuring_since).toLocaleDateString("es-ES")}`
    : "";
}

function renderWindowStats() {
  if (samples.length < 2) {
    els.range.textContent = "Potencia";
    els.stats.textContent = "esperando lectura";
    return;
  }

  const values = samples.map(([, w]) => w);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const hours = (Date.now() - samples[0][0]) / 3_600_000;
  const span = hours >= 1
    ? `${Math.round(hours)} h`
    : `${Math.max(Math.round(hours * 60), 1)} min`;

  els.range.textContent = `Potencia · ${span}`;
  els.stats.textContent = `mín ${fmtWhole.format(min)} · máx ${fmtWhole.format(max)} W`;

  els.canvas.setAttribute(
    "aria-label",
    `Potencia de las últimas ${span}: mínimo ${fmtPower.format(min)} vatios, ` +
      `máximo ${fmtPower.format(max)} vatios.`,
  );
}

function setState(state, label) {
  els.body.dataset.state = state;
  els.status.textContent = label;
}

async function fetchJson(path) {
  const response = await fetch(path, {
    cache: "no-store",
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function update() {
  // Sin el iframe a la vista no tiene sentido seguir pidiendo datos.
  if (document.hidden) return;

  try {
    renderSummary(await fetchJson("/power"));
    setState("live", "live");
  } catch (error) {
    console.warn("No se ha podido leer /power:", error);
    setState("offline", "offline");
  }
}

async function loadHistory() {
  if (document.hidden) return;

  try {
    const data = await fetchJson(`/history?hours=${HISTORY_HOURS}&points=${HISTORY_POINTS}`);
    // El backend manda segundos epoch; el canvas y el tooltip trabajan en ms.
    samples = data.points.map(([seconds, watts]) => [seconds * 1000, watts]);
  } catch (error) {
    // Un fallo aqui no vacia la grafica: se mantiene el ultimo historico.
    console.warn("No se ha podido leer /history:", error);
    return;
  }

  renderWindowStats();

  if (els.body.dataset.view === "table") renderTable();
  else draw();
}

new ResizeObserver(() => draw()).observe(els.frame);

document.addEventListener("visibilitychange", () => {
  if (document.hidden) return;
  update();
  loadHistory();
});

renderWindowStats();
draw();
update();
loadHistory();
setInterval(update, POLL_MS);
setInterval(loadHistory, HISTORY_MS);
