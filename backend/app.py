from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from jwt_utils import create_token, verify_token
from datetime import datetime, timedelta
from bson import ObjectId

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find the user
        try:
            user = users_collection.find_one({"email": email})
            if not user:
                flash("Invalid email or password.", "error")
                return redirect(url_for('login'))
        except errors.OperationFailure as e:
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('login'))

        if check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['is_admin'] = user.get('is_admin', False)
            token = create_token(session['user_id'], session['is_admin'])
            session['token'] = token
            flash("Login successful!", "success")
            if user.get('is_admin', False):
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

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
            user = users_collection.find_one({"email": email})
            if user:
                flash("Email already exists.", "error")
                return redirect(url_for('register'))
        except errors.OperationFailure as e:
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('register'))

        # Combine children first and last names into a list of dictionaries with unique IDs
        children = [{"_id": ObjectId(), "first_name": fn, "last_name": ln} for fn, ln in zip(children_first_names, children_last_names) if fn or ln]

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
            users_collection.insert_one(user)
        except errors.OperationFailure as e:
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('register'))

        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

def format_time_12hr(time_24hr):
    time_obj = datetime.strptime(time_24hr, "%H:%M")
    return time_obj.strftime("%I:%M %p")

@app.route('/admin-dashboard')
def admin_dashboard():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

    users = users_collection.find({'is_admin': False}).sort([("first_name", 1), ("last_name", 1)])
    today_date = datetime.now().strftime('%Y-%m-%d')
    today_classes = classes_collection.find({'class_date': today_date})

    formatted_classes = []
    for class_info in today_classes:
        formatted_classes.append({
            'class_name': class_info['class_name'],
            'class_date': class_info['class_date'],
            'class_start_time': format_time_12hr(class_info['class_start_time']),
            'class_end_time': format_time_12hr(class_info['class_end_time']),
            'max_students': class_info['max_students'],
            'current_students': len(class_info['students'])
        })

    return render_template('admin-dashboard.html', users=users, today_classes=formatted_classes)

@app.route('/user-dashboard')
def user_dashboard():
    token = session.get('token')
    if not token or not verify_token(token) or session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    classes = bookings_collection.find({'user_id': ObjectId(user_id)})

    class_details = {}
    for booking in classes:
        class_info = classes_collection.find_one({'_id': booking['class_id']})
        if class_info:
            child_id = str(booking.get('child_id', ''))
            if child_id not in class_details:
                class_details[child_id] = []
            class_details[child_id].append({
                'class_name': class_info['class_name'],
                'class_date': class_info['class_date'],
                'class_start_time': format_time_12hr(class_info['class_start_time']),
                'class_end_time': format_time_12hr(class_info['class_end_time']),
                'booking_id': str(booking['_id'])
            })

    user['classes'] = class_details

    # Debugging information
    print("User classes:", user['classes'])
    for child in user['children']:
        print(f"Classes for {child['first_name']} {child['last_name']}: {user['classes'].get(str(child['_id']), 'No upcoming classes')}")

    return render_template('user-dashboard.html', user=user)

@app.route('/schedule-class', methods=['GET', 'POST'])
def schedule_class():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        class_name = request.form['class_name']
        class_date = request.form['class_date']
        class_start_time = request.form['class_start_time']
        class_end_time = request.form['class_end_time']
        max_students = int(request.form['max_students'])

        # Validation
        if not class_name or not class_date or not class_start_time or not class_end_time or not max_students:
            flash("All fields are required.", "error")
            return redirect(url_for('schedule_class'))

        class_info = {
            'class_name': class_name,
            'class_date': class_date,
            'class_start_time': class_start_time,
            'class_end_time': class_end_time,
            'max_students': max_students,
            'students': []
        }

        try:
            classes_collection.insert_one(class_info)
        except errors.OperationFailure as e:
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('schedule_class'))

        flash("Class scheduled successfully!", "success")
        return redirect(url_for('admin_calendar'))

    return render_template('schedule-class.html')

@app.route('/create-weekly-schedule', methods=['GET', 'POST'])
def create_weekly_schedule():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

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
        return redirect(url_for('login'))

    return render_template('admin-calendar.html')

