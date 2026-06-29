/**
 * map.js — MSA Interactive Map v6
 * Four boundary levels: CAs, LADs, MSOAs, LSOAs (MSOA/LSOA lazy-loaded).
 * DPP areas visible at every level. Status toggle: established / existing / DPP.
 */

// ── Config ─────────────────────────────────────────────────────────────────
const BASE_PATH = '../data/processed';

const STATUS_COLOURS = {
  established:  '#2a9d8f',
  existing:     '#4895b0',
  dpp:          '#e9c46a',
  not_in_scope: '#c8cdd4',
};

const TEAL         = '#2a9d8f';
const ENGLAND_GREY = '#e8eaed';
const LAND_GREY    = '#6b7280';
const OUT_OF_SCOPE = '#c8cdd4';

// CA GSS code → MSA status
const CA_MSA_STATUS = {
  'E47000001': 'established',   // Greater Manchester
  'E47000002': 'established',   // South Yorkshire
  'E47000003': 'established',   // West Yorkshire
  'E47000004': 'established',   // Liverpool City Region
  'E47000006': 'existing',      // Tees Valley
  'E47000007': 'established',   // West Midlands
  'E47000008': 'existing',      // Cambridgeshire & Peterborough
  'E47000009': 'established',   // West of England
  'E47000012': 'existing',      // York & North Yorkshire
  'E47000013': 'existing',      // East Midlands
  'E47000014': 'established',   // North East
  'E47000015': 'not_in_scope',  // Devon & Torbay
  'E47000016': 'existing',      // Hull & East Yorkshire
  'E47000017': 'existing',      // Greater Lincolnshire
  'E47000018': 'established',   // Lancashire
};

// DPP areas keyed by LAD25CD (for ladLayer / dppLayer)
const DPP_LAD_TO_AREA = {};
const _DPP_LAD25 = {
  'Cheshire & Warrington': ['E06000049','E06000050','E06000007'],
  'Cumbria':               ['E06000063','E06000064'],
  'Sussex & Brighton':     ['E06000043','E07000061','E07000062','E07000063','E07000064','E07000065',
                            'E07000223','E07000224','E07000225','E07000226','E07000227','E07000228','E07000229'],
  'Hampshire & Solent':    ['E06000044','E06000045','E06000046',
                            'E07000084','E07000085','E07000086','E07000087','E07000088',
                            'E07000089','E07000090','E07000091','E07000092','E07000093','E07000094'],
  'Greater Essex':         ['E07000066','E07000067','E07000068','E07000069','E07000070',
                            'E07000071','E07000072','E07000073','E07000074','E07000075',
                            'E06000033','E07000076','E06000034','E07000077'],
  'Norfolk & Suffolk':     ['E07000143','E07000144','E07000145','E07000146','E07000147','E07000148','E07000149',
                            'E07000200','E07000202','E07000203','E07000244','E07000245'],
};
for (const [area, codes] of Object.entries(_DPP_LAD25)) {
  codes.forEach(c => DPP_LAD_TO_AREA[c] = area);
}
const DPP_LADS = new Set(Object.keys(DPP_LAD_TO_AREA));

// DPP areas keyed by LAD22CD (for msoaLayer / lsoaLayer).
// Cumbria reorganised in 2023: LAD25 E06000063/64 → 6 legacy LAD22 districts.
const DPP_LAD22_TO_AREA = {};
const _DPP_LAD22 = {
  'Cheshire & Warrington': ['E06000049','E06000050','E06000007'],
  'Cumbria':               ['E07000026','E07000027','E07000028','E07000029','E07000030','E07000031'],
  'Sussex & Brighton':     ['E06000043','E07000061','E07000062','E07000063','E07000064','E07000065',
                            'E07000223','E07000224','E07000225','E07000226','E07000227','E07000228','E07000229'],
  'Hampshire & Solent':    ['E06000044','E06000045','E06000046',
                            'E07000084','E07000085','E07000086','E07000087','E07000088',
                            'E07000089','E07000090','E07000091','E07000092','E07000093','E07000094'],
  'Greater Essex':         ['E07000066','E07000067','E07000068','E07000069','E07000070',
                            'E07000071','E07000072','E07000073','E07000074','E07000075',
                            'E06000033','E07000076','E06000034','E07000077'],
  'Norfolk & Suffolk':     ['E07000143','E07000144','E07000145','E07000146','E07000147','E07000148','E07000149',
                            'E07000200','E07000202','E07000203','E07000244','E07000245'],
};
for (const [area, codes] of Object.entries(_DPP_LAD22)) {
  codes.forEach(c => DPP_LAD22_TO_AREA[c] = area);
}
const DPP_LAD22 = new Set(Object.keys(DPP_LAD22_TO_AREA));

