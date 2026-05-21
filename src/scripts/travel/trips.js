import { formatMiles } from './format.js';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function parseIso(iso) {
  const clean = (iso || '').replace(/^[^0-9]/, '');
  const y = Number(clean.slice(0, 4));
  const m = Number(clean.slice(5, 7));
  const d = Number(clean.slice(8, 10));
  return { y, m, d };
}

function compactDateRange(start, end) {
  const a = parseIso(start);
  const b = parseIso(end);
  if (!a.m || !a.d) return '';
  if (start === end || (a.y === b.y && a.m === b.m && a.d === b.d)) {
    return `${MONTHS[a.m - 1]} ${a.d}`;
  }
  if (a.y === b.y && a.m === b.m) {
    return `${MONTHS[a.m - 1]} ${a.d}–${b.d}`;
  }
  return `${MONTHS[a.m - 1]} ${a.d} – ${MONTHS[b.m - 1]} ${b.d}`;
}

function pathHtml(t) {
  return t.path.map((iata, i) => {
    const sep = i === 0 ? '' : '<span class="trip-arrow">›</span>';
    return `${sep}<span class="trip-iata">${escapeHtml(iata)}</span>`;
  }).join('');
}

function tripCardHtml(t, isFocused) {
  const intl = t.isInternational ? '<span class="trip-tag-intl" aria-label="international">●</span>' : '';
  const date = compactDateRange(t.startDate, t.endDate);
  const note = t.notesList[0] || '';
  return `
    <li class="trip-card${isFocused ? ' focused' : ''}" data-key="${escapeHtml(t.key)}" tabindex="0"${note ? ` title="${escapeHtml(note)}"` : ''}>
      <div class="trip-row">
        <span class="trip-date-compact">${escapeHtml(date)}${intl}</span>
        <span class="trip-path">${pathHtml(t)}</span>
        <span class="trip-meta-compact">${t.segments.length}·${formatMiles(t.totalMiles).replace(' mi', '')}</span>
      </div>
    </li>
  `;
}

function groupByYear(trips) {
  const groups = new Map();
  for (const t of trips) {
    const y = parseIso(t.startDate).y;
    if (!groups.has(y)) groups.set(y, []);
    groups.get(y).push(t);
  }
  return [...groups.entries()].sort((a, b) => b[0] - a[0]);
}

export function initTrips({ state, container, countEl, onTripHover }) {
  let prevRange = state.filters.monthRange.slice();

  function maybeScrollToBrush() {
    const [lo, hi] = state.filters.monthRange;
    if (lo === prevRange[0] && hi === prevRange[1]) return;
    prevRange = [lo, hi];
    if (state.filters.focusTrip) return; // focused trip scroll handled in render
    // trips are newest first; find the newest trip whose start month is within [lo, hi]
    const trips = state.getFilteredTrips();
    const target = trips.find((t) => {
      const m = t.segments[0]?.monthIndex;
      return Number.isFinite(m) && m >= lo && m <= hi;
    });
    if (!target) return;
    const el = container.querySelector(`.trip-card[data-key="${CSS.escape(target.key)}"]`);
    if (!el) return;
    // scroll the trip's year header into view (slightly above the card)
    const yearHeader = el.closest('.trips-year-group')?.querySelector('.trips-year-header');
    (yearHeader || el).scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  function render() {
    const trips = state.getFilteredTrips();
    const focused = state.filters.focusTrip;
    if (countEl) countEl.textContent = `${trips.length} trip${trips.length === 1 ? '' : 's'}`;
    if (trips.length === 0) {
      container.innerHTML = '<p class="trips-empty">No trips match the current filters.</p>';
      return;
    }
    const groups = groupByYear(trips);
    container.innerHTML = groups.map(([year, items]) => {
      const segs = items.reduce((n, t) => n + t.segments.length, 0);
      return `
        <div class="trips-year-group">
          <div class="trips-year-header">
            <span class="trips-year">${year}</span>
            <span class="trips-year-count">${items.length} trip${items.length === 1 ? '' : 's'} · ${segs} seg${segs === 1 ? '' : 's'}</span>
          </div>
          <ul class="trips-list">${items.map((t) => tripCardHtml(t, t.key === focused)).join('')}</ul>
        </div>
      `;
    }).join('');
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

  if (onTripHover) {
    container.addEventListener('pointerover', (e) => {
      const card = e.target.closest('.trip-card');
      if (!card) return;
      onTripHover(card.dataset.key);
    });
    container.addEventListener('pointerleave', () => onTripHover(null));
    container.addEventListener('focusin', (e) => {
      const card = e.target.closest('.trip-card');
      if (card) onTripHover(card.dataset.key);
    });
    container.addEventListener('focusout', () => onTripHover(null));
  }
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

  state.subscribe(() => {
    render();
    maybeScrollToBrush();
  });
  render();
}
