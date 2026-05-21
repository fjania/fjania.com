import { formatNumber, formatMiles, formatDuration } from './format.js';

const ITEMS = [
  { key: 'flightCount', label: 'Segments', value: (s) => formatNumber(s.flightCount) },
  { key: 'totalMiles', label: 'Miles flown', value: (s) => formatMiles(s.totalMiles) },
  { key: 'equator', label: '× around the equator', value: (s) => s.equatorRatio.toFixed(1) + '×' },
  { key: 'duration', label: 'Time in the air', value: (s) => formatDuration(s.totalMinutes) },
  { key: 'airports', label: 'Airports', value: (s) => formatNumber(s.airports) },
  { key: 'countries', label: 'Countries', value: (s) => formatNumber(s.countries) },
  { key: 'longest', label: 'Longest leg', value: (s) => s.longest ? `${s.longest.route} · ${formatMiles(s.longest.distanceMiles)}` : '—' },
];

export function initStats({ state, container }) {
  function render() {
    const { stats } = state.getFiltered();
    container.innerHTML = ITEMS.map((it) => `
      <div class="stat">
        <div class="stat-value">${it.value(stats)}</div>
        <div class="stat-label">${it.label}</div>
      </div>
    `).join('');
  }
  state.subscribe(render);
  render();
}
