// web-dashboard/src/main.js
// =========================
// Final submission version
// =========================

import {
  Chart,
  LineController, LineElement, PointElement,
  LinearScale, CategoryScale,
  Legend, Tooltip
} from 'chart.js';

Chart.register(
  LineController, LineElement, PointElement,
  LinearScale, CategoryScale, Legend, Tooltip
);

// ---------- tiny helpers ----------
const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const show = sel => { const el = $(sel); if (el) el.style.display = ''; };
const hide = sel => { const el = $(sel); if (el) el.style.display = 'none'; };

// ---------- config ----------
const API = (import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const INGEST_TOKEN = import.meta.env?.VITE_INGEST_TOKEN || '';
const USER_KEY = 'ec_user';                           // local demo auth

// ---------- global UI state ----------
let chart = null;       // single Chart.js instance
let feedTimer = null;   // simulation timer
let paused = false;     // pause chart drawing

// ---------- demo-auth (browser only) ----------
function isAuthed() {
  try { return !!JSON.parse(localStorage.getItem(USER_KEY)); }
  catch { return false; }
}
function currentEmail() {
  try { return JSON.parse(localStorage.getItem(USER_KEY))?.email || ''; }
  catch { return ''; }
}
function login(email) {
  localStorage.setItem(USER_KEY, JSON.stringify({ email }));
}
function logout() {
  localStorage.removeItem(USER_KEY);
  stopSimulation();
  // clear nav/email
  $('#nav-email') && ($('#nav-email').textContent = '');
  route();
}

// ---------- color helpers (ONE set) ----------
function hrColor(v) {
  if (v == null) return 'rgba(37,99,235,.6)';      // default blue
  return (v < 60 || v > 120) ? '#dc2626' : '#2563eb';
}
function spo2Color(v) {
  if (v == null) return 'rgba(244,63,94,.6)';      // default pink
  return (v < 92) ? '#dc2626' : '#f43f5e';
}

// ---------- chart ----------
function makeChart() {
  const canvas = document.getElementById('trend');
  if (!canvas) return;

  // If we already have a chart on this canvas, destroy it first (Chart.js v4 rule)
  const prev = Chart.getChart(canvas);
  if (prev) prev.destroy();

  const ctx = canvas.getContext('2d');

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [], // we push times here
      datasets: [
        {
          label: 'Heart Rate (bpm)',
          data: [],
          yAxisID: 'yL',
          borderWidth: 2,
          tension: 0.3,
          segment: { borderColor: c => hrColor(c?.p1?.parsed?.y) },
          pointRadius: 2,
          pointHoverRadius: 3,
          pointBackgroundColor: c => hrColor(c?.parsed?.y),
        },
        {
          label: 'SpO₂ (%)',
          data: [],
          yAxisID: 'yR',
          borderWidth: 2,
          borderDash: [4, 3],
          tension: 0.3,
          segment: { borderColor: c => spo2Color(c?.p1?.parsed?.y) },
          pointRadius: 2,
          pointHoverRadius: 3,
          pointBackgroundColor: c => spo2Color(c?.parsed?.y),
        },
      ],
    },
    options: {
      animation: false,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed?.y;
              if (ctx.dataset.yAxisID === 'yL') {
                return v == null ? 'HR: —' : `HR: ${Math.round(v)} bpm`;
              }
              return v == null ? 'SpO₂: —' : `SpO₂: ${Math.round(v)} %`;
            },
          },
        },
      },
      // We use string time labels → 'category' keeps it simple (no date adapters)
      scales: {
        x: { type: 'category', ticks: { autoSkip: true, maxTicksLimit: 6 } },
        yL: {
          position: 'left', min: 40, max: 160,
          title: { display: true, text: 'bpm' },
        },
        yR: {
          position: 'right', min: 84, max: 100,
          title: { display: true, text: '%' },
          grid: { drawOnChartArea: false },
        },
      },
    },
  });
}

// push a point into the chart + update KPI cards
function pushPoint({ hr, spo2, temp, fall }) {
  if (!chart) return;

  const t = new Date().toLocaleTimeString();
  chart.data.labels.push(t);
  chart.data.datasets[0].data.push(hr);
  chart.data.datasets[1].data.push(spo2);

  // keep last 60
  if (chart.data.labels.length > 60) {
    chart.data.labels.shift();
    chart.data.datasets.forEach(d => d.data.shift());
  }
  chart.update('none');

  // KPI cards
  $('#card-hr .value')   && ($('#card-hr .value').textContent   = `${Math.round(hr)} bpm`);
  $('#card-spo2 .value') && ($('#card-spo2 .value').textContent = `${Math.round(spo2)} %`);
  $('#card-temp .value') && ($('#card-temp .value').textContent = `${temp.toFixed(1)} °C`);
  $('#card-fall .value') && ($('#card-fall .value').textContent = fall ? 'Yes' : 'No');
}

