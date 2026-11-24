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
const playerCountDisplay = document.getElementById('player-count-display');
const shoeInfo = document.getElementById('shoe-info');
const statusBanner = document.getElementById('game-status-banner');
const leaveRoomBtn = document.getElementById('leave-room-btn');

const betControls = document.getElementById('bet-controls');
const actionControls = document.getElementById('action-controls');
const betInput = document.getElementById('bet-input');
const betBtn = document.getElementById('bet-btn');
const twistBtn = document.getElementById('twist-btn');
const stickBtn = document.getElementById('stick-btn');

let isSignUpMode = false;
let isLoggedIn = false;
let currentUsername = null;
let currentBalance = null;
let currentGameCode = null;
let pollInterval = null;
let lastObservedGamePhase = null;
let actionLocked = false;
let betButtonDisabled = false;
let betInputDisabled = false;
let twistButtonDisabled = false;
let stickButtonDisabled = false;
let accountApprovalRequired = false;
const adminConsoleBtn = document.getElementById('admin-console-btn');
const adminConsole = document.getElementById('admin-console');
const adminConsoleClose = document.getElementById('admin-console-close');
const adminTableBody = document.getElementById('admin-table-body');
const adminSignupsState = document.getElementById('admin-signups-state');
const adminSignupsToggle = document.getElementById('admin-signups-toggle');
const adminApprovalState = document.getElementById('admin-approval-state');
const adminApprovalToggle = document.getElementById('admin-approval-toggle');
const playerStatsPanel = document.getElementById('player-stats-panel');
const playerStatFields = {
    hands: document.getElementById('stat-hands'),
    wins: document.getElementById('stat-wins'),
    losses: document.getElementById('stat-losses'),
    pushes: document.getElementById('stat-pushes'),
    blackjacks: document.getElementById('stat-blackjacks'),
    busts: document.getElementById('stat-busts'),
    wagered: document.getElementById('stat-wagered'),
    net: document.getElementById('stat-net')
};

// Semicircle seat coordinates based on exact number of active players (no empty seats shown)
const SEAT_LAYOUTS = {
    1: [
        { top: '68%', left: '50%' }
    ],
    2: [
        { top: '64%', left: '34%' },
        { top: '64%', left: '66%' }
    ],
    3: [
        { top: '56%', left: '22%' },
        { top: '70%', left: '50%' },
        { top: '56%', left: '78%' }
    ],
    4: [
        { top: '44%', left: '16%' },
        { top: '66%', left: '36%' },
        { top: '66%', left: '64%' },
        { top: '44%', left: '84%' }
    ],
    5: [
        { top: '38%', left: '14%' },
        { top: '63%', left: '26%' },
        { top: '71%', left: '50%' },
        { top: '63%', left: '74%' },
        { top: '38%', left: '86%' }
    ]
};

// --- DROPDOWN TOGGLES ---
signInBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    startDropdown.classList.remove('show');
    if (isLoggedIn) {
        if (currentGameCode) await leaveCurrentRoom();
        await fetch('/api/logout', { method: 'POST' });
        setLoggedOutUI();
        return;
    }
    dropdown.classList.toggle('show');
});

startBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.remove('show');
    adminConsole.style.display = 'none';
    startDropdown.classList.toggle('show');
});

window.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) dropdown.classList.remove('show');
    if (!startDropdown.contains(e.target)) startDropdown.classList.remove('show');
});

// --- AUTHENTICATION ---
toggleModeBtn.addEventListener('click', () => {
    setSignUpMode(!isSignUpMode);
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
    if (data.pending_approval) {
        alert(data.message);
        loginForm.reset();
        setSignUpMode(false);
        dropdown.classList.remove('show');
        return;
    }
    if (data.success) {
        setLoggedInUI(data.username, data.balance, data.is_admin);
        adminConsoleBtn.style.display = data.is_admin ? 'inline-block' : 'none';
        startBtn.disabled = data.is_admin;
        dropdown.classList.remove('show');
        startDropdown.classList.remove('show');
        loginForm.reset();
        setSignUpMode(false);
        loadLeaderboard();
        if (data.is_admin) {
            playerStatsPanel.hidden = true;
            adminConsole.style.display = 'block';
            await loadAdminAccounts();
        } else {
            playerStatsPanel.hidden = false;
            await loadPlayerStats();
        }
    } else {
        alert(data.error);
    }
});

