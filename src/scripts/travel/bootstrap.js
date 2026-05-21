import { initMap } from './map.js';
import { createState, yearToMonthIndex } from './state.js';

function readJsonIsland(id) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing JSON island: ${id}`);
  return JSON.parse(el.textContent);
}

const flights = readJsonIsland('travel-flights');
const world = readJsonIsland('travel-world');

const state = createState(flights);
window.__travel = { state }; // dev hook

initMap({ state, world });

// Minimal year-range filter (will be replaced by brush in a later phase)
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