const STATUS_LABELS = {
  established:  'Established',
  existing:     'Existing',
  dpp:          'DPP (Devolution Priority Programme)',
  not_in_scope: 'Out of scope',
  none:         'No Combined Authority',
};

// ── State ──────────────────────────────────────────────────────────────────
let activeLayer    = 'ca';
let colourMode     = 'uniform';
let caLayer        = null;
let ladLayer       = null;
let dppLayer       = null;
let msoaLayer      = null;
let lsoaLayer      = null;
let countriesLayer = null;
let tooltip        = null;

// Built during init() from ladData — LAD25CD (≈ LAD22CD) → MSA status.
// Used as the authoritative CA lookup for MSOAs/LSOAs because the MSOA/LSOA
// CAUTH25CD field has spatial-join gaps (e.g. 100/171 South Yorkshire MSOAs
// incorrectly got CAUTH25CD='none').
const LAD22_TO_CA_STATUS = {};
const LAD22_TO_CA_NAME   = {};

// ── Map init ───────────────────────────────────────────────────────────────
const map = L.map('map', {
  center: [53.2, -1.8],
  zoom: 6,
  minZoom: 5,
  maxZoom: 14,
  zoomControl: true,
});

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 19,
}).addTo(map);

fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
  .then(r => r.json())
  .then(data => {
    L.geoJSON(data, {
      style: { fillColor: LAND_GREY, fillOpacity: 1, color: '#2e3136', weight: 0.3 },
      interactive: false,
    }).addTo(map).bringToBack();
  })
  .catch(err => console.warn('World mask failed to load:', err));

// ── Tooltip ────────────────────────────────────────────────────────────────
const Tooltip = L.Control.extend({
  options: { position: 'topright' },
  onAdd() {
    this._div = L.DomUtil.create('div', 'map-tooltip hidden');
    return this._div;
  },
  update(name, sub) {
    if (!name) { this._div.classList.add('hidden'); return; }
    this._div.classList.remove('hidden');
    this._div.innerHTML = `<strong>${name}</strong>${sub ? `<br><span>${sub}</span>` : ''}`;
  }
});
tooltip = new Tooltip();
tooltip.addTo(map);

// ── Helpers ────────────────────────────────────────────────────────────────
function statusFromCA(caCode) {
  return CA_MSA_STATUS[caCode] || null;
}

function fillByStatus(status) {
  if (!status || status === 'none') return ENGLAND_GREY;
  if (status === 'not_in_scope')    return OUT_OF_SCOPE;
  return colourMode === 'deal' ? STATUS_COLOURS[status] : TEAL;
}

// ── Style functions ────────────────────────────────────────────────────────
function styleCA(feature) {
  const status = statusFromCA(feature.properties.CAUTH25CD) || 'not_in_scope';
  const fill   = status === 'not_in_scope' ? OUT_OF_SCOPE
               : colourMode === 'deal' ? STATUS_COLOURS[status] : TEAL;
  return { fillColor: fill, fillOpacity: 0.75, color: '#ffffff', weight: 1.2, opacity: 0.9 };
}

function styleLAD(feature) {
  const isDPP    = DPP_LADS.has(feature.properties.LAD25CD);
  const caStatus = statusFromCA(feature.properties.ca_gss_code);
  const fill     = isDPP
    ? (colourMode === 'deal' ? STATUS_COLOURS.dpp : TEAL)
    : fillByStatus(caStatus);
  const inMSA = isDPP || (caStatus && caStatus !== 'not_in_scope');
  return { fillColor: fill, fillOpacity: inMSA ? 0.65 : 0.5, color: '#ffffff', weight: 0.6, opacity: 0.7 };
}

function styleDPP() {
  const fill = colourMode === 'deal' ? STATUS_COLOURS.dpp : TEAL;
  // weight:0 / opacity:0 in CA view removes SVG stroke entirely — the only
  // reliable way to prevent antialiasing from revealing internal LAD edges.
  return {
    fillColor:   fill,
    fillOpacity: 0.75,
    color:       '#ffffff',
    weight:      activeLayer === 'ca' ? 0 : 0.6,
    opacity:     activeLayer === 'ca' ? 0 : 0.7,
  };
}

