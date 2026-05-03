/**
 * Lo-Fi Pomodoro — app.js v3.0
 * Sin Spotify, sin generador IA — limpio y funcional
 */

const API = '';

// ─── SONIDO ───────────────────────────────────────────────
function playBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.8);
  } catch(e) {}
}

// ─── ESTADO ───────────────────────────────────────────────
const state = {
  mode: 'study',
  isRunning: false,
  intervalId: null,
  secondsLeft: 25 * 60,
  totalSeconds: 25 * 60,
  sessionStartTime: null,
  currentCycleCount: 0,
  config: { study: 25, short: 5, long: 15, cyclesBeforeLong: 4 },
  discord: { connected: false },
  customTheme: null,
};

// ─── TEMPORIZADOR ─────────────────────────────────────────

function toggleTimer() {
  state.isRunning ? pauseTimer() : startTimer();
}

function startTimer() {
  state.isRunning = true;
  state.sessionStartTime = Date.now();
  document.getElementById('start-btn').textContent = 'Pausar';
  document.getElementById('live-clock').classList.add('hidden');

  state.intervalId = setInterval(() => {
    state.secondsLeft--;
    updateTimerDisplay();
    updateProgressRing();
    if (state.secondsLeft <= 0) {
      clearInterval(state.intervalId);
      onTimerComplete();
    }
  }, 1000);
}

function pauseTimer() {
  state.isRunning = false;
  clearInterval(state.intervalId);
  document.getElementById('start-btn').textContent = 'Continuar';
  document.getElementById('live-clock').classList.remove('hidden');

  if (state.mode === 'study' && state.sessionStartTime) {
    const elapsed = (Date.now() - state.sessionStartTime) / 1000;
    saveStats(elapsed, false);
    state.sessionStartTime = null;
  }
}

function resetTimer() {
  clearInterval(state.intervalId);
  state.isRunning = false;
  state.sessionStartTime = null;
  const mins = { study: state.config.study, short: state.config.short, long: state.config.long };
  state.secondsLeft = mins[state.mode] * 60;
  state.totalSeconds = state.secondsLeft;
  document.getElementById('start-btn').textContent = 'Iniciar';
  document.getElementById('live-clock').classList.remove('hidden');
  updateTimerDisplay();
  updateProgressRing();
}

async function onTimerComplete() {
  document.getElementById('live-clock').classList.remove('hidden');
  playBeep();

  if (Notification.permission === 'granted') {
    const msgs = {
      study: '🍅 ¡Ciclo completado! Hora de descansar.',
      short: '☕ Descanso terminado. ¡A enfocarse!',
      long: '🌙 Descanso largo terminado. ¡Vamos!'
    };
    new Notification('Lo-Fi Pomodoro', { body: msgs[state.mode] });
  }

  if (state.mode === 'study') {
    state.currentCycleCount++;
    await saveStats(state.config.study * 60, true);
    state.sessionStartTime = null;
    updateCycleDots();
    const nextMode = (state.currentCycleCount % state.config.cyclesBeforeLong === 0) ? 'long' : 'short';
    showToast(`🍅 ¡Ciclo ${state.currentCycleCount} completado! Iniciando descanso...`);
    setTimeout(() => { switchMode(nextMode); setTimeout(() => startTimer(), 1500); }, 1000);
  } else {
    showToast('☕ Descanso terminado. ¡A estudiar!');
    setTimeout(() => { switchMode('study'); setTimeout(() => startTimer(), 1500); }, 1000);
  }
}

function switchMode(mode) {
  if (state.isRunning) pauseTimer();
  state.mode = mode;
  const mins = { study: state.config.study, short: state.config.short, long: state.config.long };
  state.secondsLeft = mins[mode] * 60;
  state.totalSeconds = state.secondsLeft;
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
  document.getElementById({ study: 'tab-study', short: 'tab-short', long: 'tab-long' }[mode]).classList.add('active');
  document.getElementById('mode-label').textContent = { study: 'Estudio', short: 'Descanso Corto', long: 'Descanso Largo' }[mode];
  document.getElementById('start-btn').textContent = 'Iniciar';
  updateTimerDisplay();
  updateProgressRing();
}

function updateTimerDisplay() {
  const m = Math.floor(state.secondsLeft / 60).toString().padStart(2, '0');
  const s = (state.secondsLeft % 60).toString().padStart(2, '0');
  document.getElementById('timer-display').textContent = `${m}:${s}`;
  document.title = `${m}:${s} — Lo-Fi Pomodoro`;
}

function updateProgressRing() {
  document.getElementById('progress-ring').style.strokeDashoffset = 628.3 * (1 - state.secondsLeft / state.totalSeconds);
}

