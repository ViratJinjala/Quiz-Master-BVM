const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const switches = document.querySelectorAll('.form-switch');
switches.forEach(switchEl => {
    switchEl.addEventListener('click', () => {
        loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
        registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
    });
});