function fillFromLAD22(lad22cd, cauthCode) {
  if (DPP_LAD22.has(lad22cd)) return colourMode === 'deal' ? STATUS_COLOURS.dpp : TEAL;
  const status = LAD22_TO_CA_STATUS[lad22cd] || statusFromCA(cauthCode);
  return fillByStatus(status);
}

// Stroke weights that scale with zoom — at low zoom, borders create visual
// noise so we suppress them entirely; they fade in as the user zooms in.
function msoaWeight() {
  const z = map.getZoom();
  if (z <= 8)  return 0;
  if (z <= 9)  return 0.1;
  if (z <= 10) return 0.2;
  return 0.3;
}

function lsoaWeight() {
  const z = map.getZoom();
  if (z <= 9)  return 0;
  if (z <= 10) return 0.08;
  if (z <= 11) return 0.12;
  return 0.18;
}

function styleMSOA(feature) {
  const p = feature.properties;
  const w = msoaWeight();
  return { fillColor: fillFromLAD22(p.LAD22CD, p.CAUTH25CD), fillOpacity: 0.7,
           color: '#ffffff', weight: w, opacity: w > 0 ? 0.5 : 0 };
}

function styleLSOA(feature) {
  const p = feature.properties;
  const w = lsoaWeight();
  return { fillColor: fillFromLAD22(p.LAD22CD, p.CAUTH25CD), fillOpacity: 0.7,
           color: '#ffffff', weight: w, opacity: w > 0 ? 0.4 : 0 };
}

function styleCountry(feature) {
  if (feature.properties.is_england) {
    return { fillColor: ENGLAND_GREY, fillOpacity: 1, color: '#888', weight: 0.3, interactive: false };
  }
  return { fillColor: LAND_GREY, fillOpacity: 1, color: '#2e3136', weight: 0.3, interactive: false };
}

// ── Hover ──────────────────────────────────────────────────────────────────
function highlightFeature(e) {
  const weight = activeLayer === 'lsoa' ? 1.5 : 2.5;
  e.target.setStyle({ fillOpacity: 0.95, weight, color: '#ffffff' });
  e.target.bringToFront();
  const p = e.target.feature.properties;

  if (activeLayer === 'ca') {
    tooltip.update(
      p.short_name || p.CAUTH25NM || '',
      STATUS_LABELS[statusFromCA(p.CAUTH25CD)] || ''
    );
  } else if (activeLayer === 'lad') {
    const isDPP = DPP_LADS.has(p.LAD25CD);
    const sub   = isDPP
      ? `DPP — ${DPP_LAD_TO_AREA[p.LAD25CD]}`
      : (p.ca_name !== 'No Combined Authority' ? p.ca_name : '');
    tooltip.update(p.LAD25NM || '', sub);
  } else if (activeLayer === 'msoa') {
    const isDPP  = DPP_LAD22.has(p.LAD22CD);
    const caName = p.CAUTH25NM !== 'No Combined Authority' ? p.CAUTH25NM : LAD22_TO_CA_NAME[p.LAD22CD];
    const sub    = isDPP ? `DPP — ${DPP_LAD22_TO_AREA[p.LAD22CD]}` : (caName || p.LAD22NM);
    tooltip.update(p.MSOA21NM || '', sub);
  } else if (activeLayer === 'lsoa') {
    const isDPP  = DPP_LAD22.has(p.LAD22CD);
    const caName = p.CAUTH25NM !== 'No Combined Authority' ? p.CAUTH25NM : LAD22_TO_CA_NAME[p.LAD22CD];
    const sub    = isDPP ? `DPP — ${DPP_LAD22_TO_AREA[p.LAD22CD]}` : (caName || p.LAD22NM);
    tooltip.update(p.LSOA21NM || '', sub);
  }
}

function resetHighlight(e) {
  const layers = { ca: caLayer, lad: ladLayer, msoa: msoaLayer, lsoa: lsoaLayer };
  layers[activeLayer]?.resetStyle(e.target);
  tooltip.update(null);
}

function highlightDPP(e) {
  e.target.setStyle({ fillOpacity: 0.95, weight: 2, color: '#ffffff' });
  e.target.bringToFront();
  const p = e.target.feature.properties;
  tooltip.update(p.LAD25NM || '', `DPP — ${DPP_LAD_TO_AREA[p.LAD25CD] || ''}`);
}

function resetDPP(e) {
  dppLayer?.resetStyle(e.target);
  tooltip.update(null);
}

