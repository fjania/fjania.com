import { select } from 'd3-selection';
import { geoNaturalEarth1, geoPath, geoGraticule } from 'd3-geo';
import { feature } from 'topojson-client';
import { show as ttShow, move as ttMove, hide as ttHide } from './tooltip.js';
import { formatMiles, formatDate, formatDuration } from './format.js';

const WIDTH = 960;
const HEIGHT = 500;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function arcTooltipHtml(f) {
  const route = `${escapeHtml(f.dep)} → ${escapeHtml(f.arr)}`;
  const cities = `${escapeHtml(f.depCity || '')} → ${escapeHtml(f.arrCity || '')}`;
  const date = formatDate(f.depDate);
  const carrier = [f.airline, f.flightNumber].filter(Boolean).map(escapeHtml).join(' ');
  const dur = formatDuration(f.durationMinutes);
  const miles = formatMiles(f.distanceMiles);
  const notes = f.notes ? `<div class="tt-notes">${escapeHtml(f.notes)}</div>` : '';
  return `
    <div class="tt-title">${route}</div>
    <div class="tt-sub">${cities}</div>
    <div class="tt-meta">${date}${carrier ? ' · ' + carrier : ''}</div>
    <div class="tt-meta">${miles}${dur !== '—' ? ' · ' + dur : ''}</div>
    ${notes}
  `;
}

function airportTooltipHtml(a) {
  return `
    <div class="tt-title">${escapeHtml(a.iata)}</div>
    <div class="tt-sub">${escapeHtml(a.city || '')}${a.country ? ', ' + escapeHtml(a.country) : ''}</div>
    <div class="tt-meta">${a.count} visit${a.count === 1 ? '' : 's'}</div>
  `;
}

export function initMap({ state, world }) {
  const svg = select('#map-svg');
  svg.selectAll('*').remove();
  const svgNode = svg.node();

  const projection = geoNaturalEarth1().fitSize([WIDTH, HEIGHT], { type: 'Sphere' });
  const pathGen = geoPath(projection);

  // Graticule (under countries) — faint atlas grid
  const grat = geoGraticule().step([20, 20]);
  const gGrat = svg.append('g').attr('class', 'g-grat');
  gGrat.append('path')
    .datum(grat())
    .attr('class', 'graticule')
    .attr('d', pathGen);
  gGrat.append('path')
    .datum({ type: 'Sphere' })
    .attr('class', 'graticule-outline')
    .attr('d', pathGen);

  // Static countries
  const countries = feature(world, world.objects.countries);
  const visible = {
    ...countries,
    features: countries.features.filter((f) => f.id !== '010'),
  };
  const gWorld = svg.append('g').attr('class', 'g-world');
  gWorld.selectAll('path.country')
    .data(visible.features)
    .enter()
    .append('path')
    .attr('class', 'country')
    .attr('d', pathGen);

  const gArcs = svg.append('g').attr('class', 'g-arcs');
  const gHit = svg.append('g').attr('class', 'g-hit');
  const gAirports = svg.append('g').attr('class', 'g-airports');

  function arcPath(f) {
    return pathGen({
      type: 'LineString',
      coordinates: [[f.depLon, f.depLat], [f.arrLon, f.arrLat]],
    });
  }

  function clientForEvent(e) {
    return { x: e.clientX, y: e.clientY };
  }

  function highlightArc(f, highlight) {
    gArcs.selectAll('path.arc')
      .filter((d) => d.id === f.id)
      .classed('hovered', !!highlight);
  }

  function render() {
    const { flights, airports } = state.getFiltered();

    // Visible arcs
    const arcs = gArcs.selectAll('path.arc').data(flights, (d) => d.id);
    arcs.exit().remove();
    arcs.enter()
      .append('path')
      .attr('class', 'arc')
      .merge(arcs)
      .attr('d', arcPath);

    // Invisible hit-area arcs for hover
    const hits = gHit.selectAll('path.arc-hit').data(flights, (d) => d.id);
    hits.exit().remove();
    const hitsEnter = hits.enter()
      .append('path')
      .attr('class', 'arc-hit')
      .attr('data-tt-pin', '')
      .on('pointerenter', (e, f) => {
        const isTouch = e.pointerType === 'touch';
        ttShow(arcTooltipHtml(f), e.clientX, e.clientY, { pin: isTouch });
        highlightArc(f, true);
      })
      .on('pointermove', (e) => {
        const c = clientForEvent(e);
        ttMove(c.x, c.y);
      })
      .on('pointerleave', (e, f) => {
        // On touch: keep tooltip pinned (body dismisses it on next tap); just drop the arc highlight.
        if (e.pointerType !== 'touch') ttHide();
        highlightArc(f, false);
      });
    hitsEnter.merge(hits).attr('d', arcPath);

    // Airports
    const maxVisits = Math.max(1, ...airports.map((a) => a.count));
    const rScale = (n) => 1.8 + 3.5 * Math.sqrt(n / maxVisits);

    const dots = gAirports.selectAll('circle.airport').data(airports, (d) => d.iata);
    dots.exit().remove();
    const dotsEnter = dots.enter()
      .append('circle')
      .attr('class', 'airport')
      .attr('tabindex', '0')
      .attr('role', 'button')
      .attr('data-tt-pin', '')
      .on('pointerenter', (e, a) => {
        const isTouch = e.pointerType === 'touch';
        ttShow(airportTooltipHtml(a), e.clientX, e.clientY, { pin: isTouch });
      })
      .on('pointermove', (e) => ttMove(e.clientX, e.clientY))
      .on('pointerleave', (e) => {
        if (e.pointerType !== 'touch') ttHide();
      })
      .on('click', (e, a) => {
        const cur = state.filters.focusAirport;
        state.setFilter('focusAirport', cur === a.iata ? null : a.iata);
      });
    dotsEnter.merge(dots)
      .attr('cx', (a) => projection([a.lon, a.lat])[0])
      .attr('cy', (a) => projection([a.lon, a.lat])[1])
      .attr('r', (a) => rScale(a.count))
      .classed('focused', (a) => state.filters.focusAirport === a.iata);
  }

  function highlightTrip(key) {
    const tripAirports = new Set();
    if (key) {
      for (const f of state.getFiltered().flights) {
        if (f.id.split('-')[0] === key) { tripAirports.add(f.dep); tripAirports.add(f.arr); }
      }
    }
    gArcs.selectAll('path.arc').classed('trip-hover', (d) => key && d.id.split('-')[0] === key);
    gAirports.selectAll('circle.airport').classed('trip-hover', (a) => tripAirports.has(a.iata));
  }

  state.subscribe(render);
  render();
  return { highlightTrip };
}
