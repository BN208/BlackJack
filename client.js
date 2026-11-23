const signInBtn = document.getElementById('signin');
const dropdown = document.getElementById('signin-dropdown');
const loginForm = document.getElementById('login-form');
const toggleModeBtn = document.getElementById('signup');
const submitBtn = document.getElementById('login2');
const balanceSpan = document.getElementById('balance');

const startBtn = document.getElementById('startBtn');
const startDropdown = document.getElementById('start-dropdown');
const createGameBtn = document.getElementById('create-game-btn');
const joinForm = document.getElementById('join-form');

const homeView = document.getElementById('home-view');
const gameView = document.getElementById('game-view');
const roomCodeDisplay = document.getElementById('room-code-display');
const leaveRoomBtn = document.getElementById('leave-room-btn');

let isSignUpMode = false;
let isLoggedIn = false;
let currentUsername = null;
let currentGameCode = null;

// --- DROPDOWN TOGGLES ---
signInBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    startDropdown.classList.remove('show');
    if (isLoggedIn) {
        await fetch('/api/logout', { method: 'POST' });
        setLoggedOutUI();
        return;
    }
    dropdown.classList.toggle('show');
});

startBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.remove('show');
    startDropdown.classList.toggle('show');
});

window.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
    }
    if (!startDropdown.contains(e.target)) {
        startDropdown.classList.remove('show');
    }
});

// --- AUTHENTICATION ---
toggleModeBtn.addEventListener('click', () => {
    isSignUpMode = !isSignUpMode;
    toggleModeBtn.textContent = isSignUpMode ? 'Have an Account? Log In!' : 'No Account? Sign Up!';
    submitBtn.textContent = isSignUpMode ? 'Sign Up' : 'Log In';
});

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const endpoint = isSignUpMode ? '/api/signup' : '/api/login';

    const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (data.success) {
        setLoggedInUI(data.username, data.balance);
        dropdown.classList.remove('show');
        loginForm.reset();
        loadLeaderboard();
    } else {
        alert(data.error);
    }
});

function setLoggedInUI(username, balance) {
    isLoggedIn = true;
    currentUsername = username;
    signInBtn.textContent = `${username} (Log Out)`;
    balanceSpan.textContent = `balance: £${balance}`;
}

function setLoggedOutUI() {
    isLoggedIn = false;
    currentUsername = null;
    signInBtn.textContent = 'Sign In';
    balanceSpan.textContent = 'balance: £---';
}

// --- VIEW SWITCHING & ROOM SETUP ---
function openGameRoom(code, players = []) {
    currentGameCode = code;
    roomCodeDisplay.textContent = code;
    startDropdown.classList.remove('show');

    homeView.style.display = 'none';
    gameView.style.display = 'block';

    updateSeatsUI(players);
}

function closeGameRoom() {
    currentGameCode = null;
    roomCodeDisplay.textContent = '-----';

    gameView.style.display = 'none';
    homeView.style.display = 'block';
    loadLeaderboard();
}

function updateSeatsUI(players) {
    for (let i = 1; i <= 5; i++) {
        const nameEl = document.getElementById(`seat-${i}-name`);
        const cardsEl = document.getElementById(`seat-${i}-cards`);
        const player = players[i - 1];

        if (player) {
            nameEl.textContent = player;
        } else {
            nameEl.textContent = 'Empty Seat';
            cardsEl.innerHTML = '';
        }
    }
}

// Renders an array of card codes (e.g., ["AS", "KH"]) into any seat's card container
function renderCards(containerId, cardCodes) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    cardCodes.forEach((code) => {
        const img = document.createElement('img');
        img.className = 'hand-card';
        img.src = `assets/cards/IndividualCards/${code}.png`;
        img.alt = code;
        container.appendChild(img);
    });
}

// Create New Game
createGameBtn.addEventListener('click', async () => {
    const res = await fetch('/api/game/create', { method: 'POST' });
    const data = await res.json();

    if (data.success) {
        openGameRoom(data.code, [currentUsername]);
    } else {
        alert(data.error);
    }
});

// Join Existing Game
joinForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = document.getElementById('game-code-input').value.trim().toUpperCase();

    const res = await fetch('/api/game/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
    });

    const data = await res.json();
    if (data.success) {
        joinForm.reset();
        openGameRoom(data.code, data.players);
    } else {
        alert(data.error);
    }
});

// Leave Room Button
leaveRoomBtn.addEventListener('click', async () => {
    if (currentGameCode) {
        await fetch('/api/game/leave', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: currentGameCode })
        });
    }
    closeGameRoom();
});

// Auto-leave on tab close
window.addEventListener('beforeunload', () => {
    if (currentGameCode) {
        const blob = new Blob([JSON.stringify({ code: currentGameCode })], { type: 'application/json' });
        navigator.sendBeacon('/api/game/leave', blob);
    }
});

// --- LEADERBOARD & INIT ---
async function loadLeaderboard() {
    const res = await fetch('/api/leaderboard');
    const players = await res.json();
    const tbody = document.getElementById('lb-body');
    tbody.innerHTML = '';

    players.forEach((player, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${player.username}</td>
            <td>£${player.money}</td>
        `;
        tbody.appendChild(row);
    });
}

async function init() {
    const res = await fetch('/api/me');
    const data = await res.json();
    if (data.logged_in) {
        setLoggedInUI(data.username, data.balance);
    }
    loadLeaderboard();
}

init();