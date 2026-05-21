import { select } from 'd3-selection';
import { geoNaturalEarth1, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';

const WIDTH = 960;
const HEIGHT = 500;

export function initMap({ state, world }) {
  const svg = select('#map-svg');
  svg.selectAll('*').remove();

  const projection = geoNaturalEarth1().fitSize([WIDTH, HEIGHT], { type: 'Sphere' });
  const pathGen = geoPath(projection);

  // Static countries layer
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
  const gAirports = svg.append('g').attr('class', 'g-airports');

  function render() {
    const { flights, airports } = state.getFiltered();

    const arcs = gArcs.selectAll('path.arc').data(flights, (d) => d.id);
    arcs.exit().remove();
    arcs.enter()
      .append('path')
      .attr('class', 'arc')
      .attr('d', (f) =>
        pathGen({
          type: 'LineString',
          coordinates: [[f.depLon, f.depLat], [f.arrLon, f.arrLat]],
        })
      );

    const maxVisits = Math.max(1, ...airports.map((a) => a.count));
    const rScale = (n) => 1.8 + 3.5 * Math.sqrt(n / maxVisits);

    const dots = gAirports.selectAll('circle.airport').data(airports, (d) => d.iata);
    dots.exit().remove();
    const dotsEnter = dots.enter()
      .append('circle')
      .attr('class', 'airport');
    dotsEnter.merge(dots)
      .attr('cx', (a) => projection([a.lon, a.lat])[0])
      .attr('cy', (a) => projection([a.lon, a.lat])[1])
      .attr('r', (a) => rScale(a.count));
  }

  state.subscribe(render);
  render();
}
