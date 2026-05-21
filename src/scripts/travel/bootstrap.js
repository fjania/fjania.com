import { initMap } from './map.js';
import { initStats } from './stats.js';
import { initLeaderboards } from './leaderboards.js';
import { initTimeline } from './timeline.js';
import { createState } from './state.js';

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
initTimeline({ state, svg: document.getElementById('timeline-svg') });
initLeaderboards({
  state,
  routesContainer: document.getElementById('lb-routes'),
  airportsContainer: document.getElementById('lb-airports'),
});
