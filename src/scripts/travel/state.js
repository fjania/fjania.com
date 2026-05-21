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
    focusTrip: null,
  };

  let version = 0;
  let cache = null;
  let cacheTimeline = null;
  let cacheTrips = null;
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
    if (filters.focusTrip && tripKey(f) !== filters.focusTrip) return false;
    return true;
  }

  function tripKey(f) {
    // booking_id is the PNR; some early synthetic ones (JetBlue_09_11_25) are still unique enough
    return f.id.split('-')[0] || f.id;
  }

  function deriveTrips(filtered) {
    const map = new Map();
    for (const f of filtered) {
      const key = tripKey(f);
      if (!map.has(key)) {
        map.set(key, {
          key,
          segments: [],
          airports: new Set(),
          countries: new Set(),
          airlines: new Set(),
          notes: new Set(),
          totalMiles: 0,
          totalMinutes: 0,
          isInternational: false,
        });
      }
      const t = map.get(key);
      t.segments.push(f);
      t.airports.add(f.dep);
      t.airports.add(f.arr);
      if (f.depCountry) t.countries.add(f.depCountry);
      if (f.arrCountry) t.countries.add(f.arrCountry);
      if (f.airline) t.airlines.add(f.airline);
      if (f.notes) t.notes.add(f.notes);
      t.totalMiles += f.distanceMiles || 0;
      t.totalMinutes += f.durationMinutes || 0;
      if (f.isInternational) t.isInternational = true;
    }
    const trips = [];
    for (const t of map.values()) {
      t.segments.sort((a, b) => {
        if (a.depDate !== b.depDate) return a.depDate < b.depDate ? -1 : 1;
        return (a.id < b.id ? -1 : 1);
      });
      const path = [];
      for (let i = 0; i < t.segments.length; i++) {
        const s = t.segments[i];
        if (i === 0) path.push(s.dep);
        if (path[path.length - 1] !== s.dep) path.push(s.dep);
        path.push(s.arr);
      }
      t.path = path;
      t.startDate = t.segments[0].depDate;
      t.endDate = t.segments[t.segments.length - 1].arrDate || t.segments[t.segments.length - 1].depDate;
      t.airportCount = t.airports.size;
      t.countryList = [...t.countries];
      t.airlineList = [...t.airlines];
      t.notesList = [...t.notes];
      trips.push(t);
    }
    trips.sort((a, b) => a.startDate < b.startDate ? 1 : a.startDate > b.startDate ? -1 : 0);
    return trips;
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

  function getFilteredTrips() {
    if (cacheTrips && cacheTrips.version === version) return cacheTrips.value;
    const arr = flights.filter((f) => {
      // trips list shows everything matching filters EXCEPT focusTrip itself,
      // so picking a trip doesn't collapse the list
      if (filters.focusTrip) {
        const saved = filters.focusTrip;
        filters.focusTrip = null;
        const ok = passes(f);
        filters.focusTrip = saved;
        return ok;
      }
      return passes(f);
    });
    const value = deriveTrips(arr);
    cacheTrips = { version, value };
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
    cacheTrips = null;
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
    getFilteredTrips,
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
