import { initMap } from './map.js';
import { initStats } from './stats.js';
import { initLeaderboards } from './leaderboards.js';
import { createState, yearToMonthIndex } from './state.js';

function readJsonIsland(id) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing JSON island: ${id}`);
  return JSON.parse(el.textContent);
}

const flights = readJsonIsland('travel-flights');
const world = readJsonIsland('travel-world');

const state = createState(flights);
window.__travel = { state };

initStats({ state, container: document.getElementById('stats') });
initMap({ state, world });
initLeaderboards({
  state,
  routesContainer: document.getElementById('lb-routes'),
  airportsContainer: document.getElementById('lb-airports'),
});

function wireYearInputs() {
  const minEl = document.getElementById('year-min');
  const maxEl = document.getElementById('year-max');
  if (!minEl || !maxEl) return;
  const apply = () => {
    const yMin = Number(minEl.value) || 2009;
    const yMax = Number(maxEl.value) || 2026;
    state.setMonthRange(yearToMonthIndex(yMin, 1), yearToMonthIndex(yMax, 12));
  };
  minEl.addEventListener('change', apply);
  maxEl.addEventListener('change', apply);
}

wireYearInputs();
