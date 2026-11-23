const signInBtn = document.getElementById('signin');
const dropdown = document.getElementById('signin-dropdown');
const loginForm = document.getElementById('login-form');
const toggleModeBtn = document.getElementById('signup');
const submitBtn = document.getElementById('login2');
const balanceSpan = document.getElementById('balance');

let isSignUpMode = false;
let isLoggedIn = false;

// 1. Toggle dropdown or log out if already signed in
signInBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    if (isLoggedIn) {
        await fetch('/api/logout', { method: 'POST' });
        setLoggedOutUI();
        return;
    }
    dropdown.classList.toggle('show');
});

window.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});

// 2. Switch between Log In and Sign Up inside the dropdown
toggleModeBtn.addEventListener('click', () => {
    isSignUpMode = !isSignUpMode;
    toggleModeBtn.textContent = isSignUpMode ? 'Have an Account? Log In!' : 'No Account? Sign Up!';
    submitBtn.textContent = isSignUpMode ? 'Sign Up' : 'Log In';
});

// 3. Submit Login or Signup to Python
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
        loadLeaderboard(); // Refresh leaderboard in case a new user was added
    } else {
        alert(data.error);
    }
});

function setLoggedInUI(username, balance) {
    isLoggedIn = true;
    signInBtn.textContent = `${username} (Log Out)`;
    balanceSpan.textContent = `balance: £${balance}`;
}

function setLoggedOutUI() {
    isLoggedIn = false;
    signInBtn.textContent = 'Sign In';
    balanceSpan.textContent = 'balance: £---';
}

// 4. Populate Leaderboard Table
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

// 5. Run on page load: restore session & fetch leaderboard
async function init() {
    const res = await fetch('/api/me');
    const data = await res.json();
    if (data.logged_in) {
        setLoggedInUI(data.username, data.balance);
    }
    loadLeaderboard();
}

init();