function setSignUpMode(enabled) {
    isSignUpMode = enabled;
    toggleModeBtn.textContent = enabled ? 'Have an Account? Log In!' : 'No Account? Sign Up!';
    submitBtn.textContent = enabled ? 'Sign Up' : 'Log In';
    const passwordInput = document.getElementById('password');
    passwordInput.minLength = enabled ? 8 : 0;
    passwordInput.autocomplete = enabled ? 'new-password' : 'current-password';
}

function setLoggedInUI(username, balance, isAdmin = false) {
    isLoggedIn = true;
    currentUsername = username;
    signInBtn.textContent = `${username} (Log Out)`;
    updateBalance(balance);
    startBtn.disabled = isAdmin;
}

function updateBalance(balance) {
    if (typeof balance !== 'number') return;
    currentBalance = balance;
    balanceSpan.textContent = `balance: £${balance}`;
    betInput.max = String(Math.max(1, balance));
    if (balance === 0) {
        betInput.value = '1';
    } else if (parseInt(betInput.value, 10) > balance) {
        betInput.value = String(balance);
    }
    if (!betButtonDisabled) {
        betBtn.textContent = balance === 0 ? '£1 Safety Bet' : 'Place Bet';
    }
}

function setLoggedOutUI() {
    setSignUpMode(false);
    isLoggedIn = false;
    currentUsername = null;
    currentBalance = null;
    signInBtn.textContent = 'Sign In';
    balanceSpan.textContent = 'balance: £---';
    betInput.removeAttribute('max');
    betInput.value = '10';
    betBtn.textContent = 'Place Bet';
    startBtn.disabled = false;
    adminConsoleBtn.style.display = 'none';
    adminConsole.style.display = 'none';
    playerStatsPanel.hidden = true;
}

// --- ROOM & GAME STATE RENDERING ---
function openGameRoom(code, state) {
    currentGameCode = code;
    lastObservedGamePhase = null;
    roomCodeDisplay.textContent = code;
    startDropdown.classList.remove('show');

    homeView.style.display = 'none';
    gameView.style.display = 'block';

    renderGameState(state);

    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollRoomState, 1200);
}

async function leaveCurrentRoom() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    if (currentGameCode) {
        await fetch('/api/game/leave', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: currentGameCode })
        });
    }
    currentGameCode = null;
    roomCodeDisplay.textContent = '-----';
    gameView.style.display = 'none';
    homeView.style.display = 'block';
    loadLeaderboard();
}

async function pollRoomState() {
    if (!currentGameCode) return;
    const res = await fetch(`/api/game/state?code=${currentGameCode}`);
    const data = await res.json();
    if (data.success) {
        if (typeof data.balance === 'number') {
            updateBalance(data.balance);
        }
        renderGameState(data.state);
    } else {
        leaveCurrentRoom();
    }
}

function renderCards(containerId, cardCodes) {
    const container = document.getElementById(containerId);
    const previousCards = container.dataset.cards
        ? container.dataset.cards.split('|')
        : [];
    const sameHand = previousCards.length === cardCodes.length
        && previousCards.every((code, index) => code === cardCodes[index]);

    container.innerHTML = '';
    cardCodes.forEach((code, index) => {
        const img = document.createElement('img');
        img.className = 'hand-card';
        img.src = `assets/cards/IndividualCards/${code}.png`;
        img.alt = code;
        if (!sameHand && (index >= previousCards.length || previousCards[index] !== code)) {
            img.classList.add('card-enter');
            img.style.animationDelay = `${index * 70}ms`;
        }
        container.appendChild(img);
    });
    container.dataset.cards = cardCodes.join('|');
}

