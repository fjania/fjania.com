const WIDTH = 960;
const HEIGHT = 120;
const PAD_LEFT = 32;
const PAD_RIGHT = 12;
const PAD_TOP = 8;
const PAD_BOTTOM = 22;
const PLOT_W = WIDTH - PAD_LEFT - PAD_RIGHT;
const PLOT_H = HEIGHT - PAD_TOP - PAD_BOTTOM;
const EPOCH_YEAR = 2009;
const TOTAL_MONTHS = 216; // 2009-01 .. 2026-12 inclusive
const HANDLE_W = 8;

function monthLabel(monthIndex) {
  const y = EPOCH_YEAR + Math.floor(monthIndex / 12);
  const m = (monthIndex % 12) + 1;
  return `${y}-${String(m).padStart(2, '0')}`;
}

function xForMonth(idx) {
  return PAD_LEFT + (idx / TOTAL_MONTHS) * PLOT_W;
}

function monthForX(x) {
  const t = (x - PAD_LEFT) / PLOT_W;
  return Math.max(0, Math.min(TOTAL_MONTHS - 1, Math.round(t * TOTAL_MONTHS)));
}

export function initTimeline({ state, svg }) {
  svg.setAttribute('viewBox', `0 0 ${WIDTH} ${HEIGHT}`);
  svg.innerHTML = '';
  const xmlns = 'http://www.w3.org/2000/svg';

  // Year tick labels
  const gAxis = document.createElementNS(xmlns, 'g');
  gAxis.setAttribute('class', 'tl-axis');
  for (let y = EPOCH_YEAR; y <= EPOCH_YEAR + 17; y += 2) {
    const idx = (y - EPOCH_YEAR) * 12;
    const x = xForMonth(idx);
    const t = document.createElementNS(xmlns, 'text');
    t.setAttribute('x', String(x));
    t.setAttribute('y', String(HEIGHT - 6));
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('class', 'tl-tick');
    t.textContent = String(y);
    gAxis.appendChild(t);
  }
  svg.appendChild(gAxis);

  // Bars layer
  const gBars = document.createElementNS(xmlns, 'g');
  gBars.setAttribute('class', 'g-tl-bars');
  svg.appendChild(gBars);

  // Brush layer (drawn on top of bars but under handles)
  const gBrush = document.createElementNS(xmlns, 'g');
  gBrush.setAttribute('class', 'g-tl-brush');
  svg.appendChild(gBrush);

  const dim = document.createElementNS(xmlns, 'rect');
  dim.setAttribute('class', 'tl-dim');
  dim.setAttribute('y', String(PAD_TOP));
  dim.setAttribute('height', String(PLOT_H));
  gBrush.appendChild(dim);

  const dim2 = document.createElementNS(xmlns, 'rect');
  dim2.setAttribute('class', 'tl-dim');
  dim2.setAttribute('y', String(PAD_TOP));
  dim2.setAttribute('height', String(PLOT_H));
  gBrush.appendChild(dim2);

  const window = document.createElementNS(xmlns, 'rect');
  window.setAttribute('class', 'tl-window');
  window.setAttribute('y', String(PAD_TOP));
  window.setAttribute('height', String(PLOT_H));
  gBrush.appendChild(window);

  function makeHandle(side) {
    const h = document.createElementNS(xmlns, 'rect');
    h.setAttribute('class', `tl-handle tl-handle-${side}`);
    h.setAttribute('y', String(PAD_TOP - 2));
    h.setAttribute('height', String(PLOT_H + 4));
    h.setAttribute('width', String(HANDLE_W));
    h.setAttribute('tabindex', '0');
    h.setAttribute('role', 'slider');
    h.setAttribute('aria-label', side === 'left' ? 'Start month' : 'End month');
    return h;
  }
  const handleL = makeHandle('left');
  const handleR = makeHandle('right');
  gBrush.appendChild(handleL);
  gBrush.appendChild(handleR);

  // Render bars (counts come from getFilteredForTimeline)
  function renderBars() {
    const { flights } = state.getFilteredForTimeline();
    const counts = new Array(TOTAL_MONTHS).fill(0);
    for (const f of flights) {
      if (f.monthIndex >= 0 && f.monthIndex < TOTAL_MONTHS) counts[f.monthIndex]++;
    }
    const max = Math.max(1, ...counts);
    const barW = PLOT_W / TOTAL_MONTHS;
    const innerW = Math.max(1, barW - 0.6);
    gBars.innerHTML = '';
    for (let i = 0; i < TOTAL_MONTHS; i++) {
      if (counts[i] === 0) continue;
      const h = (counts[i] / max) * PLOT_H;
      const rect = document.createElementNS(xmlns, 'rect');
      rect.setAttribute('class', 'tl-bar');
      rect.setAttribute('x', String(xForMonth(i) + (barW - innerW) / 2));
      rect.setAttribute('y', String(PAD_TOP + PLOT_H - h));
      rect.setAttribute('width', String(innerW));
      rect.setAttribute('height', String(h));
      const title = document.createElementNS(xmlns, 'title');
      title.textContent = `${monthLabel(i)} · ${counts[i]} segment${counts[i] === 1 ? '' : 's'}`;
      rect.appendChild(title);
      gBars.appendChild(rect);
    }
  }

  // Render brush window from current state
  function renderBrush() {
    const [lo, hi] = state.filters.monthRange;
    const xl = xForMonth(lo);
    const xr = xForMonth(hi + 1); // selection includes hi
    window.setAttribute('x', String(xl));
    window.setAttribute('width', String(Math.max(0, xr - xl)));
    dim.setAttribute('x', String(PAD_LEFT));
    dim.setAttribute('width', String(Math.max(0, xl - PAD_LEFT)));
    dim2.setAttribute('x', String(xr));
    dim2.setAttribute('width', String(Math.max(0, PAD_LEFT + PLOT_W - xr)));
    handleL.setAttribute('x', String(xl - HANDLE_W / 2));
    handleR.setAttribute('x', String(xr - HANDLE_W / 2));
    handleL.setAttribute('aria-valuetext', monthLabel(lo));
    handleR.setAttribute('aria-valuetext', monthLabel(hi));
  }

  // Pointer drag logic
  let drag = null; // { mode: 'left'|'right'|'window', startX, startLo, startHi }
  function clientToSvgX(clientX) {
    const ctm = svg.getScreenCTM();
    if (!ctm) return clientX;
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = 0;
    return pt.matrixTransform(ctm.inverse()).x;
  }

  function onPointerDown(mode) {
    return (e) => {
      e.preventDefault();
      try { svg.setPointerCapture(e.pointerId); } catch (_) {}
      const [lo, hi] = state.filters.monthRange;
      drag = {
        mode,
        startX: clientToSvgX(e.clientX),
        startLo: lo,
        startHi: hi,
        pointerId: e.pointerId,
      };
    };
  }
  function onPointerMove(e) {
    if (!drag) return;
    const x = clientToSvgX(e.clientX);
    if (drag.mode === 'left') {
      const lo = Math.min(drag.startHi, monthForX(x));
      state.setMonthRange(lo, drag.startHi);
    } else if (drag.mode === 'right') {
      const hi = Math.max(drag.startLo, monthForX(x));
      state.setMonthRange(drag.startLo, hi);
    } else if (drag.mode === 'window') {
      const dxMonths = Math.round(((x - drag.startX) / PLOT_W) * TOTAL_MONTHS);
      const width = drag.startHi - drag.startLo;
      let lo = drag.startLo + dxMonths;
      let hi = drag.startHi + dxMonths;
      if (lo < 0) { hi -= lo; lo = 0; }
      if (hi > TOTAL_MONTHS - 1) { lo -= (hi - (TOTAL_MONTHS - 1)); hi = TOTAL_MONTHS - 1; }
      state.setMonthRange(lo, hi);
    } else if (drag.mode === 'create') {
      const x0 = monthForX(drag.startX);
      const x1 = monthForX(x);
      state.setMonthRange(Math.min(x0, x1), Math.max(x0, x1));
    }
  }
  function onPointerUp(e) {
    if (drag) {
      try { svg.releasePointerCapture(drag.pointerId); } catch (_) {}
      drag = null;
    }
  }

  handleL.addEventListener('pointerdown', onPointerDown('left'));
  handleR.addEventListener('pointerdown', onPointerDown('right'));
  window.addEventListener('pointerdown', onPointerDown('window'));
  svg.addEventListener('pointermove', onPointerMove);
  svg.addEventListener('pointerup', onPointerUp);
  svg.addEventListener('pointercancel', onPointerUp);

  // Keyboard support on handles
  function handleKey(side) {
    return (e) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      e.preventDefault();
      const [lo, hi] = state.filters.monthRange;
      const step = e.shiftKey ? 12 : 1;
      if (side === 'left') {
        if (e.key === 'ArrowLeft') state.setMonthRange(Math.max(0, lo - step), hi);
        if (e.key === 'ArrowRight') state.setMonthRange(Math.min(hi, lo + step), hi);
        if (e.key === 'Home') state.setMonthRange(0, hi);
        if (e.key === 'End') state.setMonthRange(hi, hi);
      } else {
        if (e.key === 'ArrowLeft') state.setMonthRange(lo, Math.max(lo, hi - step));
        if (e.key === 'ArrowRight') state.setMonthRange(lo, Math.min(TOTAL_MONTHS - 1, hi + step));
        if (e.key === 'Home') state.setMonthRange(lo, lo);
        if (e.key === 'End') state.setMonthRange(lo, TOTAL_MONTHS - 1);
      }
    };
  }
  handleL.addEventListener('keydown', handleKey('left'));
  handleR.addEventListener('keydown', handleKey('right'));

  state.subscribe(() => {
    renderBars();
    renderBrush();
  });
  renderBars();
  renderBrush();
}
