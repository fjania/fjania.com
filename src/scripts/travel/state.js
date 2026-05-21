const EPOCH_YEAR = 2009;
const MAX_MONTH_INDEX = 215; // 2026-12

const WORK_CHANNELS = new Set([
  'Amex GBT (work)',
  'Navan (work)',
  'Egencia (work)',
]);

function bookingScope(channel) {
  return WORK_CHANNELS.has(channel) ? 'work' : 'personal';
}

export function createState(flights) {
  const filters = {
    monthRange: [0, MAX_MONTH_INDEX],
    airlines: new Set(),
    bookingScopes: new Set(),
    geoScopes: new Set(),
    statuses: new Set(['taken']),
    focusAirport: null,
    focusRoute: null,
  };

  let version = 0;
  let cache = null;
  let cacheTimeline = null;
  const subscribers = [];

  function passes(f, opts) {
    const { skipMonthRange = false } = opts || {};
    if (!skipMonthRange) {
      const [lo, hi] = filters.monthRange;
      if (f.monthIndex < lo || f.monthIndex > hi) return false;
    }
    if (filters.airlines.size && !filters.airlines.has(f.airline)) return false;
    if (filters.bookingScopes.size && !filters.bookingScopes.has(bookingScope(f.bookingChannel))) return false;
    if (filters.geoScopes.size) {
      const scope = f.isInternational ? 'international' : 'domestic';
      if (!filters.geoScopes.has(scope)) return false;
    }
    if (filters.statuses.size && !filters.statuses.has(f.status)) return false;
    if (filters.focusAirport && f.dep !== filters.focusAirport && f.arr !== filters.focusAirport) return false;
    if (filters.focusRoute && f.route !== filters.focusRoute) return false;
    return true;
  }

  function deriveAirports(filtered) {
    const map = new Map();
    for (const f of filtered) {
      if (!map.has(f.dep)) map.set(f.dep, { iata: f.dep, city: f.depCity, country: f.depCountry, lat: f.depLat, lon: f.depLon, count: 0 });
      if (!map.has(f.arr)) map.set(f.arr, { iata: f.arr, city: f.arrCity, country: f.arrCountry, lat: f.arrLat, lon: f.arrLon, count: 0 });
      map.get(f.dep).count++;
      map.get(f.arr).count++;
    }
    return [...map.values()].sort((a, b) => b.count - a.count);
  }

  function deriveRoutes(filtered) {
    const map = new Map();
    for (const f of filtered) {
      const key = f.route;
      if (!key) continue;
      if (!map.has(key)) map.set(key, { key, a: key.split('-')[0], b: key.split('-')[1], count: 0, totalMiles: 0 });
      const r = map.get(key);
      r.count++;
      r.totalMiles += f.distanceMiles || 0;
    }
    return [...map.values()].sort((a, b) => b.count - a.count);
  }

  function deriveStats(filtered) {
    let totalMiles = 0;
    let totalMinutes = 0;
    const airports = new Set();
    const countries = new Set();
    let longest = null;
    for (const f of filtered) {
      totalMiles += f.distanceMiles || 0;
      totalMinutes += f.durationMinutes || 0;
      airports.add(f.dep);
      airports.add(f.arr);
      if (f.depCountry) countries.add(f.depCountry);
      if (f.arrCountry) countries.add(f.arrCountry);
      if (!longest || (f.distanceMiles || 0) > (longest.distanceMiles || 0)) longest = f;
    }
    const EARTH_CIRCUMFERENCE_MI = 24901;
    return {
      flightCount: filtered.length,
      totalMiles,
      equatorRatio: totalMiles / EARTH_CIRCUMFERENCE_MI,
      totalMinutes,
      airports: airports.size,
      countries: countries.size,
      longest,
    };
  }

  function getFiltered() {
    if (cache && cache.version === version) return cache.value;
    const arr = flights.filter((f) => passes(f));
    const airports = deriveAirports(arr);
    const routes = deriveRoutes(arr);
    const stats = deriveStats(arr);
    const value = { flights: arr, airports, routes, stats };
    cache = { version, value };
    return value;
  }

  function getFilteredForTimeline() {
    if (cacheTimeline && cacheTimeline.version === version) return cacheTimeline.value;
    const arr = flights.filter((f) => passes(f, { skipMonthRange: true }));
    const value = { flights: arr };
    cacheTimeline = { version, value };
    return value;
  }

  function notify() {
    cache = null;
    cacheTimeline = null;
    version++;
    for (const fn of subscribers) fn();
  }

  function setFilter(key, value) {
    filters[key] = value;
    notify();
  }

  function toggleSetFilter(key, value) {
    const s = filters[key];
    if (s.has(value)) s.delete(value);
    else s.add(value);
    notify();
  }

  function setMonthRange(lo, hi) {
    filters.monthRange = [Math.max(0, lo), Math.min(MAX_MONTH_INDEX, hi)];
    notify();
  }

  function subscribe(fn) {
    subscribers.push(fn);
    return () => {
      const i = subscribers.indexOf(fn);
      if (i >= 0) subscribers.splice(i, 1);
    };
  }

  return {
    filters,
    flights,
    EPOCH_YEAR,
    MAX_MONTH_INDEX,
    bookingScope,
    getFiltered,
    getFilteredForTimeline,
    setFilter,
    toggleSetFilter,
    setMonthRange,
    subscribe,
    notify,
  };
}

export function monthIndexToYear(idx) {
  return EPOCH_YEAR + Math.floor(idx / 12);
}

export function yearToMonthIndex(year, month = 1) {
  return (year - EPOCH_YEAR) * 12 + (month - 1);
}
