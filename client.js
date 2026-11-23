const signInBtn = document.getElementById('signin');
const dropdown = document.getElementById('signin-dropdown');

// Toggle dropdown when clicking the Sign In button
signInBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('show');
});

// Close dropdown if user clicks anywhere outside of it
window.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
    }
});