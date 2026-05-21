import { formatDate, formatMiles } from './format.js';

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function tripDateRange(t) {
  const a = formatDate(t.startDate);
  if (t.startDate === t.endDate) return a;
  const b = formatDate(t.endDate);
  return `${a} – ${b}`;
}

function pathHtml(t) {
  return t.path.map((iata, i) => {
    const sep = i === 0 ? '' : '<span class="trip-arrow">›</span>';
    return `${sep}<span class="trip-iata">${escapeHtml(iata)}</span>`;
  }).join('');
}

function tripCardHtml(t, isFocused) {
  const intl = t.isInternational ? '<span class="trip-tag trip-tag-intl">Intl</span>' : '';
  const segCount = t.segments.length;
  const noteSnippet = t.notesList[0] ? `<div class="trip-note">${escapeHtml(t.notesList[0])}</div>` : '';
  return `
    <li class="trip-card${isFocused ? ' focused' : ''}" data-key="${escapeHtml(t.key)}" tabindex="0">
      <div class="trip-date">${tripDateRange(t)}${intl}</div>
      <div class="trip-path">${pathHtml(t)}</div>
      <div class="trip-meta">
        ${segCount} seg${segCount === 1 ? '' : 's'} ·
        ${formatMiles(t.totalMiles)} ·
        ${escapeHtml(t.airlineList.join(', '))}
      </div>
      ${noteSnippet}
    </li>
  `;
}

export function initTrips({ state, container, countEl }) {
  function render() {
    const trips = state.getFilteredTrips();
    const focused = state.filters.focusTrip;
    if (countEl) countEl.textContent = `${trips.length} trip${trips.length === 1 ? '' : 's'}`;
    if (trips.length === 0) {
      container.innerHTML = '<p class="trips-empty">No trips match the current filters.</p>';
      return;
    }
    container.innerHTML = `<ul class="trips-list">${trips.map((t) => tripCardHtml(t, t.key === focused)).join('')}</ul>`;
    if (focused) {
      const el = container.querySelector(`.trip-card[data-key="${CSS.escape(focused)}"]`);
      if (el) el.scrollIntoView({ block: 'nearest' });
    }
  }

  function setFocus(key) {
    const next = state.filters.focusTrip === key ? null : key;
    state.setFilter('focusTrip', next);
  }

  container.addEventListener('click', (e) => {
    const card = e.target.closest('.trip-card');
    if (!card) return;
    setFocus(card.dataset.key);
  });
  container.addEventListener('keydown', (e) => {
    const card = e.target.closest('.trip-card');
    if (!card) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setFocus(card.dataset.key);
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const cards = [...container.querySelectorAll('.trip-card')];
      const i = cards.indexOf(card);
      const next = cards[e.key === 'ArrowDown' ? Math.min(cards.length - 1, i + 1) : Math.max(0, i - 1)];
      if (next) next.focus();
    }
  });

  state.subscribe(render);
  render();
}
