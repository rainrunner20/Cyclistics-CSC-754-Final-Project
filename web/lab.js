/* Inspect exported Python DES traces. This viewer never generates traffic events. */
const byId = (id) => document.getElementById(id);
const ui = {
  file: byId("trace-file"), status: byId("status"), scenario: byId("scenario"),
  meanWait: byId("mean-wait"), peakQueue: byId("peak-queue"),
  departed: byId("departed"), arrivals: byId("arrivals"),
  reset: byId("reset"), previous: byId("previous"), play: byId("play"),
  next: byId("next"), position: byId("position"), positionLabel: byId("position-label"),
  speed: byId("speed"), clock: byId("clock"), eventType: byId("event-type"),
  description: byId("event-description"), phase: byId("phase"),
  queue: byId("queue"), busy: byId("busy"), blocked: byId("blocked"),
  conservation: byId("conservation"), chart: byId("queue-chart"),
  log: byId("event-log"), pairing: byId("pairing"), policies: byId("policy-bars"),
};

const EVENT_TYPES = new Set([
  "arrival", "obstruction_start", "obstruction_end", "service_complete",
]);
const NS = "http://www.w3.org/2000/svg";
let report = null;
let cursor = 0;
let playback = null;

function setStatus(text, failed = false) {
  ui.status.textContent = text;
  ui.status.classList.toggle("error", failed);
}

function stopPlayback() {
  if (playback !== null) {
    clearInterval(playback);
    playback = null;
  }
  ui.play.textContent = "▶ Play";
}

function selectedScenario() {
  return report?.scenarios.find((item) => item.id === ui.scenario.value);
}

function validate(data) {
  if (!data || data.schema !== "cyclistics.visual_lab.v1" ||
      data.engine !== "python_des_reference" || data.data_status !== "synthetic" ||
      !Array.isArray(data.scenarios) || data.scenarios.length !== 3) {
    throw Error("Expected a Cyclistics synthetic Python DES visual_lab.v1 export.");
  }
  for (const caseData of data.scenarios) {
    if (typeof caseData.id !== "string" || typeof caseData.label !== "string" ||
        !caseData.metrics || !Array.isArray(caseData.events) ||
        caseData.events.length > 40000) {
      throw Error("Invalid scenario metadata or event limit exceeded.");
    }
    for (const key of ["arrivals", "completed_by_horizon", "mean_wait_s", "max_waiting_queue"]) {
      if (!Number.isFinite(caseData.metrics[key]) || caseData.metrics[key] < 0) {
        throw Error("Missing or invalid metric: " + key);
      }
    }
    let lastTime = -Infinity;
    for (let i = 0; i < caseData.events.length; i++) {
      const event = caseData.events[i];
      if (!event || event.index !== i || !EVENT_TYPES.has(event.event) ||
          !Number.isFinite(event.time_s) || event.time_s < lastTime ||
          !Number.isInteger(event.queue_waiting) || event.queue_waiting < 0 ||
          typeof event.description !== "string" ||
          typeof event.phase !== "string" ||
          typeof event.blocked !== "boolean" ||
          typeof event.server_busy !== "boolean" ||
          event.conservation_ok !== true) {
        throw Error("Invalid trace event at index " + i + ".");
      }
      lastTime = event.time_s;
    }
  }
  if (!data.parameters || !Number.isInteger(data.parameters.arrival_count) ||
      !Number.isInteger(data.parameters.seed)) {
    throw Error("Missing shared-arrival experiment parameters.");
  }
  return data;
}

function svgNode(tag, attributes = {}, text = "") {
  const element = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  if (text) element.textContent = text;
  return element;
}

