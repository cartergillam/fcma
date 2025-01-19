# FCMA - Class Management System

A custom class booking and management system for a local karate school.
This project is in early alpha and provides basic functionality for both administrators (to manage classes) and students (to view/book classes).  
**Features include:**

**Admin Dashboard**
  - Create, edit, and delete classes
  - Set maximum class capacity and track attendance
  - Manage user profiles (e.g., add/remove students)
    
**Student Dashboard**
  - Register and log in
  - View available classes
  - Book classes (if spots are open) and see booking history
    
**Real-Time Availability**
  - Displays remaining spots in each class
  - Automatically updates when classes fill up
    
**Secure Authentication**

  - Uses JSON Web Tokens (JWT) for user sessions
  - Passwords hashed using modern security standards
    
**Tech Stack:**
- Backend: Python (Flask)
- Database: MongoDB
- Frontend: HTML/CSS/JavaScript
- Authentication: Flask-JWT-Extended

All sensitive data has been secured using environment variables.
