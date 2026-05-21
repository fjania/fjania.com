export function formatNumber(n) {
  if (!Number.isFinite(n)) return '—';
  return Math.round(n).toLocaleString('en-US');
}

export function formatMiles(n) {
  if (!Number.isFinite(n)) return '—';
  return `${Math.round(n).toLocaleString('en-US')} mi`;
}

export function formatDuration(minutes) {
  if (!Number.isFinite(minutes) || minutes <= 0) return '—';
  const days = Math.floor(minutes / (60 * 24));
  const hours = Math.floor((minutes % (60 * 24)) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

export function formatDate(iso) {
  if (!iso) return '—';
  const clean = iso.replace(/^[^0-9]/, '');
  const parts = clean.split('-');
  if (parts.length < 3) return iso;
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const m = Number(parts[1]);
  if (!m) return iso;
  return `${months[m - 1]} ${Number(parts[2])}, ${parts[0]}`;
}
