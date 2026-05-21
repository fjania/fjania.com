export interface Flight {
  id: string;
  airline: string;
  flightNumber: string;
  depDate: string;
  arrDate: string;
  dep: string;
  arr: string;
  depCity: string;
  depCountry: string;
  arrCity: string;
  arrCountry: string;
  depLat: number;
  depLon: number;
  arrLat: number;
  arrLon: number;
  distanceMiles: number;
  durationMinutes: number;
  isInternational: boolean;
  route: string;
  year: number;
  month: number;
  monthIndex: number;
  dayOfWeek: string;
  bookingChannel: string;
  status: string;
  cabinClass: string;
  seat: string;
  notes: string;
}

const EPOCH_YEAR = 2009;

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else {
      if (c === '"') {
        inQuotes = true;
      } else if (c === ',') {
        row.push(field);
        field = '';
      } else if (c === '\n') {
        row.push(field);
        rows.push(row);
        row = [];
        field = '';
      } else if (c === '\r') {
        // ignore
      } else {
        field += c;
      }
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function num(v: string): number {
  if (!v) return NaN;
  const n = Number(v);
  return Number.isFinite(n) ? n : NaN;
}

function monthIndexFromDate(iso: string): number {
  // iso may be like '2018-06-04' or '~2018-06-04'; strip leading non-digits
  const clean = iso.replace(/^[^0-9]/, '');
  const y = Number(clean.slice(0, 4));
  const m = Number(clean.slice(5, 7));
  if (!y || !m) return NaN;
  return (y - EPOCH_YEAR) * 12 + (m - 1);
}

export function parseFlights(csvText: string): Flight[] {
  const rows = parseCsv(csvText);
  if (rows.length < 2) return [];
  const header = rows[0];
  const idx = (name: string) => header.indexOf(name);

  const cBooking = idx('booking_id');
  const cAirline = idx('airline');
  const cFlightNo = idx('flight_number');
  const cDepDate = idx('departure_date');
  const cArrDate = idx('arrival_date');
  const cDep = idx('departure_airport');
  const cArr = idx('arrival_airport');
  const cDepCity = idx('dep_city');
  const cDepCountry = idx('dep_country');
  const cArrCity = idx('arr_city');
  const cArrCountry = idx('arr_country');
  const cDepLat = idx('dep_lat');
  const cDepLon = idx('dep_lon');
  const cArrLat = idx('arr_lat');
  const cArrLon = idx('arr_lon');
  const cDist = idx('distance_miles');
  const cDur = idx('duration_minutes');
  const cIsIntl = idx('is_international');
  const cRoute = idx('route');
  const cYear = idx('year');
  const cMonth = idx('month');
  const cDow = idx('day_of_week');
  const cChannel = idx('booking_channel');
  const cStatus = idx('status');
  const cCabin = idx('cabin_class');
  const cSeat = idx('seat');
  const cNotes = idx('notes');

  const out: Flight[] = [];
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    if (!r || r.length < 2) continue;
    const dep = r[cDep] ?? '';
    const arr = r[cArr] ?? '';
    if (!dep || !arr) continue;
    const depLat = num(r[cDepLat] ?? '');
    const depLon = num(r[cDepLon] ?? '');
    const arrLat = num(r[cArrLat] ?? '');
    const arrLon = num(r[cArrLon] ?? '');
    if (!Number.isFinite(depLat) || !Number.isFinite(arrLat)) continue;

    const depDate = (r[cDepDate] ?? '').trim();
    const monthIndex = monthIndexFromDate(depDate);
    const year = num(r[cYear] ?? '') || Number(depDate.replace(/^[^0-9]/, '').slice(0, 4));
    const month = num(r[cMonth] ?? '') || Number(depDate.replace(/^[^0-9]/, '').slice(5, 7));

    out.push({
      id: `${r[cBooking] || 'X'}-${i}`,
      airline: r[cAirline] ?? '',
      flightNumber: r[cFlightNo] ?? '',
      depDate,
      arrDate: r[cArrDate] ?? '',
      dep,
      arr,
      depCity: r[cDepCity] ?? '',
      depCountry: r[cDepCountry] ?? '',
      arrCity: r[cArrCity] ?? '',
      arrCountry: r[cArrCountry] ?? '',
      depLat,
      depLon,
      arrLat,
      arrLon,
      distanceMiles: num(r[cDist] ?? '') || 0,
      durationMinutes: num(r[cDur] ?? '') || 0,
      isInternational: (r[cIsIntl] ?? '').toLowerCase() === 'true',
      route: r[cRoute] ?? '',
      year: year || 0,
      month: month || 0,
      monthIndex: Number.isFinite(monthIndex) ? monthIndex : 0,
      dayOfWeek: r[cDow] ?? '',
      bookingChannel: r[cChannel] ?? '',
      status: r[cStatus] ?? '',
      cabinClass: r[cCabin] ?? '',
      seat: r[cSeat] ?? '',
      notes: r[cNotes] ?? '',
    });
  }
  return out;
}

export function safeJsonForScript(value: unknown): string {
  return JSON.stringify(value).replace(/<\//g, '<\\/');
}
