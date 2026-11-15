/* Cyclistics experimental map. No invented geographic pins or field validation. */
const el = {
  map: document.querySelector("#map"),
  file: document.querySelector("#geojson-file"),
  scenario: document.querySelector("#scenario-filter"),
  maxTime: document.querySelector("#max-time"),
  timeLabel: document.querySelector("#max-time-label"),
  count: document.querySelector("#visible-count"),
  scenarios: document.querySelector("#scenario-count"),
  message: document.querySelector("#message"),
};
let original = [];
let activeLayer = null;
let objectUrl = null;
let ready = false;

function message(value, failed = false) {
  el.message.textContent = value;
  el.message.style.color = failed ? "#ffc9a9" : "#c5ead9";
}

function validateGeoJson(value) {
  if (!value || value.type !== "FeatureCollection" || !Array.isArray(value.features)) {
    throw Error("Expected a GeoJSON FeatureCollection of WGS84 points.");
  }
  if (value.features.length > 10000) throw Error("Maximum 10,000 features per file.");
  for (const f of value.features) {
    const coords = f.geometry?.coordinates;
    if (f.type !== "Feature" || f.geometry?.type !== "Point" ||
        !Array.isArray(coords) || coords.length !== 2 ||
        !coords.every(Number.isFinite) ||
        coords[0] < -180 || coords[0] > 180 || coords[1] < -90 || coords[1] > 90) {
      throw Error("All features must contain valid WGS84 point coordinates.");
    }
    const p = f.properties;
    if (!p || typeof p.scenario_id !== "string" || !p.scenario_id ||
        typeof p.location_source !== "string" || !p.location_source ||
        !["simulated", "provisional_nyc_count"].includes(p.data_status) ||
        !Number.isInteger(p.simulated_time_s) || p.simulated_time_s < 0 ||
        typeof p.event_type !== "string" ||
        !Number.isFinite(p.mean_queue_cyclists) || p.mean_queue_cyclists < 0) {
      throw Error("Each point needs a scenario, source, status, time and queue count.");
    }
  }
  return value.features;
}

function filtered() {
  const scenario = el.scenario.value;
  const time = Number(el.maxTime.value);
  return original.filter((f) =>
    (scenario === "all" || f.properties.scenario_id === scenario) &&
    f.properties.simulated_time_s <= time);
}

async function render() {
  if (!ready) return;
  const data = filtered();
  el.count.textContent = String(data.length);
  el.timeLabel.textContent = el.maxTime.value + " s (simulated)";
  if (activeLayer) {
    el.map.map.remove(activeLayer);
    activeLayer.destroy();
    activeLayer = null;
  }
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = null;
  if (data.length === 0) {
    message("No points match this scenario and simulation time.");
    return;
  }
  const GeoJSONLayer = await $arcgis.import("@arcgis/core/layers/GeoJSONLayer.js");
  objectUrl = URL.createObjectURL(new Blob(
    [JSON.stringify({type: "FeatureCollection", features: data})],
    {type: "application/geo+json"}
  ));
  const layer = new GeoJSONLayer({
    url: objectUrl,
    title: "Cyclistics v2 scenarios — synthetic or provisional",
    copyright: "User-provided coordinates; simulation is not field validated",
    popupTemplate: {
      title: "{scenario_id} - {event_type}",
      content: "Status: {data_status}<br>Source: {location_source}" +
               "<br>Simulated time: {simulated_time_s} s" +
               "<br>Mean waiting cyclists: {mean_queue_cyclists}",
    },
    renderer: {
      type: "unique-value", field: "data_status",
      uniqueValueInfos: [
        {value: "simulated",
         symbol: {type: "simple-marker", color: "#33bd9b", size: 11,
                  outline: {color: "#173332", width: 1.5}}},
        {value: "provisional_nyc_count",
         symbol: {type: "simple-marker", color: "#eab967", size: 11,
                  outline: {color: "#173332", width: 1.5}}},
      ],
    },
  });
  el.map.map.add(layer);
  try {
    await layer.load();
    if (layer.fullExtent) {
      await el.map.goTo(layer.fullExtent.expand(1.5)).catch(() => {});
    }
    activeLayer = layer;
    message(String(data.length) + " imported points shown with provenance labels.");
  } catch (error) {
    el.map.map.remove(layer);
    layer.destroy();
    message("Could not load GeoJSON layer: " + error.message, true);
  }
}

function updateFilters(data) {
  original = data;
  const names = [...new Set(data.map((f) => f.properties.scenario_id))].sort();
  el.scenario.replaceChildren(new Option("All scenarios", "all"));
  names.forEach((name) => el.scenario.add(new Option(name, name)));
  el.scenario.disabled = names.length === 0;
  el.scenarios.textContent = String(names.length);
  el.maxTime.max = String(Math.max(1, ...data.map((f) => f.properties.simulated_time_s)));
  el.maxTime.value = el.maxTime.max;
  el.maxTime.disabled = data.length === 0;
}

el.file.addEventListener("change", async () => {
  const file = el.file.files?.[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    message("File too large; use a GeoJSON under 5 MiB.", true);
    return;
  }
  try {
    const features = validateGeoJson(JSON.parse(await file.text()));
    updateFilters(features);
    if (ready) await render();
    else message("Data validated; map is still initializing.");
  } catch (error) {
    message("Invalid scenario file: " + error.message, true);
  }
});
el.scenario.addEventListener("change", () => void render());
el.maxTime.addEventListener("input", () => void render());

(async () => {
  try {
    await customElements.whenDefined("arcgis-map");
    await el.map.viewOnReady();
    ready = true;
    if (original.length) await render();
  } catch (error) {
    message("Map could not start: " + error.message, true);
  }
})();
