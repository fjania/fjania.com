let tt = null;
let pinned = false;

function ensureEl() {
  if (tt) return tt;
  tt = document.createElement('div');
  tt.className = 'travel-tooltip';
  tt.setAttribute('role', 'tooltip');
  tt.hidden = true;
  document.body.appendChild(tt);

  document.addEventListener('pointerdown', (e) => {
    if (!pinned) return;
    if (e.target instanceof Element && (e.target.closest('.travel-tooltip') || e.target.closest('[data-tt-pin]'))) return;
    hide();
  });
  return tt;
}

function position(x, y) {
  ensureEl();
  const PAD = 12;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  // Render off-screen to measure
  tt.style.left = '-9999px';
  tt.style.top = '-9999px';
  tt.hidden = false;
  const w = tt.offsetWidth;
  const h = tt.offsetHeight;
  let left = x + PAD;
  let top = y + PAD;
  if (left + w > vw - 4) left = Math.max(4, x - PAD - w);
  if (top + h > vh - 4) top = Math.max(4, y - PAD - h);
  tt.style.left = `${left}px`;
  tt.style.top = `${top}px`;
}

export function show(html, x, y, opts = {}) {
  ensureEl();
  tt.innerHTML = html;
  pinned = !!opts.pin;
  position(x, y);
}

export function move(x, y) {
  if (!tt || tt.hidden) return;
  if (pinned) return;
  position(x, y);
}

export function hide() {
  if (!tt) return;
  tt.hidden = true;
  pinned = false;
}
