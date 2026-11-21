import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8868918414:AAE7kUpC6aGfGeRzdASf7cKYWRwkhhhVZwA'  # <--- ВСТАВЬ СЮДА СВОЙ ТОКЕН
WEBAPP_URL = 'https://example.com' # ВРЕМЕННАЯ ССЫЛКА (Telegram требует HTTPS)

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ОБРАБОТЧИК КОМАНДЫ /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем кнопку, которая открывает WebApp (мини-игру)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("Привет! Нажми на кнопку ниже, чтобы открыть кейс-фарм.", reply_markup=kb)

# --- HTML/JS КОД МИНИ-ИГРЫ ---
# (Здесь весь интерфейс, который мы делали ранее, + новый SVG AK47)
HTML_GAME = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Кейсы</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; }
    body {
        font-family: Arial, sans-serif;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        padding: 20px 10px;
        background-color: #ffffff;
        transition: background-color 0.3s ease;
        overflow: hidden;
        position: relative;
    }
    body.dark { background-color: #6b6b6b; }
    h1 { color: #333; font-size: 28px; letter-spacing: 1px; z-index: 2; transition: color 0.3s ease; }
    body.dark h1 { color: #fff; }

    .screen { display: none; flex-direction: column; align-items: center; justify-content: space-between; width: 100%; flex: 1; z-index: 2; }
    .screen.active { display: flex; }
    .content { display: flex; flex-direction: column; align-items: center; gap: 20px; }

    .btn {
        background-color: #b0b0b0; color: #fff; border: none; border-radius: 8px;
        font-size: 16px; font-weight: bold; padding: 14px 30px; cursor: pointer;
        transition: background-color 0.2s ease; z-index: 2;
    }
    .btn:hover { background-color: #909090; }
    .btn:active { background-color: #707070; }
    body.dark .btn { background-color: #8a8a8a; }
    body.dark .btn:active { background-color: #525252; }

    .play-btn { font-size: 20px; padding: 18px 50px; }
    
    .settings-info { text-align: center; color: #333; font-size: 14px; line-height: 1.5; max-width: 300px; z-index: 2; }
    body.dark .settings-info { color: #fff; }
    .settings-list { display: flex; flex-direction: column; gap: 15px; margin-top: 20px; z-index: 2; }
    
    .setting-row { display: flex; align-items: center; gap: 10px; cursor: pointer; user-select: none; }
    .checkbox {
        width: 20px; height: 20px; border: 2px solid #888; border-radius: 4px;
        background-color: #dcdcdc; position: relative; transition: background-color 0.2s; flex-shrink: 0;
    }
    .checkbox.checked { background-color: #4a90d9; border-color: #4a90d9; }
    .checkbox.checked::after {
        content: "✓"; position: absolute; top: 50%; left: 50%;
        transform: translate(-50%, -50%); color: #fff; font-size: 14px; font-weight: bold;
    }
    .setting-label { color: #333; font-size: 16px; transition: color 0.3s; }
    body.dark .setting-label { color: #fff; }

    #snowCanvas { position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; }

    /* Экран кейсов */
    #casesScreen { justify-content: flex-start; gap: 15px; }
    .top-bar { width: 100%; display: flex; justify-content: space-between; align-items: center; z-index: 2; }
    .balance { font-size: 20px; font-weight: bold; color: #333; background-color: #e6e6e6; padding: 6px 14px; border-radius: 6px; }
    body.dark .balance { color: #fff; background-color: #7d7d7d; }

    .cases-layout { display: flex; width: 100%; flex: 1; gap: 15px; z-index: 2; padding-top: 10px; }
    .cases-grid { display: grid; grid-template-columns: 1fr; gap: 8px; width: 100%; max-width: 280px; }
    .case-btn {
        background-color: #b0b0b0; color: #fff; border: none; border-radius: 6px;
        font-size: 16px; font-weight: bold; padding: 12px 20px; cursor: pointer; width: 100%; transition: background-color 0.2s;
    }
    .case-btn:active { background-color: #707070; }

    /* Экран открытия */
    #openScreen { justify-content: space-between; gap: 10px; }
    .open-top { width: 100%; display: flex; justify-content: space-between; align-items: center; z-index: 2; }
    .open-title { font-size: 18px; font-weight: bold; color: #333; }
    body.dark .open-title { color: #fff; }

    .roulette-wrap {
        position: relative; width: 100%; max-width: 400px; height: 140px; overflow: hidden;
        border: 2px solid #888; border-radius: 8px; background-color: #f2f2f2; z-index: 2;
    }
    body.dark .roulette-wrap { background-color: #5a5a5a; border-color: #aaa; }
    .roulette-strip { display: flex; align-items: center; height: 100%; will-change: transform; }
    .roulette-item {
        flex: 0 0 auto; width: 120px; height: 110px; margin: 0 4px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        border-radius: 6px; background-color: #dcdcdc; color: #222; font-weight: bold; gap: 4px;
    }
    body.dark .roulette-item { background-color: #7a7a7a; color: #fff; }
    .roulette-item .skin-name { font-size: 11px; text-align: center; }
    .roulette-item .skin-price { font-size: 13px; color: #2a7d2a; }
    body.dark .roulette-item .skin-price { color: #7dff7d; }

    .roulette-center-line {
        position: absolute; top: 0; bottom: 0; left: 50%; width: 2px;
        background-color: #ff3b3b; transform: translateX(-50%); z-index: 3;
    }

    .chances { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; z-index: 2; max-width: 400px; }
    .chance-item { font-size: 11px; background-color: #e0e0e0; color: #333; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    body.dark .chance-item { background-color: #7d7d7d; color: #fff; }

    .open-bottom { display: flex; gap: 10px; z-index: 2; flex-wrap: wrap; justify-content: center; width: 100%; }
    .result-msg { font-size: 16px; font-weight: bold; color: #2a7d2a; z-index: 2; min-height: 20px; text-align: center; }
    body.dark .result-msg { color: #7dff7d; }

    /* Новый качественный AK-47 */
    .ak-svg {
        width: 90px;
        height: 45px;
        filter: drop-shadow(0 2px 2px rgba(0,0,0,0.3));
    }
</style>
</head>
<body>

<canvas id="snowCanvas"></canvas>

<!-- ГЛАВНЫЙ ЭКРАН -->
<div class="screen active" id="mainScreen">
    <h1>Кейсы</h1>
    <div class="content">
        <button class="btn play-btn" id="playBtn">Играть</button>
        <button class="btn" id="openSettings">Настройки</button>
    </div>
    <button class="btn">Свободный режим</button>
</div>

<!-- ЭКРАН НАСТРОЕК -->
<div class="screen" id="settingsScreen">
    <h1>Настройки</h1>
    <div class="settings-info">
        Кейсфарм – игра про открытие кейсов.<br>Сделано для развлекательного контента
    </div>
    <div class="settings-list">
        <div class="setting-row" id="snowToggle">
            <div class="checkbox" id="snowCheckbox"></div>
            <span class="setting-label">Снежный режим</span>
        </div>
        <div class="setting-row" id="themeToggle">
            <div class="checkbox" id="themeCheckbox"></div>
            <span class="setting-label">Темная тема</span>
        </div>
    </div>
    <button class="btn" id="backBtn">Назад</button>
</div>

<!-- ЭКРАН КЕЙСОВ -->
<div class="screen" id="casesScreen">
    <div class="top-bar">
        <div class="balance" id="balanceDisplay">1$</div>
        <button class="btn" id="casesExitBtn" style="padding:8px 16px; font-size:14px;">Выход</button>
    </div>
    <div class="cases-layout">
        <div class="cases-grid" id="casesGrid"></div>
    </div>
</div>

<!-- ЭКРАН ОТКРЫТИЯ КЕЙСА -->
<div class="screen" id="openScreen">
    <div class="open-top">
        <div class="open-title" id="openTitle">Кейс 1$</div>
        <div class="balance" id="openBalance">1$</div>
    </div>

    <div class="roulette-wrap">
        <div class="roulette-strip" id="rouletteStrip"></div>
        <div class="roulette-center-line"></div>
    </div>

    <div class="chances" id="chancesList"></div>
    <div class="result-msg" id="resultMsg"></div>

    <div class="open-bottom">
        <button class="btn" id="openCaseBtn" style="font-size:16px; padding:12px 24px;">Открыть</button>
        <button class="btn" id="fastSpinBtn" style="font-size:16px; padding:12px 24px;">Быстро</button>
        <button class="btn" id="openExitBtn" style="font-size:16px; padding:12px 24px;">Выход</button>
    </div>
</div>

<script>
    // Инициализация Telegram WebApp
    let tg = window.Telegram.WebApp;
    tg.expand(); // Разворачиваем на весь экран

    const state = {
        snow: false, dark: false, balance: 1, currentCase: null, spinning: false, pendingWin: null
    };

    const mainScreen = document.getElementById('mainScreen');
    const settingsScreen = document.getElementById('settingsScreen');
    const casesScreen = document.getElementById('casesScreen');
    const openScreen = document.getElementById('openScreen');

    const playBtn = document.getElementById('playBtn');
    const openSettingsBtn = document.getElementById('openSettings');
    const backBtn = document.getElementById('backBtn');
    const casesExitBtn = document.getElementById('casesExitBtn');
    const openExitBtn = document.getElementById('openExitBtn');

    const snowToggle = document.getElementById('snowToggle');
    const snowCheckbox = document.getElementById('snowCheckbox');
    const themeToggle = document.getElementById('themeToggle');
    const themeCheckbox = document.getElementById('themeCheckbox');

    const balanceDisplay = document.getElementById('balanceDisplay');
    const openBalance = document.getElementById('openBalance');
    const casesGrid = document.getElementById('casesGrid');
    const openTitle = document.getElementById('openTitle');
    const rouletteStrip = document.getElementById('rouletteStrip');
    const chancesList = document.getElementById('chancesList');
    const resultMsg = document.getElementById('resultMsg');
    const openCaseBtn = document.getElementById('openCaseBtn');
    const fastSpinBtn = document.getElementById('fastSpinBtn');

    function showScreen(screen) {
        [mainScreen, settingsScreen, casesScreen, openScreen].forEach(s => s.classList.remove('active'));
        screen.classList.add('active');
        updateSnow();
    }

    playBtn.addEventListener('click', () => { updateBalanceUI(); showScreen(casesScreen); });
    openSettingsBtn.addEventListener('click', () => showScreen(settingsScreen));
    backBtn.addEventListener('click', () => showScreen(mainScreen));
    casesExitBtn.addEventListener('click', () => showScreen(mainScreen));

    openExitBtn.addEventListener('click', () => {
        if (state.spinning && state.pendingWin) {
            stopSpin();
            state.balance = round2(state.balance + state.pendingWin.price);
            state.pendingWin = null;
            updateBalanceUI();
        }
        stopSpin();
        showScreen(casesScreen);
    });

    function updateBalanceUI() {
        const txt = formatMoney(state.balance);
        balanceDisplay.textContent = txt;
        openBalance.textContent = txt;
    }

    function formatMoney(v) {
        if (Number.isInteger(v)) return v + '$';
        return v.toFixed(2).replace(/\.?0+$/, '') + '$';
    }

    const CASE_PRICES = [1, 5, 25, 100, 500, 2500, 12500, 62500, 312500, 1000000];
    const CASE_MULTIPLIERS = [1.2, 1.6, 2, 2.5, 3];

    function getSkinsForCase(casePrice) {
        const prices = CASE_MULTIPLIERS.map(m => round2(casePrice * m));
        const chances = [40, 25, 18, 12, 5];
        return prices.map((price, i) => ({ name: 'AK47', price: price, chance: chances[i] }));
    }

    function round2(v) { return Math.round(v * 100) / 100; }

    function buildCases() {
        casesGrid.innerHTML = '';
        CASE_PRICES.forEach(price => {
            const btn = document.createElement('button');
            btn.className = 'case-btn';
            btn.textContent = formatMoney(price) + ' кейс';
            btn.addEventListener('click', () => openCase(price));
            casesGrid.appendChild(btn);
        });
    }

    function openCase(price) {
        state.currentCase = { price: price, skins: getSkinsForCase(price) };
        openTitle.textContent = 'Кейс ' + formatMoney(price);
        updateBalanceUI();
        resultMsg.textContent = '';
        state.pendingWin = null;
        buildRoulettePreview(state.currentCase.skins);
        buildChances(state.currentCase.skins);
        showScreen(openScreen);
        stopSpin();
    }

    // ТОТ САМЫЙ КРАСИВЫЙ AK-47 КАК НА ФОТО
    function getAkSvg(woodColor = '#d4883d', metalColor = '#5c5c5c') {
        return `<svg class="ak-svg" viewBox="0 0 200 80" xmlns="http://www.w3.org/2000/svg">
            <!-- Ствол и газовая трубка -->
            <rect x="120" y="35" width="70" height="6" fill="${metalColor}" stroke="#333" stroke-width="1"/>
            <rect x="120" y="28" width="50" height="7" fill="#3a3a3a" stroke="#222" stroke-width="1"/>
            <rect x="170" y="30" width="20" height="3" fill="#222" stroke="#222" stroke-width="1"/>
            
            <!-- Мушка -->
            <path d="M 175 35 L 178 25 L 182 25 L 185 35 Z" fill="#3a3a3a" stroke="#222" stroke-width="1"/>
            <rect x="178" y="20" width="4" height="5" fill="#222"/>

            <!-- Цевье -->
            <path d="M 100 30 L 130 30 L 130 52 L 100 52 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="105" y="35" width="20" height="2" fill="#6b3f1b" opacity="0.6"/>
            <rect x="105" y="42" width="20" height="2" fill="#6b3f1b" opacity="0.6"/>

            <!-- Ресивер -->
            <path d="M 60 30 L 100 30 L 105 55 L 60 55 Z" fill="${metalColor}" stroke="#222" stroke-width="1.5"/>
            <rect x="65" y="33" width="30" height="4" fill="#444" stroke="#222" stroke-width="1"/> <!-- Затвор -->
            <path d="M 70 28 L 85 28 L 80 32 L 65 32 Z" fill="#444" stroke="#222" stroke-width="1"/> <!-- Крышка ствольной коробки -->

            <!-- Магазин -->
            <path d="M 75 55 L 100 55 L 105 75 L 80 75 Z" fill="${metalColor}" stroke="#222" stroke-width="1.5"/>
            <path d="M 82 58 L 98 58 L 102 72 L 86 72 Z" fill="#3a3a3a" /> <!-- Изгиб магазина -->
            <rect x="84" y="62" width="12" height="2" fill="#555" /> <!-- Ребра магазина -->
            <rect x="85" y="66" width="10" height="2" fill="#555" />

            <!-- Пистолетная рукоятка -->
            <path d="M 60 55 L 70 55 L 65 75 L 55 75 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="57" y="62" width="8" height="2" fill="#6b3f1b" opacity="0.6"/>

            <!-- Приклад -->
            <path d="M 25 35 L 60 32 L 62 52 L 25 55 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="30" y="40" width="15" height="2" fill="#6b3f1b" opacity="0.5"/>
            <rect x="30" y="46" width="15" height="2" fill="#6b3f1b" opacity="0.5"/>
            <path d="M 25 35 L 20 36 L 20 54 L 25 55 Z" fill="#5a2e0c" stroke="#333" stroke-width="1"/> <!-- Затыльник приклада -->

            <!-- Спусковой крючок и скоба -->
            <path d="M 75 55 L 85 55 L 85 60 Q 80 65 75 60 Z" fill="#222" />
            <circle cx="80" cy="58" r="2" fill="#222"/>
            <rect x="82" y="55" width="3" height="6" fill="#222"/>

            <!-- Дополнительные детали -->
            <rect x="120" y="53" width="10" height="4" fill="#333" /> <!-- Антабка -->
            <rect x="160" y="42" width="25" height="2" fill="#222" /> <!-- Шомпол -->
        </svg>`;
    }

    function buildRoulettePreview(skins) {
        rouletteStrip.innerHTML = '';
        rouletteStrip.style.transform = 'translateX(0)';
        for (let i = 0; i < 30; i++) {
            const sk = skins[Math.floor(Math.random() * skins.length)];
            rouletteStrip.appendChild(makeRouletteItem(sk));
        }
    }

    function makeRouletteItem(skin) {
        const div = document.createElement('div');
        div.className = 'roulette-item';
        
        // Цвета для разных редкостей
        const colors = [
            { wood: '#d4883d', metal: '#5c5c5c' }, // Обычный
            { wood: '#4a7a5a', metal: '#4a5a6a' }, // Зеленый
            { wood: '#8b3a3a', metal: '#5a3a3a' }, // Красный
            { wood: '#3a4a8b', metal: '#3a3a5a' }, // Синий
            { wood: '#d4af37', metal: '#6b5a1b' }  // Золотой
        ];
        
        const colorIdx = CASE_MULTIPLIERS.findIndex(m => round2(m) === round2(skin.price / (state.currentCase ? state.currentCase.price : 1)));
        const c = colors[colorIdx >= 0 ? colorIdx : 0];
        
        div.innerHTML = `
            ${getAkSvg(c.wood, c.metal)}
            <div class="skin-name">${skin.name}</div>
            <div class="skin-price">${formatMoney(skin.price)}</div>
        `;
        return div;
    }

    function buildChances(skins) {
        chancesList.innerHTML = '';
        skins.forEach(sk => {
            const el = document.createElement('div');
            el.className = 'chance-item';
            el.textContent = `${formatMoney(sk.price)} — ${sk.chance}%`;
            chancesList.appendChild(el);
        });
    }

    let spinAnimId = null;

    function stopSpin() {
        if (spinAnimId) { cancelAnimationFrame(spinAnimId); spinAnimId = null; }
        state.spinning = false;
    }

    function startSpin(fast) {
        if (state.spinning) return;
        if (!state.currentCase) return;
        if (state.balance < state.currentCase.price) {
            resultMsg.textContent = 'Недостаточно средств!';
            return;
        }

        state.balance = round2(state.balance - state.currentCase.price);
        updateBalanceUI();
        resultMsg.textContent = '';

        const winnerIndex = pickByChance(state.currentCase.skins);
        const winner = state.currentCase.skins[winnerIndex];
        state.pendingWin = winner;

        const totalItems = fast ? 40 : 60;
        const winnerPos = fast ? 30 : 50;
        rouletteStrip.innerHTML = '';
        for (let i = 0; i < totalItems; i++) {
            const sk = (i === winnerPos) ? winner : state.currentCase.skins[Math.floor(Math.random() * state.currentCase.skins.length)];
            rouletteStrip.appendChild(makeRouletteItem(sk));
        }
        rouletteStrip.style.transform = 'translateX(0)';

        state.spinning = true;
        const itemWidth = 128; // 120 width + 8 margin (4+4)
        const wrapWidth = rouletteStrip.parentElement.clientWidth;
        const centerOffset = wrapWidth / 2;
        const targetX = -(winnerPos * itemWidth + itemWidth / 2 - centerOffset);

        const startX = 0;
        const duration = fast ? 800 : (4000 + Math.random() * 1000);
        const startTime = performance.now();
        const easeOut = t => 1 - Math.pow(1 - t, 4);

        function animate(now) {
            const elapsed = now - startTime;
            let t = Math.min(elapsed / duration, 1);
            const eased = easeOut(t);
            const x = startX + (targetX - startX) * eased;
            rouletteStrip.style.transform = `translateX(${x}px)`;

            if (t < 1) {
                spinAnimId = requestAnimationFrame(animate);
            } else {
                state.spinning = false;
                spinAnimId = null;
                state.balance = round2(state.balance + winner.price);
                state.pendingWin = null;
                updateBalanceUI();
                resultMsg.textContent = `Выпало: ${winner.name} за ${formatMoney(winner.price)} — продано!`;
            }
        }
        spinAnimId = requestAnimationFrame(animate);
    }

    openCaseBtn.addEventListener('click', () => startSpin(false));
    fastSpinBtn.addEventListener('click', () => startSpin(true));

    function pickByChance(skins) {
        const total = skins.reduce((s, x) => s + x.chance, 0);
        let r = Math.random() * total;
        for (let i = 0; i < skins.length; i++) {
            r -= skins[i].chance;
            if (r <= 0) return i;
        }
        return skins.length - 1;
    }

    function updateSnow() {
        if (state.snow && !openScreen.classList.contains('active')) {
            canvas.style.display = 'block';
            startSnow();
        } else {
            stopSnow();
            canvas.style.display = state.snow ? 'none' : 'block';
        }
    }

    snowToggle.addEventListener('click', () => {
        state.snow = !state.snow;
        snowCheckbox.classList.toggle('checked', state.snow);
        updateSnow();
    });

    themeToggle.addEventListener('click', () => {
        state.dark = !state.dark;
        themeCheckbox.classList.toggle('checked', state.dark);
        document.body.classList.toggle('dark', state.dark);
    });

    const canvas = document.getElementById('snowCanvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    let animId = null;
    let running = false;

    function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function createParticles() {
        const count = Math.min(100, Math.floor((window.innerWidth * window.innerHeight) / 15000));
        particles = [];
        for (let i = 0; i < count; i++) particles.push(newParticle(true));
    }

    function newParticle(randomY) {
        return {
            x: Math.random() * canvas.width,
            y: randomY ? Math.random() * canvas.height : -10,
            r: Math.random() * 2 + 1,
            speedY: Math.random() * 1.2 + 0.6,
            speedX: Math.random() * 0.6 - 0.3,
            drift: Math.random() * Math.PI * 2
        };
    }

    function drawSnow() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = state.dark ? '#ffffff' : '#000000';
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
            p.y += p.speedY;
            p.drift += 0.02;
            p.x += p.speedX + Math.sin(p.drift) * 0.3;
            if (p.y > canvas.height + 10) particles[i] = newParticle(false);
            if (p.x < -10) p.x = canvas.width + 10;
            if (p.x > canvas.width + 10) p.x = -10;
        }
        animId = requestAnimationFrame(drawSnow);
    }

    function startSnow() {
        if (running) return;
        running = true;
        if (particles.length === 0) createParticles();
        drawSnow();
    }

    function stopSnow() {
        running = false;
        if (animId) { cancelAnimationFrame(animId); animId = null; }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles = [];
    }

    buildCases();
    updateBalanceUI();
</script>
</body>
</html>
"""

# --- ЗАПУСК ВЕБ-СЕРВЕРА ДЛЯ МИНИ-ИГРЫ ---
async def handle(request):
    return web.Response(text=HTML_GAME, content_type='text/html')

app = web.Application()
app.router.add_get('/', handle)

async def main():
    # Запускаем веб-сервер на порту 8080 (в фоне)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Веб-сервер запущен на порту 8080")
    
    # Запускаем бота
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