// ── Click → sidebar ────────────────────────────────────────────────────────
function onFeatureClick(e, type) {
  L.DomEvent.stopPropagation(e);
  const p = e.target.feature.properties;

  document.getElementById('sidebar-default').style.display = 'none';
  document.getElementById('sidebar-content').classList.remove('hidden');

  let name, gss, status, caName;

  if (type === 'ca') {
    name   = p.short_name || p.CAUTH25NM || '—';
    gss    = p.CAUTH25CD  || '—';
    status = statusFromCA(p.CAUTH25CD) || 'not_in_scope';
    caName = name;
  } else if (type === 'lad') {
    name = p.LAD25NM || '—';
    gss  = p.LAD25CD  || '—';
    if (DPP_LADS.has(p.LAD25CD)) {
      status = 'dpp';
      caName = DPP_LAD_TO_AREA[p.LAD25CD] || '—';
    } else {
      status = statusFromCA(p.ca_gss_code) || 'none';
      caName = (p.ca_name && p.ca_name !== 'No Combined Authority') ? p.ca_name : '—';
    }
  } else if (type === 'msoa') {
    name = p.MSOA21NM || '—';
    gss  = p.MSOA21CD || '—';
    if (DPP_LAD22.has(p.LAD22CD)) {
      status = 'dpp';
      caName = DPP_LAD22_TO_AREA[p.LAD22CD] || '—';
    } else {
      status = LAD22_TO_CA_STATUS[p.LAD22CD] || statusFromCA(p.CAUTH25CD) || 'none';
      caName = (p.CAUTH25NM && p.CAUTH25NM !== 'No Combined Authority')
        ? p.CAUTH25NM : (LAD22_TO_CA_NAME[p.LAD22CD] || '—');
    }
  } else if (type === 'lsoa') {
    name = p.LSOA21NM || '—';
    gss  = p.LSOA21CD || '—';
    if (DPP_LAD22.has(p.LAD22CD)) {
      status = 'dpp';
      caName = DPP_LAD22_TO_AREA[p.LAD22CD] || '—';
    } else {
      status = LAD22_TO_CA_STATUS[p.LAD22CD] || statusFromCA(p.CAUTH25CD) || 'none';
      caName = (p.CAUTH25NM && p.CAUTH25NM !== 'No Combined Authority')
        ? p.CAUTH25NM : (LAD22_TO_CA_NAME[p.LAD22CD] || '—');
    }
  }

  document.getElementById('sidebar-name').textContent = name;
  document.getElementById('sidebar-gss').textContent  = gss;
  document.getElementById('detail-gss').textContent   = gss;
  document.getElementById('detail-ca').textContent    = caName;
  document.getElementById('detail-deal').textContent  = STATUS_LABELS[status] || status;

  const dealBadge = document.getElementById('sidebar-deal-badge');
  dealBadge.textContent = STATUS_LABELS[status] || status;
  dealBadge.className   = `badge badge-${status}`;

  const typeBadge = document.getElementById('sidebar-status-badge');
  const typeLabels = { ca: 'Combined Authority', lad: 'Local Authority', msoa: 'MSOA', lsoa: 'LSOA' };
  typeBadge.textContent = typeLabels[type] || type.toUpperCase();
  typeBadge.className   = `badge badge-${type}`;

  document.getElementById('ca-row').style.display   = type !== 'ca' ? 'flex' : 'none';
  document.getElementById('deal-row').style.display = 'flex';

  // Clicking a CA zooms in and auto-switches to MSOA boundaries
  if (type === 'ca') zoomToMSOA(e.target);
}

// Zoom to a CA's bounds and switch the boundary layer to MSOAs.
// Called fire-and-forget from onFeatureClick so the sidebar update isn't blocked.
async function zoomToMSOA(clickedLayer) {
  map.fitBounds(clickedLayer.getBounds(), { padding: [30, 30], maxZoom: 11 });

  if (!msoaLayer) {
    const btn = document.querySelector('.layer-btn[data-layer="msoa"]');
    if (btn) { btn.textContent = 'Loading…'; btn.disabled = true; }
    try {
      const data = await loadGeoJSON(`${BASE_PATH}/msoa.geojson`);
      msoaLayer = L.geoJSON(data, { filter: isMSAOrDPP, style: styleMSOA });
      bindInteraction(msoaLayer, 'msoa');
    } catch (err) {
      console.error('MSOA auto-load error:', err);
      if (btn) { btn.textContent = 'MSOAs'; btn.disabled = false; }
      return;
    }
    if (btn) { btn.textContent = 'MSOAs'; btn.disabled = false; }
  }

  activeLayer = 'msoa';
  document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('.layer-btn[data-layer="msoa"]')?.classList.add('active');
  applyLayerSwitch('msoa');
}

