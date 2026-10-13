const { useEffect, useMemo, useRef, useState } = React;
const COLORS = { LOW: '#19a974', MODERATE: '#d9a514', HIGH: '#ed7c28', SEVERE: '#d84b4b', NO_TRAVEL: '#772d91' };
const RISK_ORDER = ['LOW', 'MODERATE', 'HIGH', 'SEVERE', 'NO_TRAVEL'];
const formatTime = value => new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value));
const formatDuration = mins => `${Math.floor(mins / 60)}h ${mins % 60}m`;
function summarizeAtHour(route, hour) {
  const riskMiles = Object.fromEntries(RISK_ORDER.map(level => [level, 0]));
  let weighted = 0;
  route.checkpoints.slice(0, -1).forEach((checkpoint, index) => {
    const next = route.checkpoints[index + 1];
    const miles = Math.max(0, next.distance_miles - checkpoint.distance_miles);
    const risk = checkpoint.forecasts[hour]?.risk || checkpoint.risk;
    riskMiles[risk] += miles;
    weighted += RISK_ORDER.indexOf(risk) * miles;
  });
  return { riskMiles, average: weighted / route.distance_miles };
}
function localDateTime() {
  const date = new Date(Date.now() + 60 * 60 * 1000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function App() {
  const [origin, setOrigin] = useState('Chicago, IL');
  const [destination, setDestination] = useState('Detroit, MI');
  const [departure, setDeparture] = useState(localDateTime());
  const [load, setLoad] = useState('20000');
  const [interval, setInterval] = useState('25');
  const [result, setResult] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [hour, setHour] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const mapNode = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const fittedRouteRef = useRef(null);
  const selected = result?.routes.find(route => route.route_id === selectedId) || result?.routes[0];

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapNode.current,
      style: 'https://tiles.openfreemap.org/styles/positron',
      center: [-84.5, 41.8], zoom: 4.5,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
    mapRef.current = map;
    return () => { markersRef.current.forEach(marker => marker.remove()); map.remove(); };
  }, []);

  const shownSummary = useMemo(() => {
    if (!selected) return null;
    return summarizeAtHour(selected, hour);
  }, [selected, hour]);

  const routeSummaries = useMemo(() => {
    if (!result) return {};
    return Object.fromEntries(result.routes.map(route => [route.route_id, summarizeAtHour(route, hour)]));
  }, [result, hour]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    function drawRoute() {
      if (!map.isStyleLoaded()) return;
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];
      const routeCoordinates = selected ? selected.geometry.map(point => [point.longitude, point.latitude]) : [];
      const checkpointFeatures = selected ? selected.checkpoints.map(point => {
        const conditions = point.forecasts[hour] || point.forecasts[0];
        return { type: 'Feature', properties: { weight: (RISK_ORDER.indexOf(conditions.risk) + 1) / RISK_ORDER.length },
          geometry: { type: 'Point', coordinates: [point.longitude, point.latitude] } };
      }) : [];
      const routeData = selected
        ? { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: routeCoordinates } }
        : { type: 'FeatureCollection', features: [] };
      const heatData = { type: 'FeatureCollection', features: checkpointFeatures };
      if (!map.getSource('trip-route')) {
        map.addSource('trip-route', { type: 'geojson', data: routeData });
        map.addSource('risk-heat', { type: 'geojson', data: heatData });
        map.addLayer({ id: 'risk-heat', type: 'heatmap', source: 'risk-heat', maxzoom: 12,
          paint: { 'heatmap-weight': ['get', 'weight'], 'heatmap-intensity': 1.1, 'heatmap-radius': 32, 'heatmap-opacity': .68,
            'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(25,169,116,0)', .2, '#19a974', .4, '#d9a514', .6, '#ed7c28', .8, '#d84b4b', 1, '#772d91'] },
        });
        map.addLayer({ id: 'trip-route', type: 'line', source: 'trip-route',
          paint: { 'line-color': '#597b76', 'line-width': 4, 'line-opacity': .85 },
        });
      } else {
        map.getSource('trip-route').setData(routeData);
        map.getSource('risk-heat').setData(heatData);
      }
      if (!selected) return;
      selected.checkpoints.forEach(point => {
        const conditions = point.forecasts[hour] || point.forecasts[0];
        const popup = new maplibregl.Popup({ offset: 12 }).setHTML(
          `<b>${point.distance_miles.toFixed(1)} mi · ${conditions.risk}</b><br>ETA ${formatTime(point.eta)}<br>Wind ${conditions.wind_mph} mph · Rain ${conditions.rain_in_per_hour} in/hr · Snow ${conditions.snow_in_per_hour} in/hr`,
        );
        const marker = new maplibregl.Marker({ color: conditions.color })
          .setLngLat([point.longitude, point.latitude]).setPopup(popup).addTo(map);
        markersRef.current.push(marker);
      });
      if (routeCoordinates.length && fittedRouteRef.current !== selected) {
        const bounds = routeCoordinates.reduce((result, coordinate) => result.extend(coordinate),
          new maplibregl.LngLatBounds(routeCoordinates[0], routeCoordinates[0]));
        map.fitBounds(bounds, { padding: 28, maxZoom: 8, duration: 450 });
        fittedRouteRef.current = selected;
      }
    }
    if (map.isStyleLoaded()) drawRoute();
    else map.once('load', drawRoute);
    return () => map.off('load', drawRoute);
  }, [selected, hour]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/plan/', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.getElementById('root').dataset.csrf },
        body: JSON.stringify({ origin, destination, departure_time: new Date(departure).toISOString(), load_lb: load, interval_miles: interval }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not plan this trip.');
      setResult(data); setSelectedId(data.recommended_route_id); setHour(0);
    } catch (err) {
      setError(err.message || 'The trip could not be planned. Check your connection and try again.');
    } finally { setBusy(false); }
  }

  const originRoute = result && `${result.origin.label} → ${result.destination.label}`;
  return <>
    <header className="topbar"><div className="brand"><span className="brand-mark">●</span> spotter</div><span className="top-note">Weather aware dispatch · Global</span></header>
    <main className="layout">
      <div className="intro"><div><div className="eyebrow">Safer miles start here</div><h1>Weather-aware truck routing</h1><p>Compare route risk, checkpoint forecasts and travel time before you roll.</p></div><div className="status-pill">● &nbsp;Weather risk engine ready</div></div>
      <div className="columns">
        <aside className="card form-card"><h2>Plan your trip</h2>
          <form onSubmit={submit}>
            <label className="field"><span>Origin</span><input required value={origin} onChange={e => setOrigin(e.target.value)} placeholder="City, state or address" /></label>
            <label className="field"><span>Destination</span><input required value={destination} onChange={e => setDestination(e.target.value)} placeholder="City, state or address" /></label>
            <label className="field"><span>Departure date and time</span><input required type="datetime-local" value={departure} onChange={e => setDeparture(e.target.value)} /></label>
            <div className="field-row"><label className="field"><span>Load weight</span><div className="unit"><input required type="number" min="0" step="100" value={load} onChange={e => setLoad(e.target.value)} /><em>lb</em></div></label>
              <label className="field"><span>Weather checks</span><select value={interval} onChange={e => setInterval(e.target.value)}><option value="10">Every 10 mi</option><option value="25">Every 25 mi</option><option value="50">Every 50 mi</option></select></label></div>
            <button className="primary" disabled={busy}>{busy ? <span className="loading"><i className="spinner"/>Finding safer routes…</span> : 'Compare routes'}</button>
          </form>
          {error && <div className="error" role="alert">{error}</div>}
          <p className="hint">Route options use truck routing. Weather is forecast at each checkpoint's estimated arrival time. The map slider explores the next 48 forecast hours.</p>
        </aside>
        <section className="main">
          <div className="card map-card"><div className="map-head"><h2>{selected ? originRoute : 'Trip corridor & weather risk'}</h2>
            <div className="map-controls"><span className="forecast-label">Forecast offset</span><input aria-label="Forecast hour" type="range" min="0" max="48" value={hour} onChange={e => setHour(Number(e.target.value))} /><span className="forecast-value">+{hour} hr</span></div></div>
            <div id="map" ref={mapNode}>{!result && <div className="map-empty">Enter a trip to view route options and forecast</div>}</div>
            <div className="map-legend">{RISK_ORDER.map(risk => <span className="legend-item" key={risk}><i className="dot" style={{background:COLORS[risk]}}/>{risk.replace('_',' ')}</span>)}<span className="legend-item">● &nbsp;Checkpoint forecast at selected hour</span></div>
          </div>
          {result && <>
          <div className="route-grid">{result.routes.map(route => { const routeSummary = routeSummaries[route.route_id]; return <article key={route.route_id} className={`card route-card ${route.route_id === selected?.route_id ? 'active' : ''}`} onClick={() => setSelectedId(route.route_id)}>
              <div className="route-title"><strong>{route.name}</strong>{route.recommended && <span className="recommended">SAFEST PICK</span>}</div>
              <div className="route-meta">{route.distance_miles.toLocaleString()} mi · {formatDuration(route.travel_minutes)} · Risk {hour ? `+${hour}h` : 'at ETA'}</div>
              <div className="route-stats"><div className="stat"><small>Severe miles</small><b>{routeSummary.riskMiles.SEVERE.toFixed(1)} mi</b></div><div className="stat"><small>High risk miles</small><b>{routeSummary.riskMiles.HIGH.toFixed(1)} mi</b></div></div>
              <div className="riskline">{RISK_ORDER.map(level => <i key={level} style={{width:`${routeSummary.riskMiles[level] / route.distance_miles * 100}%`,background:COLORS[level]}} />)}</div>
            </article>; })}</div>
            {selected && <div className="card summary-card"><div className="summary-head"><h2>{selected.name} · route summary</h2><span className="eyebrow">{hour ? `Forecast +${hour} hours` : 'At estimated arrival'}</span></div>
              <div className="summary-grid"><div className="summary-cell"><small>Distance</small><b>{selected.distance_miles.toLocaleString()} mi</b></div><div className="summary-cell"><small>Travel time</small><b>{formatDuration(selected.travel_minutes)}</b></div><div className="summary-cell"><small>Severe</small><b style={{color:COLORS.SEVERE}}>{shownSummary.riskMiles.SEVERE.toFixed(1)} mi</b></div><div className="summary-cell"><small>High risk</small><b style={{color:COLORS.HIGH}}>{shownSummary.riskMiles.HIGH.toFixed(1)} mi</b></div><div className="summary-cell"><small>Average risk</small><b>{shownSummary.average.toFixed(2)} / 4</b></div></div>
              <div className="stops"><h3>Weather checkpoints · {selected.checkpoints.length}</h3><div className="stop-list">{selected.checkpoints.map((point,index) => { const w=point.forecasts[hour]||point.forecasts[0]; return <div className="stop" key={`${point.distance_miles}-${index}`}><b style={{color:w.color}}>Mile {point.distance_miles} · {w.risk.replace('_',' ')}</b><span>{formatTime(point.eta)}<br/>Wind {w.wind_mph} mph · Rain {w.rain_in_per_hour} in/hr</span></div> })}</div></div>
            </div>}
            <p className="disclaimer">Weather estimates are for planning support. Follow current road closures and dispatch safety procedures.</p>
          </>}
        </section>
      </div>
    </main>
  </>;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
