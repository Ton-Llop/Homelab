const POLL_MS = 10_000;
const TIMEOUT_MS = 8_000;

const els = {
  body: document.body,
  status: document.getElementById("status-text"),
  power: document.getElementById("power"),
  todayKwh: document.getElementById("today-kwh"),
  todayCost: document.getElementById("today-cost"),
  monthKwh: document.getElementById("month-kwh"),
  monthCost: document.getElementById("month-cost"),
  runtime: document.getElementById("runtime"),
};

function decimals(min, max) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  });
}

const power = decimals(1, 1);
const energy = decimals(3, 3);
// 3 decimals pq no sigui 0,00
const smallCost = decimals(3, 3);
const cost = decimals(2, 2);

function formatCost(value) {
  const fmt = value < 1 ? smallCost : cost;
  return `${fmt.format(value)} €`;
}

function formatRuntime(minutes) {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

function render(data) {
  els.power.textContent = power.format(data.power_w);
  els.todayKwh.textContent = `${energy.format(data.today_kwh)} kWh`;
  els.monthKwh.textContent = `${energy.format(data.month_kwh)} kWh`;
  els.todayCost.textContent = formatCost(data.today_cost_eur);
  els.monthCost.textContent = formatCost(data.month_cost_eur);
  els.runtime.textContent = formatRuntime(data.today_runtime_min);
}

function setState(state, label) {
  els.body.dataset.state = state;
  els.status.textContent = label;
}

async function update() {

  if (document.hidden) return;

  try {
    const response = await fetch("/power", {
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    render(await response.json());
    setState("live", "Live");
  } catch (error) {
    console.warn("No se ha podido leer /power:", error);
    setState("offline", "Offline");
  }
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) update();
});

update();
setInterval(update, POLL_MS);
