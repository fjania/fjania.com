import { formatNumber, formatMiles, formatDuration } from './format.js';

const ITEMS = [
  { label: 'Segments', value: (s) => formatNumber(s.flightCount) },
  { label: 'Miles flown', value: (s) => formatMiles(s.totalMiles) },
  { label: '× around the equator', value: (s) => s.equatorRatio.toFixed(1) + '×' },
  { label: 'Time in the air', value: (s) => formatDuration(s.totalMinutes) },
  { label: 'Airports', value: (s) => formatNumber(s.airports) },
  { label: 'Countries', value: (s) => formatNumber(s.countries) },
  {
    label: (s) => s.longest ? `Longest · ${s.longest.route}` : 'Longest leg',
    value: (s) => s.longest ? formatMiles(s.longest.distanceMiles) : '—',
  },
];

function resolve(field, stats) {
  return typeof field === 'function' ? field(stats) : field;
}

export function initStats({ state, container }) {
  function render() {
    const { stats } = state.getFiltered();
    container.innerHTML = ITEMS.map((it) => `
      <div class="stat">
        <div class="stat-value">${resolve(it.value, stats)}</div>
        <div class="stat-label">${resolve(it.label, stats)}</div>
      </div>
    `).join('');
  }
  state.subscribe(render);
  render();
}
