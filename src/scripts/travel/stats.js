import { formatNumber, formatMiles, formatDuration } from './format.js';

const ITEMS = [
  { label: 'segments', value: (s) => formatNumber(s.flightCount) },
  { label: 'miles', value: (s) => formatMiles(s.totalMiles).replace(' mi', '') },
  { label: '× equator', value: (s) => s.equatorRatio.toFixed(1) + '×' },
  { label: 'in the air', value: (s) => formatDuration(s.totalMinutes) },
  { label: 'airports', value: (s) => formatNumber(s.airports) },
  { label: 'countries', value: (s) => formatNumber(s.countries) },
  {
    label: (s) => s.longest ? `longest · ${s.longest.route}` : 'longest',
    value: (s) => s.longest ? formatMiles(s.longest.distanceMiles).replace(' mi', '') + ' mi' : '—',
  },
];

function resolve(field, stats) {
  return typeof field === 'function' ? field(stats) : field;
}

export function initStats({ state, container }) {
  function render() {
    const { stats } = state.getFiltered();
    container.innerHTML = ITEMS.map((it) => `
      <span class="stat-pair">
        <span class="stat-num">${resolve(it.value, stats)}</span>
        <span class="stat-cap">${resolve(it.label, stats)}</span>
      </span>
    `).join('<span class="stat-sep" aria-hidden="true">·</span>');
  }
  state.subscribe(render);
  render();
}