function updateCycleDots() {
  const container = document.getElementById('cycles-dots');
  const total = state.config.cyclesBeforeLong;
  const filled = state.currentCycleCount % total || (state.currentCycleCount > 0 && state.currentCycleCount % total === 0 ? total : 0);
  container.innerHTML = '';
  for (let i = 0; i < total; i++) {
    const dot = document.createElement('div');
    dot.className = `cycle-dot ${i < filled ? 'filled' : ''}`;
    container.appendChild(dot);
  }
}

// ─── RELOJ ────────────────────────────────────────────────

function startLiveClock() {
  function tick() {
    const now = new Date();
    document.getElementById('live-clock').textContent =
      `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;
  }
  tick();
  setInterval(tick, 1000);
}

// ─── CONFIGURACIÓN ────────────────────────────────────────

function openSettings() {
  document.getElementById('settings-overlay').classList.remove('hidden');
  document.getElementById('settings-overlay').classList.add('open');
  if (Notification.permission === 'default') Notification.requestPermission();
}

function closeSettings() {
  document.getElementById('settings-overlay').classList.add('hidden');
  document.getElementById('settings-overlay').classList.remove('open');
}

function updateLabel(inputId, labelId) {
  document.getElementById(labelId).textContent = document.getElementById(inputId).value;
}

function applySettings() {
  state.config.study = parseInt(document.getElementById('cfg-study').value);
  state.config.short = parseInt(document.getElementById('cfg-short').value);
  state.config.long = parseInt(document.getElementById('cfg-long').value);
  state.config.cyclesBeforeLong = parseInt(document.getElementById('cfg-cycles').value);
  resetTimer();
  updateCycleDots();
  closeSettings();
  showToast('⚙ Configuración aplicada');
}

// ─── ESTADÍSTICAS ─────────────────────────────────────────

async function loadTodayStats() {
  try {
    const res = await fetch(`${API}/api/stats/today`);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-hours').textContent = data.total_hours_studied.toFixed(2);
    document.getElementById('stat-cycles').textContent = data.cycles_completed;
    document.getElementById('stat-streak').textContent = state.currentCycleCount;
  } catch (e) {}
}

async function saveStats(seconds, cycleCompleted) {
  try {
    const res = await fetch(`${API}/api/stats/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seconds_studied: seconds, cycle_completed: cycleCompleted })
    });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-hours').textContent = data.total_hours_studied.toFixed(2);
    document.getElementById('stat-cycles').textContent = data.cycles_completed;
    document.getElementById('stat-streak').textContent = state.currentCycleCount;
  } catch (e) {}
}

async function resetTodayStats() {
  if (!confirm('¿Reiniciar estadísticas de hoy?')) return;
  try {
    await fetch(`${API}/api/stats/reset`, { method: 'DELETE' });
    state.currentCycleCount = 0;
    updateCycleDots();
    await loadTodayStats();
    closeSettings();
    showToast('↺ Estadísticas reiniciadas');
  } catch (e) {}
}

// ─── CLIMA ────────────────────────────────────────────────

const WEATHER_ICONS = { sunny: '☀️', cloudy: '☁️', rainy: '🌧️' };

async function loadWeather() {
  if (state.customTheme && state.customTheme !== 'auto') return;
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      async (pos) => await fetchWeather(pos.coords.latitude, pos.coords.longitude),
      async () => await fetchWeather(null, null),
      { timeout: 8000 }
    );
  } else {
    await fetchWeather(null, null);
  }
}

async function fetchWeather(lat, lon) {
  try {
    const url = (lat !== null && lon !== null)
      ? `${API}/api/weather/current?lat=${lat}&lon=${lon}`
      : `${API}/api/weather/current`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('weather-icon').textContent = WEATHER_ICONS[data.condition] || '🌤️';
    document.getElementById('weather-temp').textContent = `${data.temperature}°C`;
    document.getElementById('weather-city').textContent = data.city;
    applyBackground(data.background_key);
  } catch (e) {
    const hour = new Date().getHours();
    const t = hour < 12 ? 'morning' : hour < 19 ? 'afternoon' : 'night';
    applyBackground(`${t}_cloudy`);
  }
}

function applyBackground(key) {
  const bg = document.getElementById('bg-layer');
  const classes = ['morning-sunny','morning-cloudy','morning-rainy',
    'afternoon-sunny','afternoon-cloudy','afternoon-rainy',
    'night-sunny','night-cloudy','night-rainy',
    'dark-landscape','pink-dream','purple-galaxy','ocean-night',
    'sunset-warm','mint-forest','rainy-city','cherry-blossom'];
  classes.forEach(c => bg.classList.remove(`bg-${c}`));
  bg.style.background = '';
  bg.classList.add(`bg-${key.replace(/_/g, '-')}`);
}

// ─── TEMAS ────────────────────────────────────────────────