function renderGameState(state) {
    const roundJustFinished = state.phase === 'round_over' && lastObservedGamePhase !== 'round_over';
    lastObservedGamePhase = state.phase;
    const players = state.players;
    const count = players.length;

    playerCountDisplay.textContent = `(${count}/5 Max)`;
    shoeInfo.textContent = state.reshuffled
        ? `NEW 6-DECK SHOE SHUFFLED (${state.cards_remaining} cards)`
        : `6-Deck Shoe: ${state.cards_remaining} cards left`;
    statusBanner.textContent = state.message;

    // Dealer
    document.getElementById('dealer-label').textContent = `Dealer ${state.dealer.total}`.trim();
    renderCards('dealer-cards', state.dealer.hand);

    // Position only active players smoothly across the semicircle
    const layout = SEAT_LAYOUTS[count] || SEAT_LAYOUTS[5];

    for (let i = 0; i < 5; i++) {
        const seatEl = document.getElementById(`seat-${i}`);
        if (i < count) {
            const p = players[i];
            seatEl.style.display = 'flex';
            seatEl.style.top = layout[i].top;
            seatEl.style.left = layout[i].left;
            seatEl.classList.toggle('active-turn', p.is_turn);

            const totalText = p.total ? ` (${p.total})` : '';
            document.getElementById(`seat-${i}-name`).textContent = `${p.username}${totalText}`;
            renderCards(`seat-${i}-cards`, p.hand);

            const infoEl = document.getElementById(`seat-${i}-info`);
            if (p.result) {
                infoEl.textContent = p.result;
            } else if (p.bet > 0) {
                infoEl.textContent = `Bet: £${p.bet}`;
            } else {
                infoEl.textContent = 'Waiting for bet...';
            }
        } else {
            seatEl.style.display = 'none';
            seatEl.classList.remove('active-turn');
            document.getElementById(`seat-${i}-cards`).innerHTML = '';
        }
    }

    // Update bottom controls for current user
    const me = players.find((p) => p.username === currentUsername);
    if (!me) return;

    if (state.phase === 'betting' || state.phase === 'round_over') {
        betControls.style.display = 'flex';
        actionControls.style.display = 'none';
        const alreadyBet = (state.phase === 'betting' && me.status === 'bet_placed');
        betButtonDisabled = alreadyBet;
        betInputDisabled = alreadyBet;
        betBtn.textContent = alreadyBet
            ? 'Bet Placed'
            : currentBalance === 0 ? '£1 Safety Bet' : 'Place Bet';
    } else if (state.phase === 'playing') {
        betControls.style.display = 'none';
        actionControls.style.display = 'flex';
        twistButtonDisabled = !me.is_turn;
        stickButtonDisabled = !me.is_turn;
    }
    applyActionLockState();
    if (roundJustFinished && isLoggedIn && !startBtn.disabled) {
        loadPlayerStats();
    }
}

function applyActionLockState() {
    betBtn.disabled = actionLocked || betButtonDisabled;
    betInput.disabled = betInputDisabled;
    twistBtn.disabled = actionLocked || twistButtonDisabled;
    stickBtn.disabled = actionLocked || stickButtonDisabled;
}

function lockActionsBriefly() {
    if (actionLocked) return false;
    actionLocked = true;
    applyActionLockState();
    window.setTimeout(() => {
        actionLocked = false;
        applyActionLockState();
    }, 300);
    return true;
}

// --- ACTION BUTTON HANDLERS ---
createGameBtn.addEventListener('click', async () => {
    const res = await fetch('/api/game/create', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
        openGameRoom(data.code, data.state);
    } else {
        alert(data.error);
    }
});

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
        openGameRoom(data.code, data.state);
    } else {
        alert(data.error);
    }
});

betBtn.addEventListener('click', async () => {
    if (!currentGameCode) return;
    if (!lockActionsBriefly()) return;
    const amount = parseInt(betInput.value, 10);
    const res = await fetch('/api/game/bet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentGameCode, amount })
    });
    const data = await res.json();
    if (data.success) {
        updateBalance(data.balance);
        renderGameState(data.state);
    } else {
        alert(data.error);
    }
});