function resetSidebar() {
  document.getElementById('sidebar-default').style.display = 'flex';
  document.getElementById('sidebar-content').classList.add('hidden');
}

// ── Bind interactions ──────────────────────────────────────────────────────
function bindInteraction(layer, type) {
  layer.eachLayer(l => l.on({
    mouseover: highlightFeature,
    mouseout:  resetHighlight,
    click:     e => onFeatureClick(e, type),
  }));
}

function bindDPPInteraction(layer) {
  layer.eachLayer(l => l.on({
    mouseover: highlightDPP,
    mouseout:  resetDPP,
    click:     e => onFeatureClick(e, 'lad'),
  }));
}

// ── Legend ─────────────────────────────────────────────────────────────────
function updateLegend() {
  const el = document.getElementById('legend-items');
  if (colourMode === 'uniform') {
    el.innerHTML = `
      <div class="legend-item"><span class="legend-swatch" style="background:${TEAL}"></span>In-scope MSA</div>
      <div class="legend-item"><span class="legend-swatch" style="background:${OUT_OF_SCOPE}"></span>Out of scope</div>`;
  } else {
    el.innerHTML = `
      <div class="legend-item"><span class="legend-swatch" style="background:${STATUS_COLOURS.established}"></span>Established</div>
      <div class="legend-item"><span class="legend-swatch" style="background:${STATUS_COLOURS.existing}"></span>Existing</div>
      <div class="legend-item"><span class="legend-swatch legend-swatch-dashed" style="background:${STATUS_COLOURS.dpp}"></span>DPP (pipeline)</div>
      <div class="legend-item"><span class="legend-swatch" style="background:${OUT_OF_SCOPE}"></span>Out of scope</div>`;
  }
}

function refreshStyles() {
  if (caLayer)   caLayer.setStyle(styleCA);
  if (ladLayer)  ladLayer.setStyle(styleLAD);
  if (dppLayer)  dppLayer.setStyle(styleDPP);
  if (msoaLayer) msoaLayer.setStyle(styleMSOA);
  if (lsoaLayer) lsoaLayer.setStyle(styleLSOA);
  updateLegend();
}

// ── Load GeoJSON ───────────────────────────────────────────────────────────
async function loadGeoJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

// Filter predicate: only features inside an MSA or DPP area.
// Uses LAD22CD → LAD22_TO_CA_STATUS (built from authoritative LAD data) as the
// primary check; falls back to CAUTH25CD only if the LAD code isn't in the map.
function isMSAOrDPP(feature) {
  const p        = feature.properties;
  const lad22    = p.LAD22CD || p.LAD25CD;
  if (DPP_LAD22.has(lad22)) return true;
  const status = LAD22_TO_CA_STATUS[lad22] || statusFromCA(p.CAUTH25CD);
  return !!status && status !== 'not_in_scope';
}

