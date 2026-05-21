import { initMap } from './map.js';

function readJsonIsland(id) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing JSON island: ${id}`);
  return JSON.parse(el.textContent);
}

const flights = readJsonIsland('travel-flights');
const world = readJsonIsland('travel-world');

initMap({ flights, world });
