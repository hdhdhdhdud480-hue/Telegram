import asyncio
import logging
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    InlineQueryResultArticle, InputTextMessageContent
)

# --- НАСТРОЙКИ ---
BOT_TOKEN = '8868918414:AAE7kUpC6aGfGeRzdASf7cKYWRwkhhhVZwA'
WEBAPP_URL = 'https://genuine-creativity-production-58b6a574.up.railway.app'
BOT_USERNAME = 'GameSeregabot'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance REAL DEFAULT 1.0)''')
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 1.0

def update_balance_in_db(user_id, username, first_name, new_balance):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (user_id, username, first_name, balance) 
                 VALUES (?, ?, ?, ?) 
                 ON CONFLICT(user_id) DO UPDATE SET 
                 balance = excluded.balance,
                 username = excluded.username,
                 first_name = excluded.first_name''', (user_id, username, first_name, new_balance))
    conn.commit()
    conn.close()

def reset_user_balance(user_id):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('UPDATE users SET balance = 1.0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_top_players():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('SELECT username, first_name, user_id, balance FROM users ORDER BY balance DESC LIMIT 10')
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# --- ОБРАБОТЧИКИ КОМАНД БОТА ---
@dp.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: types.Message, command: CommandObject):
    if command.args == "play_game":
        await show_game_menu(message)
    else:
        await cmd_start(message)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "Привет! Нажми на кнопку ниже, чтобы открыть кейс-фарм.\n\n"
        "А еще ты можешь отправить меня в любой чат! Просто напиши в поле ввода:\n"
        f"`@{BOT_USERNAME} Игра в кейсы заходи`", 
        reply_markup=kb, 
        parse_mode="Markdown"
    )

async def show_game_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть игру", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer("Добро пожаловать в игру! Жми кнопку ниже, чтобы начать.", reply_markup=kb)

# --- ИНЛАЙН РЕЖИМ ---
@dp.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    msg_text = "🔥 <b>Кейсфарм</b> — игра про открытие кейсов!\nЗаходи и попробуй выбить AK47 за триллион долларов."
    deep_link = f"https://t.me/{BOT_USERNAME}?start=play_game"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Зайти", url=deep_link)]
    ])

    result = InlineQueryResultArticle(
        id="casefarm_game",
        title="Игра в кейсы",
        description="Нажми, чтобы отправить приглашение в игру",
        input_message_content=InputTextMessageContent(
            message_text=msg_text,
            parse_mode="HTML"
        ),
        reply_markup=kb,
        thumb_url="https://cdn-icons-png.flaticon.com/512/2592/2592989.png"
    )

    await inline_query.answer([result], cache_time=1)

