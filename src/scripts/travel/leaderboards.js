const TOP_N = 10;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function rowsHtml(items, maxCount, getLabel, focusedKey) {
  return items.map((it) => {
    const pct = maxCount > 0 ? (it.count / maxCount) * 100 : 0;
    const isFocused = focusedKey != null && focusedKey === it.__key;
    return `
      <li class="lb-row${isFocused ? ' focused' : ''}" data-key="${escapeHtml(it.__key)}" tabindex="0">
        <div class="lb-bar" style="width: ${pct.toFixed(1)}%"></div>
        <div class="lb-row-content">
          <span class="lb-label">${getLabel(it)}</span>
          <span class="lb-count">${it.count}</span>
        </div>
      </li>
    `;
  }).join('');
}

export function initLeaderboards({ state, routesContainer, airportsContainer }) {
  function render() {
    const { routes, airports } = state.getFiltered();

    const topRoutes = routes.slice(0, TOP_N).map((r) => ({ ...r, __key: r.key }));
    const maxR = topRoutes.length ? topRoutes[0].count : 0;
    routesContainer.innerHTML = topRoutes.length
      ? `<ol class="lb-list">${rowsHtml(topRoutes, maxR, (r) => `<strong>${escapeHtml(r.key)}</strong>`, state.filters.focusRoute)}</ol>`
      : '<p class="lb-empty">No routes match the current filters.</p>';

    const topAirports = airports.slice(0, TOP_N).map((a) => ({ ...a, __key: a.iata }));
    const maxA = topAirports.length ? topAirports[0].count : 0;
    airportsContainer.innerHTML = topAirports.length
      ? `<ol class="lb-list">${rowsHtml(topAirports, maxA, (a) => `<strong>${escapeHtml(a.iata)}</strong> <span class="lb-sub">${escapeHtml(a.city || '')}</span>`, state.filters.focusAirport)}</ol>`
      : '<p class="lb-empty">No airports match the current filters.</p>';
  }

  function handleClick(container, kind) {
    container.addEventListener('click', (e) => {
      const row = e.target.closest('.lb-row');
      if (!row) return;
      const key = row.dataset.key;
      const prop = kind === 'route' ? 'focusRoute' : 'focusAirport';
      const next = state.filters[prop] === key ? null : key;
      state.setFilter(prop, next);
    });
    container.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const row = e.target.closest('.lb-row');
      if (!row) return;
      e.preventDefault();
      const key = row.dataset.key;
      const prop = kind === 'route' ? 'focusRoute' : 'focusAirport';
      const next = state.filters[prop] === key ? null : key;
      state.setFilter(prop, next);
    });
  }

  handleClick(routesContainer, 'route');
  handleClick(airportsContainer, 'airport');
  state.subscribe(render);
  render();
}