// ── Show / hide layers ─────────────────────────────────────────────────────
function applyLayerSwitch(target) {
  // Remove all toggleable layers
  [caLayer, dppLayer, ladLayer, msoaLayer, lsoaLayer]
    .forEach(l => l && map.removeLayer(l));

  if (target === 'ca') {
    caLayer.addTo(map);
    if (dppLayer) { dppLayer.addTo(map); dppLayer.setStyle(styleDPP); }
  } else if (target === 'lad') {
    ladLayer.addTo(map);
  } else if (target === 'msoa') {
    msoaLayer.addTo(map);
  } else if (target === 'lsoa') {
    lsoaLayer.addTo(map);
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
async function init() {
  try {
    const [countriesData, caData, ladData] = await Promise.all([
      loadGeoJSON(`${BASE_PATH}/countries.geojson`),
      loadGeoJSON(`${BASE_PATH}/ca.geojson`),
      loadGeoJSON(`${BASE_PATH}/lad.geojson`),
    ]);

    // Build LAD22→CA status/name lookups from LAD data (LAD25CD ≈ LAD22CD for most).
    for (const feat of ladData.features) {
      const p      = feat.properties;
      const status = statusFromCA(p.ca_gss_code);
      if (status && p.LAD25CD) {
        LAD22_TO_CA_STATUS[p.LAD25CD] = status;
        LAD22_TO_CA_NAME[p.LAD25CD]   = p.ca_name;
      }
    }
    // Barnsley (E08000016→E08000038) and Sheffield (E08000019→E08000039) were
    // reorganised in 2023. MSOA/LSOA data uses old LAD22 codes; add overrides.
    LAD22_TO_CA_STATUS['E08000016'] = 'established';
    LAD22_TO_CA_STATUS['E08000019'] = 'established';
    LAD22_TO_CA_NAME['E08000016']   = 'South Yorkshire';
    LAD22_TO_CA_NAME['E08000019']   = 'South Yorkshire';

    countriesLayer = L.geoJSON(countriesData, {
      style: styleCountry, interactive: false,
    }).addTo(map);

    caLayer = L.geoJSON(caData, { style: styleCA });
    bindInteraction(caLayer, 'ca');
    caLayer.addTo(map);

    // DPP layer: sits on top of caLayer to fill the gaps where DPP areas have no CA polygon
    dppLayer = L.geoJSON(ladData, {
      filter: f => DPP_LADS.has(f.properties.LAD25CD),
      style:  styleDPP,
    });
    bindDPPInteraction(dppLayer);
    dppLayer.addTo(map);

    ladLayer = L.geoJSON(ladData, { style: styleLAD });
    bindInteraction(ladLayer, 'lad');

    updateLegend();
    console.log('Loaded — CAs:', caData.features.length,
                'LADs:', ladData.features.length,
                'DPP LADs:', dppLayer.getLayers().length);

  } catch (err) {
    console.error('Map load error:', err);
    alert(`Could not load map data.\n\n${err.message}\n\nMake sure you are running via Live Server.`);
  }
}

// ── UI listeners ───────────────────────────────────────────────────────────
document.querySelectorAll('.layer-btn').forEach(btn => {
  btn.addEventListener('click', async function () {
    const target = this.dataset.layer;
    if (target === activeLayer) return;

    // Lazy-load MSOA / LSOA on first click
    if (target === 'msoa' && !msoaLayer) {
      const orig = this.textContent;
      this.textContent = 'Loading…';
      this.disabled = true;
      try {
        const data = await loadGeoJSON(`${BASE_PATH}/msoa.geojson`);
        msoaLayer = L.geoJSON(data, { filter: isMSAOrDPP, style: styleMSOA });
        bindInteraction(msoaLayer, 'msoa');
        console.log('MSOA layer:', msoaLayer.getLayers().length, 'features');
      } catch (err) {
        console.error('MSOA load error:', err);
        this.textContent = orig;
        this.disabled = false;
        return;
      }
      this.textContent = orig;
      this.disabled = false;
    }

    if (target === 'lsoa' && !lsoaLayer) {
      const orig = this.textContent;
      this.textContent = 'Loading…';
      this.disabled = true;
      try {
        const data = await loadGeoJSON(`${BASE_PATH}/lsoa.geojson`);
        lsoaLayer = L.geoJSON(data, { filter: isMSAOrDPP, style: styleLSOA });
        bindInteraction(lsoaLayer, 'lsoa');
        console.log('LSOA layer:', lsoaLayer.getLayers().length, 'features');
      } catch (err) {
        console.error('LSOA load error:', err);
        this.textContent = orig;
        this.disabled = false;
        return;
      }
      this.textContent = orig;
      this.disabled = false;
    }

    activeLayer = target;
    document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    applyLayerSwitch(target);
    resetSidebar();
  });
});

document.querySelectorAll('.colour-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const target = this.dataset.colour;
    if (target === colourMode) return;
    colourMode = target;
    document.querySelectorAll('.colour-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    refreshStyles();
  });
});

map.on('click', resetSidebar);

// Dynamically thin MSOA/LSOA borders as the user zooms out.
// Only update the stroke weight — fill colour stays the same — so this is fast.
map.on('zoomend', function () {
  if (activeLayer === 'msoa' && msoaLayer) {
    const w = msoaWeight();
    const o = w > 0 ? 0.5 : 0;
    msoaLayer.eachLayer(l => l.setStyle({ weight: w, opacity: o }));
  }
  if (activeLayer === 'lsoa' && lsoaLayer) {
    const w = lsoaWeight();
    const o = w > 0 ? 0.4 : 0;
    lsoaLayer.eachLayer(l => l.setStyle({ weight: w, opacity: o }));
  }
});

init();