@app.route('/user-calendar')
def user_calendar():
    token = session.get('token')
    if not token or not verify_token(token):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

    return render_template('user-calendar.html')

@app.route('/api/classes')
def get_classes():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

    classes = classes_collection.find({
        'class_date': {
            '$gte': start_date.strftime('%Y-%m-%d'),
            '$lt': end_date.strftime('%Y-%m-%d')
        }
    })

    classes_by_date = {}
    for class_info in classes:
        class_date = class_info['class_date']
        if class_date not in classes_by_date:
            classes_by_date[class_date] = []
        classes_by_date[class_date].append({
            '_id': str(class_info['_id']),
            'class_name': class_info['class_name'],
            'class_start_time': class_info['class_start_time'],
            'class_end_time': class_info['class_end_time'],
            'max_students': class_info['max_students'],
            'current_students': len(class_info['students'])
        })

    return jsonify({'classes': classes_by_date})

@app.route('/api/class/<class_id>')
def get_class_details(class_id):
    class_info = classes_collection.find_one({'_id': ObjectId(class_id)})
    if not class_info:
        return jsonify({'error': 'Class not found'}), 404

    students = []
    for student_id in class_info['students']:
        student = users_collection.find_one({'_id': ObjectId(student_id)}, {'first_name': 1, 'last_name': 1})
        if student:
            students.append({
                'first_name': student['first_name'],
                'last_name': student['last_name']
            })

    return jsonify({
        'class_name': class_info['class_name'],
        'class_date': class_info['class_date'],
        'class_start_time': class_info['class_start_time'],
        'class_end_time': class_info['class_end_time'],
        'max_students': class_info['max_students'],
        'current_students': len(class_info['students']),
        'students': students
    })

@app.route('/renew-schedule', methods=['GET', 'POST'])
def renew_schedule():
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

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
                    new_class_info.pop('_id')  # Remove the _id field to avoid duplication
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
        return redirect(url_for('login'))

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
            flash("An error occurred. Please try again later.", "error")
            return redirect(url_for('edit_class', class_id=class_id))

    return render_template('edit-class.html', class_info=class_info)

@app.route('/api/edit-class/<class_id>', methods=['POST'])
def api_edit_class(class_id):
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    class_name = data.get('class_name')
    class_date = data.get('class_date')
    class_start_time = data.get('class_start_time')
    class_end_time = data.get('class_end_time')
    max_students = int(data.get('max_students'))  # Ensure max_students is an integer

    # Validation
    if not class_name or not class_date or not class_start_time or not class_end_time or not max_students:
        return jsonify({'error': 'All fields are required'}), 400

    updated_class_info = {
        'class_name': class_name,
        'class_date': class_date,
        'class_start_time': class_start_time,
        'class_end_time': class_end_time,
        'max_students': max_students
    }

    try:
        classes_collection.update_one({'_id': ObjectId(class_id)}, {'$set': updated_class_info})
        return jsonify({'success': 'Class updated successfully'}), 200
    except errors.OperationFailure as e:
        return jsonify({'error': 'An error occurred. Please try again later.'}), 500

@app.route('/remove-class/<class_id>', methods=['POST'])
def remove_class(class_id):
    token = session.get('token')
    if not token or not verify_token(token) or not session.get('is_admin'):
        flash("You do not have access to this page.", "error")
        return redirect(url_for('login'))

    try:
        # Remove the class
        classes_collection.delete_one({'_id': ObjectId(class_id)})
        # Remove the corresponding bookings
        bookings_collection.delete_many({'class_id': ObjectId(class_id)})
        flash("Class and associated bookings removed successfully!", "success")
    except errors.OperationFailure as e:
        flash("An error occurred. Please try again later.", "error")

    return redirect(url_for('admin_calendar'))

