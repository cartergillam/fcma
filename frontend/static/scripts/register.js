document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector('form');
    const password = document.querySelector('input[name="password"]');
    const confirmPassword = document.querySelector('input[name="confirm_password"]');
    const email = document.querySelector('input[name="email"]');

    form.addEventListener('submit', (event) => {
        // Password matching validation
        if (password.value !== confirmPassword.value) {
            event.preventDefault();
            alert("Passwords do not match!");
            return;
        }

        // Email format validation (basic regex check)
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email.value)) {
            event.preventDefault();
            alert("Please enter a valid email address.");
            return;
        }
    });

    const addChildButton = document.getElementById('add-child');
    const childrenContainer = document.getElementById('children-container');

    addChildButton.addEventListener('click', () => {
        const childEntry = document.createElement('div');
        childEntry.classList.add('child-entry');
        childEntry.innerHTML = `
            <input type="text" name="children_first_name[]" placeholder="Child's First Name (optional)">
            <input type="text" name="children_last_name[]" placeholder="Child's Last Name (optional)">
            <button type="button" class="delete-child">×</button>
        `;
        childrenContainer.appendChild(childEntry);

        // Add event listener to the delete button
        childEntry.querySelector('.delete-child').addEventListener('click', () => {
            childEntry.remove();
        });
    });
});
