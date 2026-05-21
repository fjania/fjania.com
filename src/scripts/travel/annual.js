import { yearToMonthIndex } from './state.js';

const FIRST_YEAR = 2009;
const LAST_YEAR = 2026;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function initAnnual({ state, container }) {
  function render() {
    const { flights } = state.getFilteredForTimeline();
    const counts = new Map();
    for (let y = FIRST_YEAR; y <= LAST_YEAR; y++) counts.set(y, 0);
    for (const f of flights) {
      if (counts.has(f.year)) counts.set(f.year, counts.get(f.year) + 1);
    }
    const max = Math.max(1, ...counts.values());
    const [lo, hi] = state.filters.monthRange;

    const rows = [];
    for (let y = LAST_YEAR; y >= FIRST_YEAR; y--) {
      const n = counts.get(y);
      const pct = (n / max) * 100;
      const yLo = yearToMonthIndex(y, 1);
      const yHi = yearToMonthIndex(y, 12);
      const active = yLo === lo && yHi === hi;
      rows.push(`
        <li class="yr-row${active ? ' active' : ''}${n === 0 ? ' empty' : ''}" data-year="${y}" tabindex="0">
          <span class="yr-num">${y}</span>
          <span class="yr-bar-cell">
            <span class="yr-bar" style="width: ${pct.toFixed(1)}%"></span>
          </span>
          <span class="yr-count">${n}</span>
        </li>
      `);
    }
    container.innerHTML = `<ol class="yr-list">${rows.join('')}</ol>`;
  }

  container.addEventListener('click', (e) => {
    const row = e.target.closest('.yr-row');
    if (!row) return;
    const y = Number(row.dataset.year);
    if (!y) return;
    const lo = yearToMonthIndex(y, 1);
    const hi = yearToMonthIndex(y, 12);
    const [curLo, curHi] = state.filters.monthRange;
    // Toggle: if this year is already the selected range, reset to full
    if (curLo === lo && curHi === hi) {
      state.setMonthRange(0, state.MAX_MONTH_INDEX);
    } else {
      state.setMonthRange(lo, hi);
    }
  });
  container.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const row = e.target.closest('.yr-row');
    if (!row) return;
    e.preventDefault();
    row.click();
  });

  state.subscribe(render);
  render();
}
