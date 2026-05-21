function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

const STATUSES = [
  { key: 'taken', label: 'Taken' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'cancelled', label: 'Cancelled' },
  { key: 'rescheduled', label: 'Rescheduled' },
];

const GEO_SCOPES = [
  { key: 'domestic', label: 'Domestic' },
  { key: 'international', label: 'International' },
];

const BOOKING_SCOPES = [
  { key: 'personal', label: 'Personal' },
  { key: 'work', label: 'Work' },
];

function renderGroup(label, group, items, activeSet) {
  return `
    <div class="filter-group" data-group="${group}">
      <span class="filter-label">${label}</span>
      <div class="filter-chips">
        ${items.map((it) => `
          <a href="#" class="filter-chip${activeSet.has(it.key) ? ' active' : ''}" data-value="${escapeHtml(it.key)}">${escapeHtml(it.label)}</a>
        `).join('')}
      </div>
    </div>
  `;
}

export function initFilters({ state, container }) {
  const airlines = [...new Set(state.flights.map((f) => f.airline).filter(Boolean))].sort();
  const airlineItems = airlines.map((a) => ({ key: a, label: a }));

  function render() {
    container.innerHTML = `
      ${renderGroup('Status', 'statuses', STATUSES, state.filters.statuses)}
      ${renderGroup('Scope', 'geoScopes', GEO_SCOPES, state.filters.geoScopes)}
      ${renderGroup('Trip type', 'bookingScopes', BOOKING_SCOPES, state.filters.bookingScopes)}
      ${renderGroup('Airline', 'airlines', airlineItems, state.filters.airlines)}
    `;
  }

  container.addEventListener('click', (e) => {
    const chip = e.target.closest('.filter-chip');
    if (!chip) return;
    e.preventDefault();
    const group = chip.closest('.filter-group')?.dataset.group;
    const value = chip.dataset.value;
    if (!group || value == null) return;
    state.toggleSetFilter(group, value);
  });

  state.subscribe(render);
  render();
}
