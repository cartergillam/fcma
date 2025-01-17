document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const email = document.querySelector('input[name="email"]');
    const password = document.querySelector('input[name="password"]');

    form.addEventListener('submit', (event) => {
        if (!email.value.trim() || !password.value.trim()) {
            event.preventDefault();
            alert("Both email and password are required.");
        }
    });
});
