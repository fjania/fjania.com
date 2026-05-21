import { select } from 'd3-selection';
import { geoNaturalEarth1, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';

const WIDTH = 960;
const HEIGHT = 500;

function uniqueAirports(flights) {
  const map = new Map();
  for (const f of flights) {
    if (!map.has(f.dep)) map.set(f.dep, { iata: f.dep, city: f.depCity, country: f.depCountry, lat: f.depLat, lon: f.depLon, count: 0 });
    if (!map.has(f.arr)) map.set(f.arr, { iata: f.arr, city: f.arrCity, country: f.arrCountry, lat: f.arrLat, lon: f.arrLon, count: 0 });
    map.get(f.dep).count++;
    map.get(f.arr).count++;
  }
  return [...map.values()];
}

export function initMap({ flights, world }) {
  const svg = select('#map-svg');
  svg.selectAll('*').remove();

  const projection = geoNaturalEarth1().fitSize([WIDTH, HEIGHT], { type: 'Sphere' });
  const pathGen = geoPath(projection);

  // Countries (filter out Antarctica id=010)
  const countries = feature(world, world.objects.countries);
  const visible = {
    ...countries,
    features: countries.features.filter((f) => f.id !== '010'),
  };

  const gWorld = svg.append('g').attr('class', 'g-world');
  gWorld.append('path')
    .datum({ type: 'Sphere' })
    .attr('class', 'sphere')
    .attr('d', pathGen)
    .attr('fill', 'transparent');

  gWorld.selectAll('path.country')
    .data(visible.features)
    .enter()
    .append('path')
    .attr('class', 'country')
    .attr('d', pathGen);

  const gArcs = svg.append('g').attr('class', 'g-arcs');
  const gAirports = svg.append('g').attr('class', 'g-airports');

  // Arcs: each flight as a great-circle LineString
  gArcs.selectAll('path.arc')
    .data(flights)
    .enter()
    .append('path')
    .attr('class', 'arc')
    .attr('d', (f) =>
      pathGen({
        type: 'LineString',
        coordinates: [
          [f.depLon, f.depLat],
          [f.arrLon, f.arrLat],
        ],
      })
    );

  // Airports
  const airports = uniqueAirports(flights);
  const maxVisits = Math.max(...airports.map((a) => a.count));
  const rScale = (n) => 1.8 + 3.5 * Math.sqrt(n / maxVisits);

  gAirports.selectAll('circle.airport')
    .data(airports)
    .enter()
    .append('circle')
    .attr('class', 'airport')
    .attr('cx', (a) => projection([a.lon, a.lat])[0])
    .attr('cy', (a) => projection([a.lon, a.lat])[1])
    .attr('r', (a) => rScale(a.count));
}