// ---------- simulation ----------
function startSimulation() {
  stopSimulation(); // ensure clean start
  const intSec = Math.max(1, parseInt($('#interval')?.value || '2', 10));

  $('#btn-start')?.setAttribute('disabled', 'true');
  $('#btn-stop')?.removeAttribute('disabled');

  feedTimer = setInterval(async () => {
    // generate plausible readings
    const hr   = 60 + Math.random() * 70;
    const spo2 = 88 + Math.random() * 12;
    const temp = 36 + Math.random() * 2;
    const fall = Math.random() < 0.05;

    // send to API (token optional)
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (INGEST_TOKEN) headers.Authorization = `Bearer ${INGEST_TOKEN}`;
      await fetch(`${API}/ingest`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          device_id: 'demo',
          heart_rate: hr,
          spo2,
          temperature: temp,
          fall_detected: fall,
        }),
      });
    } catch { /* ignore network hiccups in demo */ }

    if (!paused) pushPoint({ hr, spo2, temp, fall });
  }, intSec * 1000);
}

function stopSimulation() {
  if (feedTimer) clearInterval(feedTimer);
  feedTimer = null;
  $('#btn-stop')?.setAttribute('disabled', 'true');
  $('#btn-start')?.removeAttribute('disabled');
}

function pauseChart()  { paused = true;  }
function resumeChart() { paused = false; }

// ---------- views (mounters) ----------
function setActive(tabId) {
  $$('.tabs a').forEach(a => a.classList.remove('active'));
  $(tabId)?.classList.add('active');
}

function mountAuth() {
  hide('#view-dash'); hide('#view-alerts'); hide('#view-reports'); show('#view-auth');
  $('#nav-email') && ($('#nav-email').textContent = '');
  $('#btn-logout') && ($('#btn-logout').style.display = 'none');

  const form = $('#auth-form');
  if (form && !form.dataset.bound) {
    form.dataset.bound = '1';
    form.addEventListener('submit', e => {
      e.preventDefault();
      const email = $('#auth-email')?.value?.trim();
      if (!email) return;
      login(email);
      location.hash = '#/dashboard';
      route();
    });
  }
}

async function mountDashboard() {
  hide('#view-auth'); hide('#view-alerts'); hide('#view-reports'); show('#view-dash');
  setActive('#tab-d');
  $('#nav-email') && ($('#nav-email').textContent = currentEmail());
  $('#btn-logout') && ($('#btn-logout').style.display = '');

  // (re)create chart & wire controls
  makeChart();

  $('#btn-pause')  && ($('#btn-pause').onclick  = () => pauseChart());
  $('#btn-resume') && ($('#btn-resume').onclick = () => resumeChart());
  $('#btn-start')  && ($('#btn-start').onclick  = () => startSimulation());
  $('#btn-stop')   && ($('#btn-stop').onclick   = () => stopSimulation());

  // set initial card values
  $('#card-hr .value')   && ($('#card-hr .value').textContent   = '-- bpm');
  $('#card-spo2 .value') && ($('#card-spo2 .value').textContent = '-- %');
  $('#card-temp .value') && ($('#card-temp .value').textContent = '-- °C');
  $('#card-fall .value') && ($('#card-fall .value').textContent = 'No');
}

async function mountAlerts() {
  hide('#view-auth'); hide('#view-dash'); hide('#view-reports'); show('#view-alerts');
  setActive('#tab-a');

  const ul = $('#alert-list');
  if (ul) ul.innerHTML = '';
  try {
    const r = await fetch(`${API}/alerts`);
    const items = await r.json();
    items.forEach(a => {
      const li = document.createElement('li');
      li.className = 'alert-item';
      li.textContent = `[${a.created_at}] ${a.severity?.toUpperCase()} ${a.message}`;
      ul?.appendChild(li);
    });
  } catch { /* ignore */ }

  // export
  if (!$('#btn-export-alerts')?.dataset.bound) {
    $('#btn-export-alerts').dataset.bound = '1';
    $('#btn-export-alerts').addEventListener('click', () =>
      window.open(`${API}/export/alerts.csv`, '_blank'));
  }
}

async function mountReports() {
  hide('#view-auth'); hide('#view-dash'); hide('#view-alerts'); show('#view-reports');
  setActive('#tab-r');

  // export buttons
  if (!$('#btn-export-readings')?.dataset.bound) {
    $('#btn-export-readings').dataset.bound = '1';
    $('#btn-export-readings').addEventListener('click', () =>
      window.open(`${API}/export/readings.csv`, '_blank'));
  }
  if (!$('#btn-export-alerts-2')?.dataset.bound) {
    $('#btn-export-alerts-2').dataset.bound = '1';
    $('#btn-export-alerts-2').addEventListener('click', () =>
      window.open(`${API}/export/alerts.csv`, '_blank'));
  }

  try {
    const r = await fetch(`${API}/version`);
    $('#version-json') && ($('#version-json').textContent = JSON.stringify(await r.json(), null, 2));
  } catch { /* ignore */ }
}

// ---------- router ----------
function route() {
  const h = location.hash || '#/auth';

  // logout wiring (always)
  const lo = $('#btn-logout');
  if (lo && !lo.dataset.bound) {
    lo.dataset.bound = '1';
    lo.addEventListener('click', () => logout());
  }

  if (!isAuthed()) { mountAuth(); return; }
  if (h.startsWith('#/dashboard')) { mountDashboard(); return; }
  if (h.startsWith('#/alerts'))    { mountAlerts(); return; }
  if (h.startsWith('#/reports'))   { mountReports(); return; }
  mountDashboard();
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', route);
