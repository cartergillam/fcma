from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient, errors
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from jwt_utils import create_token, verify_token
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Secure configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# Extensions
mongo = PyMongo(app)
jwt = JWTManager(app)

# MongoDB connection
client = MongoClient(app.config["MONGO_URI"])
db = client['fcma']
users_collection = db['users']
classes_collection = db['classes']
bookings_collection = db['bookings']

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        children_first_names = request.form.getlist('children_first_name[]')
        children_last_names = request.form.getlist('children_last_name[]')

        # Validation
        if not first_name or not last_name or not email or not phone or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        try:
            print("Attempting to find user by email...")
            user = users_collection.find_one({"email": email})
            if user:
                flash("Email already exists.", "error")
                return redirect(url_for('register'))
        except errors.OperationFailure as e:
            print(f"Error during find_one operation: {e}")
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('register'))

        # Combine children first and last names into a list of dictionaries
        children = [{"first_name": fn, "last_name": ln} for fn, ln in zip(children_first_names, children_last_names) if fn or ln]

        # Hash the password and save the user
        hashed_password = generate_password_hash(password)
        user = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'password': hashed_password,
            'children': children,
            'is_admin': False  # Default to non-admin
        }

        try:
            print("Attempting to insert new user...")
            users_collection.insert_one(user)
        except errors.OperationFailure as e:
            print(f"Error during insert_one operation: {e}")
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('register'))

        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find the user
        try:
            print("Attempting to find user by email...")
            user = users_collection.find_one({"email": email})
            if not user:
                flash("Invalid email or password.", "error")
                return redirect(url_for('login'))
        except errors.OperationFailure as e:
            print(f"Error during find_one operation: {e}")
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('login'))

        if check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['is_admin'] = user.get('is_admin', False)
            token = create_token(session['user_id'], session['is_admin'])
            session['token'] = token
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/admin-dashboard')
def admin_dashboard():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    users = users_collection.find()
    return render_template('admin-dashboard.html', users=users)

@app.route('/schedule-class', methods=['GET', 'POST'])
def schedule_class():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        class_name = request.form['class_name']
        class_date = request.form['class_date']
        class_start_time = request.form['class_start_time']
        class_end_time = request.form['class_end_time']

        # Validation
        if not class_name or not class_date or not class_start_time or not class_end_time:
            flash("All fields are required.", "error")
            return redirect(url_for('schedule_class'))

        class_info = {
            'class_name': class_name,
            'class_date': class_date,
            'class_start_time': class_start_time,
            'class_end_time': class_end_time
        }

        try:
            print("Attempting to insert new class...")
            classes_collection.insert_one(class_info)
        except errors.OperationFailure as e:
            print(f"Error during insert_one operation: {e}")
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('schedule_class'))

        flash("Class scheduled successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('schedule-class.html')

@app.route('/create-weekly-schedule', methods=['GET', 'POST'])
def create_weekly_schedule():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))
    app.run(debug=True)

    if request.method == 'POST':
        classes = request.form.getlist('classes')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')

        for i in range(7):  # Create schedule for 7 days
            for class_info in classes:
                class_name, class_time = class_info.split(',')
                class_date = start_date + timedelta(days=i)
                class_entry = {
                    'class_name': class_name,
                    'class_date': class_date.strftime('%Y-%m-%d'),
                    'class_time': class_time
                }
                try:
                    classes_collection.insert_one(class_entry)
                except errors.OperationFailure as e:
                    print(f"Error during insert_one operation: {e}")
                    flash("An error occurred. Please try again later.", "error")
                    return redirect(url_for('create_weekly_schedule'))

        flash("Weekly schedule created successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('create-weekly-schedule.html')

@app.route('/admin-calendar')
def admin_calendar():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    # Fetch classes and organize them by date
    classes = classes_collection.find()
    calendar = {}
    for class_info in classes:
        class_date = class_info['class_date']
        if class_date not in calendar:
            calendar[class_date] = []
        calendar[class_date].append(class_info)

    # Convert calendar to a list of days with classes
    calendar_list = [{'date': date, 'classes': classes} for date, classes in calendar.items()]
    calendar_list.sort(key=lambda x: x['date'])

    return render_template('admin-calendar.html', calendar=calendar_list)

@app.route('/renew-schedule', methods=['GET', 'POST'])
def renew_schedule():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    if request.method == 'POST':
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        current_date = datetime.now()

        while current_date <= end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            week_classes = classes_collection.find({'class_date': {'$gte': week_start.strftime('%Y-%m-%d'), '$lte': week_end.strftime('%Y-%m-%d')}})

            for class_info in week_classes:
                new_class_date = datetime.strptime(class_info['class_date'], '%Y-%m-%d') + timedelta(weeks=1)
                if new_class_date <= end_date:
                    new_class_info = class_info.copy()
                    new_class_info['class_date'] = new_class_date.strftime('%Y-%m-%d')
                    classes_collection.insert_one(new_class_info)

            current_date += timedelta(weeks=1)

        flash("Schedule renewed successfully!", "success")
        return redirect(url_for('admin_calendar'))

    return render_template('renew-schedule.html')

@app.route('/edit-class/<class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    class_info = classes_collection.find_one({'_id': ObjectId(class_id)})

    if request.method == 'POST':
        class_name = request.form['class_name']
        class_date = request.form['class_date']
        class_start_time = request.form['class_start_time']
        class_end_time = request.form['class_end_time']

        # Validation
        if not class_name or not class_date or not class_start_time or not class_end_time:
            flash("All fields are required.", "error")
            return redirect(url_for('edit_class', class_id=class_id))

        updated_class_info = {
            'class_name': class_name,
            'class_date': class_date,
            'class_start_time': class_start_time,
            'class_end_time': class_end_time
        }

        try:
            classes_collection.update_one({'_id': ObjectId(class_id)}, {'$set': updated_class_info})
            flash("Class updated successfully!", "success")
            return redirect(url_for('admin_calendar'))
        except errors.OperationFailure as e:
            print(f"Error during update_one operation: {e}")
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('edit_class', class_id=class_id))

    return render_template('edit-class.html', class_info=class_info)

@app.route('/remove-class/<class_id>', methods=['POST'])
def remove_class(class_id):
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('home'))

    try:
        classes_collection.delete_one({'_id': ObjectId(class_id)})
        flash("Class removed successfully!", "success")
    except errors.OperationFailure as e:
        print(f"Error during delete_one operation: {e}")
        flash("An error occurred. Please try again later.", "error")

    return redirect(url_for('admin_calendar'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