function openThemes() {
  document.getElementById('themes-overlay').classList.remove('hidden');
  document.getElementById('themes-overlay').classList.add('open');
}

function closeThemes() {
  document.getElementById('themes-overlay').classList.add('hidden');
  document.getElementById('themes-overlay').classList.remove('open');
}

function applyTheme(key) {
  state.customTheme = key;
  if (key === 'auto') {
    state.customTheme = null;
    loadWeather();
    closeThemes();
    showToast('🌍 Tema automático activado');
    return;
  }
  const THEMES = {
    dark_landscape: 'linear-gradient(135deg, #0d1b0d 0%, #1a2a1a 50%, #0a1a0a 100%)',
    pink_dream:     'linear-gradient(135deg, #ff6b9d 0%, #c44db5 50%, #8b1a8b 100%)',
    purple_galaxy:  'linear-gradient(135deg, #4a0080 0%, #1a0040 50%, #0d001a 100%)',
    ocean_night:    'linear-gradient(135deg, #001a33 0%, #003366 50%, #001a4d 100%)',
    sunset_warm:    'linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #c0392b 100%)',
    mint_forest:    'linear-gradient(135deg, #00b09b 0%, #096644 50%, #004d33 100%)',
    rainy_city:     'linear-gradient(135deg, #2c3e50 0%, #4a6274 50%, #1a2a36 100%)',
    cherry_blossom: 'linear-gradient(135deg, #ffb7c5 0%, #d4547a 50%, #a03060 100%)',
  };
  const bg = document.getElementById('bg-layer');
  bg.className = 'fixed inset-0 z-0 transition-all duration-1500';
  bg.style.background = THEMES[key] || THEMES.dark_landscape;
  closeThemes();
  const names = {
    dark_landscape: '🌲 Paisaje Oscuro', pink_dream: '🌸 Sueño Rosa',
    purple_galaxy: '🌌 Galaxia Morada', ocean_night: '🌊 Océano Nocturno',
    sunset_warm: '🌅 Atardecer Cálido', mint_forest: '🍃 Bosque Menta',
    rainy_city: '🌧️ Ciudad Lluviosa', cherry_blossom: '🌺 Cerezo en Flor'
  };
  showToast(`${names[key]} activado`);
}

// ─── DISCORD ──────────────────────────────────────────────

function handleDiscordLogin() {
  window.location.href = `${API}/api/discord/login`;
}

async function loadDiscordUser() {
  try {
    const res = await fetch(`${API}/api/discord/me`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.connected) {
      document.getElementById('discord-username').textContent = data.username;
      document.getElementById('discord-status-text').textContent = data.status || 'online';
      if (data.avatar_url) {
        document.getElementById('discord-avatar').src = data.avatar_url;
        document.getElementById('discord-avatar-wrap').classList.remove('hidden');
      }
      document.getElementById('discord-status-dot').className =
        `absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-black/40 status-${data.status || 'online'}`;
      const btn = document.getElementById('discord-btn');
      btn.textContent = '✕';
      btn.onclick = handleDiscordLogout;
      state.discord.connected = true;
    }
  } catch (e) {}
}

async function handleDiscordLogout() {
  await fetch(`${API}/api/discord/logout`, { method: 'POST' });
  state.discord.connected = false;
  document.getElementById('discord-username').textContent = 'Sin conectar';
  document.getElementById('discord-status-text').textContent = 'Discord';
  document.getElementById('discord-avatar-wrap').classList.add('hidden');
  const btn = document.getElementById('discord-btn');
  btn.textContent = 'Conectar';
  btn.onclick = handleDiscordLogin;
}

// ─── TOAST ────────────────────────────────────────────────

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.classList.add('hidden'), 300);
  }, 3500);
}

// ─── URL PARAMS ───────────────────────────────────────────

function checkURLParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('discord') === 'connected') {
    showToast('💬 Discord conectado');
    window.history.replaceState({}, '', '/');
    loadDiscordUser();
  }
}

// ─── INIT ─────────────────────────────────────────────────

async function init() {
  updateTimerDisplay();
  updateProgressRing();
  updateCycleDots();
  startLiveClock();
  await loadTodayStats();
  await loadWeather();
  setInterval(loadWeather, 10 * 60 * 1000);
  await loadDiscordUser();
  checkURLParams();
  document.getElementById('settings-overlay').addEventListener('click', (e) => { if (e.target === e.currentTarget) closeSettings(); });
  document.getElementById('themes-overlay').addEventListener('click', (e) => { if (e.target === e.currentTarget) closeThemes(); });
  if (Notification.permission === 'default') setTimeout(() => Notification.requestPermission(), 2000);
  console.log('🍅 Lo-Fi Pomodoro v3.0');
}

document.addEventListener('DOMContentLoaded', init);