twistBtn.addEventListener('click', async () => {
    if (!currentGameCode) return;
    if (!lockActionsBriefly()) return;
    const res = await fetch('/api/game/twist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentGameCode })
    });
    const data = await res.json();
    if (data.success) {
        updateBalance(data.balance);
        renderGameState(data.state);
    } else {
        alert(data.error);
    }
});

stickBtn.addEventListener('click', async () => {
    if (!currentGameCode) return;
    if (!lockActionsBriefly()) return;
    const res = await fetch('/api/game/stick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: currentGameCode })
    });
    const data = await res.json();
    if (data.success) {
        updateBalance(data.balance);
        renderGameState(data.state);
    } else {
        alert(data.error);
    }
});

leaveRoomBtn.addEventListener('click', leaveCurrentRoom);

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
        const rankCell = document.createElement('td');
        rankCell.textContent = String(index + 1);
        const usernameCell = document.createElement('td');
        usernameCell.textContent = player.username;
        const moneyCell = document.createElement('td');
        moneyCell.textContent = `£${player.money}`;
        row.append(rankCell, usernameCell, moneyCell);
        tbody.appendChild(row);
    });
}

async function loadPlayerStats() {
    if (!isLoggedIn || !currentUsername || startBtn.disabled) {
        playerStatsPanel.hidden = true;
        return;
    }
    const requestedUsername = currentUsername;
    const res = await fetch('/api/me/stats');
    const data = await res.json();
    if (!isLoggedIn || currentUsername !== requestedUsername || startBtn.disabled) return;
    if (!data.success) {
        playerStatsPanel.hidden = true;
        return;
    }

    const stats = data.stats;
    playerStatFields.hands.textContent = String(stats.hands_played);
    playerStatFields.wins.textContent = String(stats.wins);
    playerStatFields.losses.textContent = String(stats.losses);
    playerStatFields.pushes.textContent = String(stats.pushes);
    playerStatFields.blackjacks.textContent = String(stats.blackjacks);
    playerStatFields.busts.textContent = String(stats.busts);
    playerStatFields.wagered.textContent = `£${stats.total_wagered}`;
    playerStatFields.net.textContent = stats.net_profit > 0
        ? `+£${stats.net_profit}`
        : stats.net_profit < 0 ? `-£${Math.abs(stats.net_profit)}` : '£0';
    playerStatsPanel.hidden = false;
}