# --- HTML/JS КОД МИНИ-ИГРЫ ---
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

    .screen { display: none; flex-direction: column; align-items: center; justify-content: space-between; width: 100%; flex: 1; z-index: 2; height: 100%; }
    .screen.active { display: flex; }
    .content { display: flex; flex-direction: column; align-items: center; gap: 15px; }

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

    #casesScreen, #freeCasesScreen { justify-content: flex-start; gap: 15px; height: 100%; overflow: hidden; }
    .top-bar { width: 100%; display: flex; justify-content: space-between; align-items: center; z-index: 2; flex-shrink: 0; }
    .balance { font-size: 20px; font-weight: bold; color: #333; background-color: #e6e6e6; padding: 6px 14px; border-radius: 6px; }
    body.dark .balance { color: #fff; background-color: #7d7d7d; }

    .cases-layout { display: flex; width: 100%; flex: 1; gap: 15px; z-index: 2; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-bottom: 20px; }
    .cases-grid { display: grid; grid-template-columns: 1fr; gap: 8px; width: 100%; max-width: 280px; margin: 0 auto; }
    .case-btn {
        background-color: #b0b0b0; color: #fff; border: none; border-radius: 6px;
        font-size: 16px; font-weight: bold; padding: 12px 20px; cursor: pointer; width: 100%; transition: background-color 0.2s;
    }
    .case-btn:active { background-color: #707070; }

    #openScreen, #freeOpenScreen { justify-content: space-between; gap: 10px; }
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

    .ak-svg { width: 90px; height: 45px; filter: drop-shadow(0 2px 2px rgba(0,0,0,0.3)); }

    .top-table { width: 100%; max-width: 350px; background: #e6e6e6; border-radius: 8px; overflow: hidden; z-index: 2; }
    body.dark .top-table { background: #7d7d7d; }
    .top-row { display: flex; justify-content: space-between; padding: 10px 15px; border-bottom: 1px solid #ccc; font-size: 14px; color: #333; }
    body.dark .top-row { border-bottom-color: #555; color: #fff; }
    .top-row:last-child { border-bottom: none; }
    .top-row:nth-child(1) { background: #f9d71c; font-weight: bold; color: #000; }
    .top-row:nth-child(2) { background: #c0c0c0; font-weight: bold; color: #000; }
    .top-row:nth-child(3) { background: #cd7f32; font-weight: bold; color: #000; }

    .warning-box { background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 8px; text-align: center; max-width: 300px; z-index: 2; }
    body.dark .warning-box { background: #4a4a4a; border-color: #888; color: #fff; }
    .btn-red { background: #dc3545; }
    .btn-red:hover { background-color: #c82333; }
    .btn-green { background: #28a745; }
    .btn-green:hover { background-color: #218838; }
</style>
</head>
<body>

<canvas id="snowCanvas"></canvas>

<div class="screen active" id="mainScreen">
    <h1>Кейсы</h1>
    <div class="content">
        <button class="btn play-btn" id="playBtn">Играть</button>
        <button class="btn" id="openSettings">Настройки</button>
        <button class="btn" id="openTop">🏆 Топ игроков</button>
    </div>
    <button class="btn" id="freeModeBtn">Свободный режим</button>
</div>

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
    <div class="content" style="margin-bottom: 20px;">
        <button class="btn btn-red" id="newGameBtn">Новая игра</button>
        <button class="btn" id="backBtn">Назад</button>
    </div>
</div>

<div class="screen" id="warningScreen">
    <h1>Внимание</h1>
    <div class="warning-box">
        При этом действии вы начнете все сначала, и ваш баланс сбросится до 1$.<br><br>
        Продолжить?
    </div>
    <div class="content">
        <button class="btn btn-red" id="confirmNewGame">Продолжить</button>
        <button class="btn btn-green" id="cancelNewGame">Не продолжать</button>
    </div>
</div>

<div class="screen" id="casesScreen">
    <div class="top-bar">
        <div class="balance" id="balanceDisplay">1$</div>
        <button class="btn" id="casesExitBtn" style="padding:8px 16px; font-size:14px;">Выход</button>
    </div>
    <div class="cases-layout">
        <div class="cases-grid" id="casesGrid"></div>
    </div>
</div>

<div class="screen" id="freeCasesScreen">
    <div class="top-bar">
        <div class="balance">Свободный режим (1$)</div>
        <button class="btn" id="freeCasesExitBtn" style="padding:8px 16px; font-size:14px;">Выход</button>
    </div>
    <div class="cases-layout">
        <div class="cases-grid" id="freeCasesGrid"></div>
    </div>
</div>

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

<div class="screen" id="freeOpenScreen">
    <div class="open-top">
        <div class="open-title" id="freeOpenTitle">Кейс 1$ (Свободный)</div>
        <div class="balance">Бесконечно</div>
    </div>
    <div class="roulette-wrap">
        <div class="roulette-strip" id="freeRouletteStrip"></div>
        <div class="roulette-center-line"></div>
    </div>
    <div class="chances" id="freeChancesList"></div>
    <div class="result-msg" id="freeResultMsg"></div>
    <div class="open-bottom">
        <button class="btn" id="freeOpenCaseBtn" style="font-size:16px; padding:12px 24px;">Открыть</button>
        <button class="btn" id="freeFastSpinBtn" style="font-size:16px; padding:12px 24px;">Быстро</button>
        <button class="btn" id="freeOpenExitBtn" style="font-size:16px; padding:12px 24px;">Выход</button>
    </div>
</div>

<div class="screen" id="topScreen">
    <h1>🏆 Топ игроков</h1>
    <div class="top-table" id="topTable"></div>
    <button class="btn" id="topExitBtn">Назад</button>
</div>

<script>
    let tg = window.Telegram.WebApp;
    tg.expand();

    const state = { snow: false, dark: false, balance: 1, currentCase: null, spinning: false, pendingWin: null, isFreeMode: false };
    const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 0;
    const username = tg.initDataUnsafe.user ? (tg.initDataUnsafe.user.username || '') : '';
    const firstName = tg.initDataUnsafe.user ? (tg.initDataUnsafe.user.first_name || 'Игрок') : 'Игрок';

    const mainScreen = document.getElementById('mainScreen');
    const settingsScreen = document.getElementById('settingsScreen');
    const casesScreen = document.getElementById('casesScreen');
    const openScreen = document.getElementById('openScreen');
    const topScreen = document.getElementById('topScreen');
    const warningScreen = document.getElementById('warningScreen');
    const freeCasesScreen = document.getElementById('freeCasesScreen');
    const freeOpenScreen = document.getElementById('freeOpenScreen');

    const playBtn = document.getElementById('playBtn');
    const openSettingsBtn = document.getElementById('openSettings');
    const backBtn = document.getElementById('backBtn');
    const casesExitBtn = document.getElementById('casesExitBtn');
    const openExitBtn = document.getElementById('openExitBtn');
    const openTopBtn = document.getElementById('openTop');
    const topExitBtn = document.getElementById('topExitBtn');
    const freeModeBtn = document.getElementById('freeModeBtn');
    const freeCasesExitBtn = document.getElementById('freeCasesExitBtn');
    const freeOpenExitBtn = document.getElementById('freeOpenExitBtn');
    
    const newGameBtn = document.getElementById('newGameBtn');
    const confirmNewGame = document.getElementById('confirmNewGame');
    const cancelNewGame = document.getElementById('cancelNewGame');

    const snowToggle = document.getElementById('snowToggle');
    const snowCheckbox = document.getElementById('snowCheckbox');
    const themeToggle = document.getElementById('themeToggle');
    const themeCheckbox = document.getElementById('themeCheckbox');

    const balanceDisplay = document.getElementById('balanceDisplay');
    const openBalance = document.getElementById('openBalance');
    const casesGrid = document.getElementById('casesGrid');
    const freeCasesGrid = document.getElementById('freeCasesGrid');
    const openTitle = document.getElementById('openTitle');
    const rouletteStrip = document.getElementById('rouletteStrip');
    const chancesList = document.getElementById('chancesList');
    const resultMsg = document.getElementById('resultMsg');
    const openCaseBtn = document.getElementById('openCaseBtn');
    const fastSpinBtn = document.getElementById('fastSpinBtn');
    const topTable = document.getElementById('topTable');

    const freeOpenTitle = document.getElementById('freeOpenTitle');
    const freeRouletteStrip = document.getElementById('freeRouletteStrip');
    const freeChancesList = document.getElementById('freeChancesList');
    const freeResultMsg = document.getElementById('freeResultMsg');
    const freeOpenCaseBtn = document.getElementById('freeOpenCaseBtn');
    const freeFastSpinBtn = document.getElementById('freeFastSpinBtn');

    function showScreen(screen) {
        [mainScreen, settingsScreen, casesScreen, openScreen, topScreen, warningScreen, freeCasesScreen, freeOpenScreen].forEach(s => s.classList.remove('active'));
        screen.classList.add('active');
        updateSnow();
    }

    async function fetchBalance() {
        if (!userId) return;
        try {
            const res = await fetch('/api/get_balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username: username, first_name: firstName })
            });
            const data = await res.json();
            state.balance = data.balance;
            updateBalanceUI();
        } catch (e) { console.error(e); }
    }

    async function syncBalance() {
        if (!userId) return;
        try {
            await fetch('/api/update_balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username: username, first_name: firstName, balance: state.balance })
            });
        } catch (e) { console.error(e); }
    }

    async function resetBalanceOnServer() {
        if (!userId) return;
        try {
            await fetch('/api/reset_balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            state.balance = 1.0;
            updateBalanceUI();
        } catch (e) { console.error(e); }
    }

    async function loadTop() {
        try {
            const res = await fetch('/api/get_top');
            const data = await res.json();
            topTable.innerHTML = '';
            if (data.length === 0) {
                topTable.innerHTML = '<div class="top-row">Пока нет игроков</div>';
                return;
            }
            data.forEach((user, index) => {
                const div = document.createElement('div');
                div.className = 'top-row';
                const name = user.username ? '@' + user.username : (user.first_name || 'ID: ' + user.user_id);
                div.innerHTML = `<span>${index + 1}. ${name}</span> <span>${formatMoney(user.balance)}</span>`;
                topTable.appendChild(div);
            });
        } catch (e) {
            topTable.innerHTML = '<div class="top-row">Ошибка загрузки</div>';
        }
    }

    playBtn.addEventListener('click', () => { state.isFreeMode = false; fetchBalance(); showScreen(casesScreen); });
    openSettingsBtn.addEventListener('click', () => showScreen(settingsScreen));
    backBtn.addEventListener('click', () => showScreen(mainScreen));
    casesExitBtn.addEventListener('click', () => { syncBalance(); showScreen(mainScreen); });
    openTopBtn.addEventListener('click', () => { loadTop(); showScreen(topScreen); });
    topExitBtn.addEventListener('click', () => showScreen(mainScreen));
    
    freeModeBtn.addEventListener('click', () => {
        state.isFreeMode = true;
        buildFreeCases();
        showScreen(freeCasesScreen);
    });
    freeCasesExitBtn.addEventListener('click', () => showScreen(mainScreen));

    newGameBtn.addEventListener('click', () => showScreen(warningScreen));
    cancelNewGame.addEventListener('click', () => showScreen(settingsScreen));
    confirmNewGame.addEventListener('click', async () => {
        await resetBalanceOnServer();
        showScreen(settingsScreen);
    });

    openExitBtn.addEventListener('click', () => {
        if (state.spinning && state.pendingWin) {
            stopSpin();
            state.balance = round2(state.balance + state.pendingWin.price);
            state.pendingWin = null;
            updateBalanceUI();
            syncBalance();
        }
        stopSpin();
        showScreen(casesScreen);
    });

    freeOpenExitBtn.addEventListener('click', () => {
        stopSpin();
        showScreen(freeCasesScreen);
    });

    function updateBalanceUI() {
        const txt = formatMoney(state.balance);
        balanceDisplay.textContent = txt;
        openBalance.textContent = txt;
    }

    function formatMoney(v) {
        if (v >= 1e20) return '∞$'; 
        if (!isFinite(v)) return '∞$';
        
        let str;
        if (Number.isInteger(v)) {
            str = v.toLocaleString('fullwide', {useGrouping: false});
        } else {
            str = v.toFixed(2);
        }

        let parts = str.split('.');
        let intPart = parts[0];
        let decPart = parts[1];

        intPart = intPart.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ');

        if (decPart) {
            decPart = decPart.replace(/0+$/, '');
            if (decPart === '') return intPart + '$';
            return intPart + '.' + decPart + '$';
        }
        
        return intPart + '$';
    }

    const CASE_PRICES = [];
    let p = 1;
    for (let i = 0; i < 30; i++) {
        CASE_PRICES.push(p);
        p *= 5;
    }

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

    function buildFreeCases() {
        freeCasesGrid.innerHTML = '';
        CASE_PRICES.forEach(price => {
            const btn = document.createElement('button');
            btn.className = 'case-btn';
            btn.textContent = formatMoney(price) + ' кейс';
            btn.addEventListener('click', () => openFreeCase(price));
            freeCasesGrid.appendChild(btn);
        });
    }

    function openCase(price) {
        state.currentCase = { price: price, skins: getSkinsForCase(price) };
        openTitle.textContent = 'Кейс ' + formatMoney(price);
        updateBalanceUI();
        resultMsg.textContent = '';
        state.pendingWin = null;
        buildRoulettePreview(state.currentCase.skins, rouletteStrip);
        buildChances(state.currentCase.skins, chancesList);
        showScreen(openScreen);
        stopSpin();
    }

    function openFreeCase(price) {
        state.currentCase = { price: price, skins: getSkinsForCase(price) };
        freeOpenTitle.textContent = 'Кейс ' + formatMoney(price) + ' (Свободный)';
        freeResultMsg.textContent = '';
        state.pendingWin = null;
        buildRoulettePreview(state.currentCase.skins, freeRouletteStrip);
        buildChances(state.currentCase.skins, freeChancesList);
        showScreen(freeOpenScreen);
        stopSpin();
    }

    function getAkSvg(woodColor = '#d4883d', metalColor = '#5c5c5c') {
        return `<svg class="ak-svg" viewBox="0 0 200 80" xmlns="http://www.w3.org/2000/svg">
            <rect x="120" y="35" width="70" height="6" fill="${metalColor}" stroke="#333" stroke-width="1"/>
            <rect x="120" y="28" width="50" height="7" fill="#3a3a3a" stroke="#222" stroke-width="1"/>
            <rect x="170" y="30" width="20" height="3" fill="#222" stroke="#222" stroke-width="1"/>
            <path d="M 175 35 L 178 25 L 182 25 L 185 35 Z" fill="#3a3a3a" stroke="#222" stroke-width="1"/>
            <rect x="178" y="20" width="4" height="5" fill="#222"/>
            <path d="M 100 30 L 130 30 L 130 52 L 100 52 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="105" y="35" width="20" height="2" fill="#6b3f1b" opacity="0.6"/>
            <rect x="105" y="42" width="20" height="2" fill="#6b3f1b" opacity="0.6"/>
            <path d="M 60 30 L 100 30 L 105 55 L 60 55 Z" fill="${metalColor}" stroke="#222" stroke-width="1.5"/>
            <rect x="65" y="33" width="30" height="4" fill="#444" stroke="#222" stroke-width="1"/>
            <path d="M 70 28 L 85 28 L 80 32 L 65 32 Z" fill="#444" stroke="#222" stroke-width="1"/>
            <path d="M 75 55 L 100 55 L 105 75 L 80 75 Z" fill="${metalColor}" stroke="#222" stroke-width="1.5"/>
            <path d="M 82 58 L 98 58 L 102 72 L 86 72 Z" fill="#3a3a3a" />
            <rect x="84" y="62" width="12" height="2" fill="#555" />
            <rect x="85" y="66" width="10" height="2" fill="#555" />
            <path d="M 60 55 L 70 55 L 65 75 L 55 75 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="57" y="62" width="8" height="2" fill="#6b3f1b" opacity="0.6"/>
            <path d="M 25 35 L 60 32 L 62 52 L 25 55 Z" fill="${woodColor}" stroke="#6b3f1b" stroke-width="1.5"/>
            <rect x="30" y="40" width="15" height="2" fill="#6b3f1b" opacity="0.5"/>
            <rect x="30" y="46" width="15" height="2" fill="#6b3f1b" opacity="0.5"/>
            <path d="M 25 35 L 20 36 L 20 54 L 25 55 Z" fill="#5a2e0c" stroke="#333" stroke-width="1"/>
            <path d="M 75 55 L 85 55 L 85 60 Q 80 65 75 60 Z" fill="#222" />
            <circle cx="80" cy="58" r="2" fill="#222"/>
            <rect x="82" y="55" width="3" height="6" fill="#222"/>
            <rect x="120" y="53" width="10" height="4" fill="#333" />
            <rect x="160" y="42" width="25" height="2" fill="#222" />
        </svg>`;
    }

    function buildRoulettePreview(skins, stripElement) {
        stripElement.innerHTML = '';
        stripElement.style.transform = 'translateX(0)';
        for (let i = 0; i < 30; i++) {
            const sk = skins[Math.floor(Math.random() * skins.length)];
            stripElement.appendChild(makeRouletteItem(sk));
        }
    }

    function makeRouletteItem(skin) {
        const div = document.createElement('div');
        div.className = 'roulette-item';
        const colors = [
            { wood: '#d4883d', metal: '#5c5c5c' },
            { wood: '#4a7a5a', metal: '#4a5a6a' },
            { wood: '#8b3a3a', metal: '#5a3a3a' },
            { wood: '#3a4a8b', metal: '#3a3a5a' },
            { wood: '#d4af37', metal: '#6b5a1b' }
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

    function buildChances(skins, listElement) {
        listElement.innerHTML = '';
        skins.forEach(sk => {
            const el = document.createElement('div');
            el.className = 'chance-item';
            el.textContent = `${formatMoney(sk.price)} — ${sk.chance}%`;
            listElement.appendChild(el);
        });
    }

    let spinAnimId = null;

    function stopSpin() {
        if (spinAnimId) { cancelAnimationFrame(spinAnimId); spinAnimId = null; }
        state.spinning = false;
    }

    function startSpin(isFree, fast) {
        if (state.spinning) return;
        if (!state.currentCase) return;

        if (!isFree && state.balance < state.currentCase.price) {
            resultMsg.textContent = 'Недостаточно средств!';
            return;
        }

        if (!isFree) {
            state.balance = round2(state.balance - state.currentCase.price);
            updateBalanceUI();
            resultMsg.textContent = '';
        } else {
            freeResultMsg.textContent = '';
        }

        const winnerIndex = pickByChance(state.currentCase.skins);
        const winner = state.currentCase.skins[winnerIndex];
        state.pendingWin = winner;

        const totalItems = fast ? 40 : 60;
        const winnerPos = fast ? 30 : 50;
        const stripElement = isFree ? freeRouletteStrip : rouletteStrip;
        
        stripElement.innerHTML = '';
        for (let i = 0; i < totalItems; i++) {
            const sk = (i === winnerPos) ? winner : state.currentCase.skins[Math.floor(Math.random() * state.currentCase.skins.length)];
            stripElement.appendChild(makeRouletteItem(sk));
        }
        stripElement.style.transform = 'translateX(0)';

        state.spinning = true;
        const itemWidth = 128;
        const wrapWidth = stripElement.parentElement.clientWidth;
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
            stripElement.style.transform = `translateX(${x}px)`;

            if (t < 1) {
                spinAnimId = requestAnimationFrame(animate);
            } else {
                state.spinning = false;
                spinAnimId = null;
                state.pendingWin = null;
                
                if (isFree) {
                    freeResultMsg.textContent = `Выпало: ${winner.name} за ${formatMoney(winner.price)} (Свободный режим)`;
                } else {
                    state.balance = round2(state.balance + winner.price);
                    updateBalanceUI();
                    resultMsg.textContent = `Выпало: ${winner.name} за ${formatMoney(winner.price)} — продано!`;
                    syncBalance();
                }
            }
        }
        spinAnimId = requestAnimationFrame(animate);
    }

    openCaseBtn.addEventListener('click', () => startSpin(false, false));
    fastSpinBtn.addEventListener('click', () => startSpin(false, true));
    freeOpenCaseBtn.addEventListener('click', () => startSpin(true, false));
    freeFastSpinBtn.addEventListener('click', () => startSpin(true, true));

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
        const isOpenScreen = openScreen.classList.contains('active') || freeOpenScreen.classList.contains('active');
        if (state.snow && !isOpenScreen) {
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
    fetchBalance();
</script>
</body>
</html>
"""

# --- API ДЛЯ ИГРЫ ---
async def handle(request):
    return web.Response(text=HTML_GAME, content_type='text/html')

async def api_get_balance(request):
    data = await request.json()
    user_id = data.get('user_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    
    if user_id:
        conn = sqlite3.connect('/app/game.db')
        c = conn.cursor()
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute('INSERT INTO users (user_id, username, first_name, balance) VALUES (?, ?, ?, 1.0)', (user_id, username, first_name))
            conn.commit()
            balance = 1.0
        else:
            balance = row[0]
        conn.close()
        return web.json_response({"balance": balance})
    return web.json_response({"balance": 1.0})

async def api_update_balance(request):
    data = await request.json()
    user_id = data.get('user_id')
    username = data.get('username', '')
    first_name = data.get('first_name', '')
    balance = data.get('balance', 1.0)
    
    if user_id:
        update_balance_in_db(user_id, username, first_name, balance)
    return web.json_response({"status": "ok"})

async def api_reset_balance(request):
    data = await request.json()
    user_id = data.get('user_id')
    if user_id:
        reset_user_balance(user_id)
    return web.json_response({"status": "ok"})

async def api_get_top(request):
    top = get_top_players()
    result = []
    for row in top:
        result.append({
            "username": row[0],
            "first_name": row[1],
            "user_id": row[2],
            "balance": row[3]
        })
    return web.json_response(result)

app = web.Application()
app.router.add_get('/', handle)
app.router.add_post('/api/get_balance', api_get_balance)
app.router.add_post('/api/update_balance', api_update_balance)
app.router.add_post('/api/reset_balance', api_reset_balance)
app.router.add_get('/api/get_top', api_get_top)

async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Веб-сервер запущен на порту 8080")
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