@app.route('/api/user/<user_id>')
def get_user_details(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    today = datetime.now().strftime('%Y-%m-%d')
    classes = bookings_collection.find({'user_id': ObjectId(user_id)})
    class_details = {}
    for booking in classes:
        class_info = classes_collection.find_one({'_id': booking['class_id']})
        if class_info and class_info['class_date'] >= today:
            child_id = str(booking.get('child_id', ''))
            if child_id not in class_details:
                class_details[child_id] = []
            class_details[child_id].append({
                'class_name': class_info['class_name'],
                'class_date': class_info['class_date'],
                'class_start_time': format_time_12hr(class_info['class_start_time']),
                'class_end_time': format_time_12hr(class_info['class_end_time']),
                'booking_id': str(booking['_id'])
            })

    return jsonify({
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email'],
        'phone': user['phone'],
        'children': [{'_id': str(child['_id']), 'first_name': child['first_name'], 'last_name': child['last_name']} for child in user['children']],
        'classes': class_details
    })

@app.route('/api/child/<child_id>')
def get_child_details(child_id):
    user = users_collection.find_one({'children._id': ObjectId(child_id)}, {'children.$': 1, 'email': 1, 'phone': 1})
    if not user:
        return jsonify({'error': 'Child not found'}), 404

    child = user['children'][0]
    today = datetime.now().strftime('%Y-%m-%d')
    classes = bookings_collection.find({'child_id': ObjectId(child_id)})
    class_details = []
    for booking in classes:
        class_info = classes_collection.find_one({'_id': booking['class_id']})
        if class_info and class_info['class_date'] >= today:
            class_details.append({
                'class_name': class_info['class_name'],
                'class_date': class_info['class_date'],
                'class_start_time': format_time_12hr(class_info['class_start_time']),
                'class_end_time': format_time_12hr(class_info['class_end_time']),
                'booking_id': str(booking['_id'])
            })

    return jsonify({
        'first_name': child['first_name'],
        'last_name': child['last_name'],
        'email': user['email'],
        'phone': user['phone'],
        'classes': class_details
    })

@app.route('/api/book-class/<class_id>', methods=['POST'])
def book_class(class_id):
    token = session.get('token')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized access'}), 403

    user_id = session.get('user_id')
    child_ids = request.json.get('child_ids')
    class_info = classes_collection.find_one({'_id': ObjectId(class_id)})

    if not class_info:
        return jsonify({'error': 'Class not found'}), 404

    if len(class_info['students']) + len(child_ids) > class_info['max_students']:
        return jsonify({'error': 'Class is full'}), 400

    user = users_collection.find_one({'_id': ObjectId(user_id)})
    all_children = [{'_id': str(user['_id']), 'first_name': user['first_name'], 'last_name': user['last_name']}] + user['children']

    for child_id in child_ids:
        if not ObjectId.is_valid(child_id):
            return jsonify({'error': f'Invalid child ID: {child_id}'}), 400
        if ObjectId(child_id) in class_info['students']:
            child = next((child for child in all_children if str(child['_id']) == child_id), None)
            child_name = f"{child['first_name']} {child['last_name']}" if child else "Unknown"
            return jsonify({'error': f'{child_name} is already booked for this class'}), 400

    classes_collection.update_one({'_id': ObjectId(class_id)}, {'$push': {'students': {'$each': [ObjectId(child_id) for child_id in child_ids]}}})
    bookings_collection.insert_many([{'user_id': ObjectId(user_id), 'child_id': ObjectId(child_id), 'class_id': ObjectId(class_id)} for child_id in child_ids])

    return jsonify({'success': 'Class booked successfully'}), 200

@app.route('/api/remove-booking/<booking_id>', methods=['POST'])
def remove_booking(booking_id):
    token = session.get('token')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized access'}), 403

    booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    class_id = booking['class_id']
    child_id = booking['child_id']

    try:
        bookings_collection.delete_one({'_id': ObjectId(booking_id)})
        classes_collection.update_one({'_id': ObjectId(class_id)}, {'$pull': {'students': ObjectId(child_id)}})
        return jsonify({'success': 'Booking removed successfully'}), 200
    except errors.OperationFailure as e:
        return jsonify({'error': 'An error occurred. Please try again later.'}), 500

@app.route('/api/user')
def get_current_user():
    token = session.get('token')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized access'}), 403

    user_id = session.get('user_id')
    return jsonify({'user_id': user_id})

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