async function loadAdminAccounts() {
    const res = await fetch('/api/admin/accounts');
    const data = await res.json();
    if (!data.success) {
        alert(data.error);
        return;
    }

    adminSignupsState.textContent =
        `Public signups are ${data.signups_enabled ? 'enabled' : 'disabled'}.`;
    adminSignupsToggle.textContent = data.signups_enabled ? 'Disable Signups' : 'Enable Signups';
    accountApprovalRequired = data.account_approval_required;
    adminApprovalState.textContent = accountApprovalRequired
        ? 'New accounts require your approval before they can sign in.'
        : 'New accounts can sign in as soon as they register.';
    adminApprovalToggle.textContent = accountApprovalRequired
        ? 'Stop Requiring Approval'
        : 'Require Approval';
    adminTableBody.innerHTML = '';

    data.accounts.forEach((account) => {
        const row = document.createElement('tr');
        const usernameCell = document.createElement('td');
        usernameCell.textContent = account.username;
        const moneyCell = document.createElement('td');
        moneyCell.textContent = `£${account.money}`;
        const adminCell = document.createElement('td');
        adminCell.textContent = account.is_admin ? 'Yes' : 'No';
        const approvalCell = document.createElement('td');
        approvalCell.textContent = account.is_admin
            ? 'Not required'
            : account.approved ? 'Approved' : 'Pending';
        const actionsCell = document.createElement('td');
        const actionRow = document.createElement('div');
        actionRow.className = 'admin-action-row';
        let approveButton = null;
        if (!account.approved && !account.is_admin) {
            approveButton = document.createElement('button');
            approveButton.type = 'button';
            approveButton.className = 'button small-btn admin-approve-account';
            approveButton.textContent = 'Approve';
            actionRow.append(approveButton);
        }
        const moneyInput = document.createElement('input');
        moneyInput.type = 'number';
        moneyInput.className = 'txtIn admin-money-input';
        moneyInput.min = '0';
        moneyInput.value = String(account.money);
        moneyInput.setAttribute('aria-label', `Balance for ${account.username}`);
        const saveButton = document.createElement('button');
        saveButton.type = 'button';
        saveButton.className = 'button small-btn admin-save-money';
        saveButton.textContent = 'Save';
        actionRow.append(moneyInput, saveButton);
        let deleteButton = null;
        if (!account.is_admin) {
            deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'button small-btn admin-delete-account';
            deleteButton.textContent = 'Delete';
            actionRow.append(deleteButton);
        }
        actionsCell.append(actionRow);
        row.append(usernameCell, moneyCell, adminCell, approvalCell, actionsCell);

        const saveMoneyButton = saveButton;
        const moneyInputElement = moneyInput;

        if (approveButton) {
            approveButton.addEventListener('click', async () => {
                const response = await fetch(
                    `/api/admin/accounts/${encodeURIComponent(account.username)}/approve`,
                    { method: 'POST' }
                );
                const result = await response.json();
                if (result.success) {
                    await loadAdminAccounts();
                    await loadLeaderboard();
                } else {
                    alert(result.error);
                }
            });
        }

        saveMoneyButton.addEventListener('click', async () => {
            const amount = parseInt(moneyInputElement.value, 10);
            const response = await fetch('/api/admin/accounts/money', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: account.username, amount })
            });
            const result = await response.json();
            if (result.success) {
                await loadAdminAccounts();
                loadLeaderboard();
            } else {
                alert(result.error);
            }
        });

        if (deleteButton) {
            deleteButton.addEventListener('click', async () => {
                if (!confirm(`Delete account "${account.username}"?`)) return;
                const response = await fetch(`/api/admin/accounts/${encodeURIComponent(account.username)}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                if (result.success) {
                    await loadAdminAccounts();
                    loadLeaderboard();
                } else {
                    alert(result.error);
                }
            });
        }

        adminTableBody.appendChild(row);
    });
}

adminConsoleBtn.addEventListener('click', async () => {
    adminConsole.style.display = 'block';
    await loadAdminAccounts();
});

adminConsoleClose.addEventListener('click', () => {
    adminConsole.style.display = 'none';
});

adminSignupsToggle.addEventListener('click', async () => {
    adminSignupsToggle.disabled = true;
    try {
        const currentlyEnabled = adminSignupsToggle.textContent === 'Disable Signups';
        const response = await fetch('/api/admin/settings/signups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !currentlyEnabled })
        });
        const result = await response.json();
        if (!result.success) {
            alert(result.error);
            return;
        }
        await loadAdminAccounts();
    } finally {
        adminSignupsToggle.disabled = false;
    }
});

adminApprovalToggle.addEventListener('click', async () => {
    adminApprovalToggle.disabled = true;
    try {
        const response = await fetch('/api/admin/settings/account-approval', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !accountApprovalRequired })
        });
        const result = await response.json();
        if (!result.success) {
            alert(result.error);
            return;
        }
        await loadAdminAccounts();
    } finally {
        adminApprovalToggle.disabled = false;
    }
});

async function init() {
    const res = await fetch('/api/me');
    const data = await res.json();
    if (data.logged_in) {
        setLoggedInUI(data.username, data.balance, data.is_admin);
        adminConsoleBtn.style.display = data.is_admin ? 'inline-block' : 'none';
        if (data.is_admin) {
            playerStatsPanel.hidden = true;
            adminConsole.style.display = 'block';
            await loadAdminAccounts();
        } else {
            adminConsole.style.display = 'none';
            playerStatsPanel.hidden = false;
            await loadPlayerStats();
        }
    } else {
        playerStatsPanel.hidden = true;
    }
    loadLeaderboard();
}

init();