function renderChart(events, position) {
  ui.chart.replaceChildren();
  if (!events.length) return;
  const left = 43, right = 700, top = 14, bottom = 147;
  const maxTime = Math.max(1, events.at(-1).time_s);
  const maxQueue = Math.max(1, ...events.map((e) => e.queue_waiting));
  const x = (time) => left + (time / maxTime) * (right - left);
  const y = (value) => bottom - (value / maxQueue) * (bottom - top);

  for (const fraction of [0, 0.5, 1]) {
    const yy = y(maxQueue * fraction);
    ui.chart.append(svgNode("line", {
      x1: left, x2: right, y1: yy, y2: yy,
      stroke: "#31545b", "stroke-width": 1, "stroke-dasharray": "4 5",
    }));
    ui.chart.append(svgNode("text", {
      x: 31, y: yy + 4, "text-anchor": "end", fill: "#88b0ac", "font-size": 11,
    }, String(Math.round(maxQueue * fraction * 10) / 10)));
  }
  ui.chart.append(svgNode("text", {
    x: left, y: 166, fill: "#94bcb0", "font-size": 11,
  }, "0 s"));
  ui.chart.append(svgNode("text", {
    x: right, y: 166, "text-anchor": "end", fill: "#94bcb0", "font-size": 11,
  }, maxTime.toFixed(1) + " s"));

  // The path is stepped because queue size changes only when events execute.
  let path = "M " + x(0) + " " + y(0);
  for (const event of events) {
    path += " H " + x(event.time_s) + " V " + y(event.queue_waiting);
  }
  ui.chart.append(svgNode("path", {
    d: path, fill: "none", stroke: "#6ac9a4",
    "stroke-width": 2.5, "stroke-linejoin": "round",
  }));
  const current = events[position];
  const cx = x(current.time_s), cy = y(current.queue_waiting);
  ui.chart.append(svgNode("line", {
    x1: cx, x2: cx, y1: top, y2: bottom,
    stroke: "#d9b478", "stroke-width": 1.4, "stroke-dasharray": "3 4",
  }));
  ui.chart.append(svgNode("circle", {
    cx, cy, r: 6, fill: "#ecc98c", stroke: "#11282b", "stroke-width": 2,
  }));
}

function logRow(event, active) {
  const row = document.createElement("button");
  row.type = "button";
  row.className = "log-row" + (active ? " selected" : "");
  row.setAttribute("aria-label", "Inspect event " + (event.index + 1));
  const fields = [
    "#" + (event.index + 1),
    event.time_s.toFixed(3) + "s",
    event.event.replaceAll("_", " "),
    "Q " + event.queue_waiting,
  ];
  for (const text of fields) {
    const cell = document.createElement("span");
    cell.textContent = text;
    row.append(cell);
  }
  row.addEventListener("click", () => {
    stopPlayback();
    cursor = event.index;
    render();
  });
  return row;
}

function renderLog(events) {
  ui.log.replaceChildren();
  if (!events.length) {
    ui.log.textContent = "No events in this scenario.";
    return;
  }
  const start = Math.max(0, cursor - 6);
  const end = Math.min(events.length, Math.max(13, cursor + 7));
  for (let i = start; i < end; i++) {
    ui.log.append(logRow(events[i], i === cursor));
  }
  ui.log.querySelector(".selected")?.scrollIntoView({ block: "nearest" });
}

function render() {
  const caseData = selectedScenario();
  if (!caseData) return;
  const { metrics, events } = caseData;
  ui.meanWait.textContent = metrics.mean_wait_s.toFixed(2) + " s";
  ui.peakQueue.textContent = String(metrics.max_waiting_queue);
  ui.departed.textContent = String(metrics.completed_by_horizon);
  ui.arrivals.textContent = String(metrics.arrivals);

  cursor = Math.min(cursor, Math.max(0, events.length - 1));
  ui.position.max = String(Math.max(0, events.length - 1));
  ui.position.value = String(cursor);
  ui.positionLabel.textContent = events.length ? (cursor + 1) + " / " + events.length : "0 / 0";
  for (const id of ["reset", "previous", "play", "next", "position"]) {
    ui[id].disabled = events.length === 0;
  }
  if (!events.length) return;
  const event = events[cursor];
  ui.clock.textContent = "t = " + event.time_s.toFixed(3) + " s";
  ui.eventType.textContent = event.event.replaceAll("_", " ");
  ui.description.textContent = event.description +
    (event.blocked && event.server_busy
      ? " An already-started service may continue while the lane is blocked."
      : "");
  ui.phase.textContent = event.phase;
  ui.queue.textContent = String(event.queue_waiting);
  ui.busy.textContent = event.server_busy ? "Yes" : "No";
  ui.blocked.textContent = event.blocked ? "Yes" : "No";
  ui.conservation.textContent = event.conservation_ok ? "PASS" : "FAIL";
  renderChart(events, cursor);
  renderLog(events);
}

function renderComparison() {
  ui.policies.replaceChildren();
  if (!report) return;
  const maxWait = Math.max(1, ...report.scenarios.map((c) => c.metrics.mean_wait_s));
  for (const scenario of report.scenarios) {
    const row = document.createElement("div");
    row.className = "policy-row";
    const label = document.createElement("div");
    label.className = "policy-label";
    label.textContent = scenario.label;
    const note = document.createElement("small");
    note.textContent = "Peak queue: " + scenario.metrics.max_waiting_queue +
      " · Departed by horizon: " + scenario.metrics.completed_by_horizon;
    label.append(note);
    const track = document.createElement("div");
    track.className = "bar-track";
    track.setAttribute("aria-label", "Mean waiting seconds for " + scenario.label);
    const fill = document.createElement("div");
    fill.className = "bar-fill " + scenario.id;
    fill.style.width = (scenario.metrics.mean_wait_s / maxWait * 100) + "%";
    track.append(fill);
    const value = document.createElement("strong");
    value.className = "policy-value";
    value.textContent = scenario.metrics.mean_wait_s.toFixed(2) + " s";
    row.append(label, track, value);
    ui.policies.append(row);
  }
}

function setScenario(index) {
  stopPlayback();
  cursor = Math.max(0, index);
  render();
}

function startPlayback() {
  const events = selectedScenario()?.events ?? [];
  if (!events.length) return;
  if (cursor >= events.length - 1) cursor = 0;
  ui.play.textContent = "Ⅱ Pause";
  playback = setInterval(() => {
    if (cursor >= events.length - 1) {
      stopPlayback();
      return;
    }
    cursor++;
    render();
  }, 180 / Number(ui.speed.value));
  render();
}

ui.file.addEventListener("change", async () => {
  const file = ui.file.files?.[0];
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    setStatus("Trace file is too large (10 MiB maximum).", true);
    return;
  }
  try {
    const incoming = validate(JSON.parse(await file.text()));
    stopPlayback();
    report = incoming;
    cursor = 0;
    ui.scenario.replaceChildren();
    for (const scenario of report.scenarios) {
      ui.scenario.add(new Option(scenario.label, scenario.id));
    }
    ui.scenario.disabled = false;
    ui.pairing.textContent = "Shared arrivals: " + report.parameters.arrival_count +
      " · seed " + report.parameters.seed;
    renderComparison();
    render();
    const priority = report.event_ordering?.priority?.join(" → ") || "see exporter";
    setStatus("Imported " + file.name + ". Identical-time event priority: " + priority +
      ". Trace times displayed to 0.001 s.");
  } catch (error) {
    setStatus("Could not import trace: " + error.message, true);
  }
});
ui.scenario.addEventListener("change", () => setScenario(0));
ui.reset.addEventListener("click", () => setScenario(0));
ui.previous.addEventListener("click", () => {
  stopPlayback();
  cursor = Math.max(0, cursor - 1);
  render();
});
ui.next.addEventListener("click", () => {
  stopPlayback();
  cursor = Math.min((selectedScenario()?.events.length ?? 1) - 1, cursor + 1);
  render();
});
ui.position.addEventListener("input", () => {
  stopPlayback();
  cursor = Number(ui.position.value);
  render();
});
ui.play.addEventListener("click", () => {
  if (playback !== null) stopPlayback();
  else startPlayback();
});
ui.speed.addEventListener("change", () => {
  if (playback !== null) {
    stopPlayback();
    startPlayback();
  }
});
