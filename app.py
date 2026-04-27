"""
Rigor Barbershop Online Booking and AI-Powered Queue Management System
Main Flask Application

This is the main entry point for the barbershop booking system.
It handles all routes, database connections, and business logic.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import qrcode
from PIL import Image
import pyttsx3
import os
from datetime import datetime, date, timedelta
import random
import string
import json
from functools import wraps

# =====================================================
# FLASK APP CONFIGURATION
# =====================================================

app = Flask(__name__)
app.secret_key = 'rigor_barbershop_secret_key_2024'  # Secret key for session management

# Database configuration - XAMPP MySQL defaults
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Default XAMPP has no password
    'database': 'rigor_barbershop',
    'port': 3306
}

# Ensure upload directories exist
UPLOAD_FOLDER = 'static/uploads'
QR_FOLDER = 'static/qr_codes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# =====================================================
# DATABASE HELPER FUNCTIONS
# =====================================================

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch_one=False):
    """Execute a database query and return results"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id
    except Error as e:
        print(f"Query error: {e}")
        conn.close()
        return None

# =====================================================
# TEXT-TO-SPEECH (VOICE ANNOUNCEMENT)
# =====================================================

def announce_queue(queue_number, customer_name):
    """
    Announce queue number using text-to-speech
    This feature calls customers when their turn arrives
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume
        
        # Create announcement message
        message = f"Attention please. Queue number {queue_number}. {customer_name}, please proceed to the service area."
        
        engine.say(message)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"Voice announcement error: {e}")
        return False

# =====================================================
# QR CODE GENERATION
# =====================================================

def generate_qr_code(queue_id, queue_number):
    """Generate QR code for queue entry"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # QR code data contains queue info
        data = f"QUEUE:{queue_number}|ID:{queue_id}|TIME:{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        filename = f"qr_{queue_number}_{queue_id}.png"
        filepath = os.path.join(QR_FOLDER, filename)
        img.save(filepath)
        
        return filename
    except Exception as e:
        print(f"QR generation error: {e}")
        return None

# =====================================================
# AI RECOMMENDATION SYSTEM
# =====================================================

def get_ai_recommendations(customer_id):
    """
    Simple AI recommendation based on booking history
    Analyzes past appointments to suggest services and barbers
    """
    recommendations = {
        'favorite_services': [],
        'favorite_barber': None,
        'suggested_time': None,
        'message': ''
    }
    
    # Get customer's booking history
    history = execute_query("""
        SELECT a.*, s.name as service_name, s.price, b.id as barber_id, u.full_name as barber_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE a.customer_id = %s AND a.status = 'completed'
        ORDER BY a.appointment_date DESC
    """, (customer_id,))
    
    if not history:
        recommendations['message'] = "Welcome! Based on popular choices, we recommend our Haircut + Beard Trim package with Juan."
        return recommendations
    
    # Count service frequency
    service_count = {}
    barber_count = {}
    
    for booking in history:
        service = booking['service_name']
        barber = booking['barber_name']
        service_count[service] = service_count.get(service, 0) + 1
        barber_count[barber] = barber_count.get(barber, 0) + 1
    
    # Find most booked service and barber
    if service_count:
        fav_service = max(service_count, key=service_count.get)
        recommendations['favorite_services'] = [fav_service]
        recommendations['message'] = f"Based on your history, you seem to love {fav_service}!"
    
    if barber_count:
        fav_barber = max(barber_count, key=barber_count.get)
        recommendations['favorite_barber'] = fav_barber
        recommendations['message'] += f" Your favorite barber is {fav_barber}."
    
    # Suggest off-peak hours
    recommendations['suggested_time'] = "02:00 PM"  # Less busy time
    
    return recommendations

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def generate_queue_number():
    """Generate unique queue number (W + 3 digits for walk-in)"""
    prefix = "W"
    number = random.randint(1, 999)
    return f"{prefix}{number:03d}"

def check_time_conflict(barber_id, appointment_date, appointment_time):
    """Check if barber is already booked at this time"""
    existing = execute_query("""
        SELECT id FROM appointments 
        WHERE barber_id = %s AND appointment_date = %s 
        AND appointment_time = %s AND status NOT IN ('cancelled', 'no_show')
    """, (barber_id, appointment_date, appointment_time), fetch_one=True)
    
    return existing is not None

def get_available_slots(barber_id, appointment_date):
    """Get available time slots for a barber on a specific date"""
    # Define business hours (9 AM to 6 PM)
    slots = []
    start_hour = 9
    end_hour = 18
    
    for hour in range(start_hour, end_hour):
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}:00"
            if not check_time_conflict(barber_id, appointment_date, time_str):
                slots.append(f"{hour:02d}:{minute:02d}")
    
    return slots

def login_required(role=None):
    """Decorator to check if user is logged in and has correct role"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                current_role = session.get('role', 'unknown')
                flash(f'Access denied: This area is restricted to {role} only. You are logged in as {current_role}.', 'danger')
                # Redirect to appropriate dashboard based on user's actual role
                if current_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif current_role == 'barber':
                    return redirect(url_for('barber_dashboard'))
                elif current_role == 'customer':
                    return redirect(url_for('customer_dashboard'))
                else:
                    return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# =====================================================
# ROUTES - AUTHENTICATION
# =====================================================

@app.route('/')
def index():
    """Home page - shows services and barbers"""
    services = execute_query("SELECT * FROM services WHERE is_active = TRUE") or []
    barbers = execute_query("""
        SELECT b.*, u.full_name, u.phone 
        FROM barbers b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.is_available = TRUE
    """) or []
    return render_template('index.html', services=services, barbers=barbers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Customer registration"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        
        # Check if username exists
        existing = execute_query("SELECT id FROM users WHERE username = %s", (username,), fetch_one=True)
        if existing:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Insert user
        user_id = execute_query(
            "INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES (%s, %s, %s, %s, %s, 'customer')",
            (username, email, password_hash, full_name, phone)
        )
        
        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Get user from database
        user = execute_query(
            "SELECT * FROM users WHERE username = %s",
            (username,), fetch_one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            flash(f'Welcome, {user["full_name"]}!', 'success')
            
            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'barber':
                return redirect(url_for('barber_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# =====================================================
# ROUTES - CUSTOMER
# =====================================================

@app.route('/customer/dashboard')
@login_required('customer')
def customer_dashboard():
    """Customer dashboard - shows bookings and recommendations"""
    customer_id = session['user_id']
    
    # Get upcoming appointments
    appointments = execute_query("""
        SELECT a.*, s.name as service_name, s.price, u.full_name as barber_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE a.customer_id = %s AND a.appointment_date >= CURDATE()
        ORDER BY a.appointment_date, a.appointment_time
    """, (customer_id,))
    
    # Get booking history
    history = execute_query("""
        SELECT a.*, s.name as service_name, s.price, u.full_name as barber_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE a.customer_id = %s AND a.appointment_date < CURDATE()
        ORDER BY a.appointment_date DESC
        LIMIT 5
    """, (customer_id,))
    
    # Get AI recommendations
    recommendations = get_ai_recommendations(customer_id)
    
    # Get customer's active queue ticket
    queue_ticket = execute_query("""
        SELECT q.*, s.name as service_name, u.full_name as barber_name
        FROM queue q
        LEFT JOIN services s ON q.service_id = s.id
        LEFT JOIN barbers b ON q.barber_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE q.customer_id = %s AND q.status IN ('waiting', 'serving')
        ORDER BY q.joined_at DESC
        LIMIT 1
    """, (customer_id,), fetch_one=True)
    
    return render_template('customer/dashboard.html', 
                         appointments=appointments, 
                         history=history,
                         recommendations=recommendations,
                         queue_ticket=queue_ticket)

@app.route('/customer/book', methods=['GET', 'POST'])
@login_required('customer')
def book_appointment():
    """Book an appointment"""
    if request.method == 'POST':
        # Get form data with validation
        barber_id = request.form.get('barber_id')
        service_id = request.form.get('service_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        notes = request.form.get('notes', '')
        customer_id = session['user_id']
        
        # Validate required fields
        if not barber_id:
            flash('Please select a barber.', 'warning')
            return redirect(url_for('book_appointment'))
        # Validate barber_id is numeric (for database compatibility)
        try:
            barber_id = int(barber_id)
        except ValueError:
            flash('Invalid barber selected. Please choose a barber from the database.', 'warning')
            return redirect(url_for('book_appointment'))
        if not service_id:
            flash('Please select a service.', 'warning')
            return redirect(url_for('book_appointment'))
        try:
            service_id = int(service_id)
        except ValueError:
            flash('Invalid service selected.', 'warning')
            return redirect(url_for('book_appointment'))
        if not appointment_date:
            flash('Please select a date.', 'warning')
            return redirect(url_for('book_appointment'))
        if not appointment_time:
            flash('Please select a time slot.', 'warning')
            return redirect(url_for('book_appointment'))
        
        # Check for conflicts
        if check_time_conflict(barber_id, appointment_date, appointment_time):
            flash('This time slot is already booked. Please choose another time.', 'warning')
            return redirect(url_for('book_appointment'))
        
        # Create appointment
        appointment_id = execute_query("""
            INSERT INTO appointments (customer_id, barber_id, service_id, appointment_date, appointment_time, status, notes)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s)
        """, (customer_id, barber_id, service_id, appointment_date, appointment_time, notes))
        
        if appointment_id:
            flash('Appointment booked successfully! Waiting for confirmation.', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Failed to book appointment', 'danger')
    
    # Get available barbers and services for the form
    barbers = execute_query("""
        SELECT b.*, u.full_name 
        FROM barbers b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.is_available = TRUE
    """)
    services = execute_query("SELECT * FROM services WHERE is_active = TRUE")
    
    return render_template('customer/book.html', barbers=barbers, services=services)

@app.route('/customer/walkin', methods=['GET', 'POST'])
@login_required('customer')
def walkin_booking():
    """Walk-in booking - for immediate service today"""
    if request.method == 'POST':
        barber_id = request.form.get('barber_id')
        service_id = request.form.get('service_id')
        notes = request.form.get('notes', '')
        customer_id = session['user_id']
        
        # Validate required fields
        if not barber_id:
            flash('Please select a barber.', 'warning')
            return redirect(url_for('walkin_booking'))
        try:
            barber_id = int(barber_id)
        except ValueError:
            flash('Invalid barber selected.', 'warning')
            return redirect(url_for('walkin_booking'))
            
        if not service_id:
            flash('Please select a service.', 'warning')
            return redirect(url_for('walkin_booking'))
        try:
            service_id = int(service_id)
        except ValueError:
            flash('Invalid service selected.', 'warning')
            return redirect(url_for('walkin_booking'))
        
        # Get current date and next available time slot
        from datetime import datetime, timedelta
        today = date.today()
        current_time = datetime.now()
        
        # Round up to next 30-min slot
        if current_time.minute < 30:
            next_slot = current_time.replace(minute=30, second=0, microsecond=0)
        else:
            next_slot = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        appointment_time = next_slot.strftime('%H:%M:%S')
        
        # Check for conflicts
        if check_time_conflict(barber_id, today, appointment_time):
            flash('Barber is busy at this time. Please try another barber or wait.', 'warning')
            return redirect(url_for('walkin_booking'))
        
        # Create walk-in appointment
        appointment_id = execute_query("""
            INSERT INTO appointments (customer_id, barber_id, service_id, appointment_date, appointment_time, status, notes, is_walkin)
            VALUES (%s, %s, %s, %s, %s, 'confirmed', %s, TRUE)
        """, (customer_id, barber_id, service_id, today, appointment_time, notes))
        
        if appointment_id:
            flash('Walk-in booked successfully! Please proceed to the barbershop.', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Failed to book walk-in appointment', 'danger')
    
    # Get available barbers and services
    barbers = execute_query("""
        SELECT b.*, u.full_name 
        FROM barbers b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.is_available = TRUE
    """)
    services = execute_query("SELECT * FROM services WHERE is_active = TRUE")
    
    return render_template('customer/walkin.html', barbers=barbers, services=services)

@app.route('/api/available_slots/<int:barber_id>/<date>')
def get_slots(barber_id, date):
    """API endpoint to get available time slots"""
    slots = get_available_slots(barber_id, date)
    return jsonify({'slots': slots})

@app.route('/customer/cancel/<int:appointment_id>')
@login_required('customer')
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    customer_id = session['user_id']
    
    # Verify ownership
    appointment = execute_query(
        "SELECT * FROM appointments WHERE id = %s AND customer_id = %s",
        (appointment_id, customer_id), fetch_one=True
    )
    
    if appointment:
        execute_query(
            "UPDATE appointments SET status = 'cancelled' WHERE id = %s",
            (appointment_id,)
        )
        flash('Appointment cancelled successfully', 'success')
    else:
        flash('Appointment not found', 'danger')
    
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/payment/<int:appointment_id>')
@login_required('customer')
def payment_page(appointment_id):
    """Payment page for appointment"""
    customer_id = session['user_id']
    
    # Get appointment details
    appointment = execute_query("""
        SELECT a.*, s.name as service_name, s.price, s.duration_minutes,
               u.full_name as barber_name, u.phone as barber_phone
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE a.id = %s AND a.customer_id = %s
    """, (appointment_id, customer_id), fetch_one=True)
    
    if not appointment:
        flash('Appointment not found', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    # Check existing payment
    payment = execute_query(
        "SELECT * FROM payments WHERE appointment_id = %s",
        (appointment_id,), fetch_one=True
    )
    
    return render_template('customer/payment.html', 
                         appointment=appointment, 
                         payment=payment)

@app.route('/customer/process_payment/<int:appointment_id>', methods=['POST'])
@login_required('customer')
def process_payment(appointment_id):
    """Process payment for appointment"""
    customer_id = session['user_id']
    payment_method = request.form.get('payment_method')
    
    # Get appointment and service details
    appointment = execute_query("""
        SELECT a.*, s.price, s.name as service_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        WHERE a.id = %s AND a.customer_id = %s
    """, (appointment_id, customer_id), fetch_one=True)
    
    if not appointment:
        flash('Appointment not found', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    # Generate transaction reference
    import random
    import string
    transaction_ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    # Create payment record
    payment_id = execute_query("""
        INSERT INTO payments (appointment_id, customer_id, amount, payment_method, 
                            payment_status, transaction_reference, paid_at)
        VALUES (%s, %s, %s, %s, 'completed', %s, NOW())
    """, (appointment_id, customer_id, appointment['price'], payment_method, transaction_ref))
    
    if payment_id:
        # Update appointment status to confirmed
        execute_query(
            "UPDATE appointments SET status = 'confirmed' WHERE id = %s",
            (appointment_id,)
        )
        flash(f'Payment successful! Transaction Reference: {transaction_ref}', 'success')
    else:
        flash('Payment failed. Please try again.', 'danger')
    
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/payment_history')
@login_required('customer')
def payment_history():
    """View payment history"""
    customer_id = session['user_id']
    
    payments = execute_query("""
        SELECT p.*, s.name as service_name, u.full_name as barber_name,
               a.appointment_date, a.appointment_time
        FROM payments p
        JOIN appointments a ON p.appointment_id = a.id
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users u ON b.user_id = u.id
        WHERE p.customer_id = %s
        ORDER BY p.created_at DESC
    """, (customer_id,))
    
    return render_template('customer/payment_history.html', payments=payments)

# =====================================================
# ROUTES - QUEUE SYSTEM
# =====================================================

@app.route('/queue')
@login_required('customer')
def queue_status():
    """Personal queue status - shows only the logged-in customer's queue entries"""
    customer_id = session.get('user_id')
    
    # Get customer's own waiting queue entries
    waiting = execute_query("""
        SELECT q.*, s.name as service_name, u.full_name as barber_name
        FROM queue q
        LEFT JOIN services s ON q.service_id = s.id
        LEFT JOIN barbers b ON q.barber_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE q.customer_id = %s AND q.status = 'waiting'
        ORDER BY q.priority DESC, q.joined_at
    """, (customer_id,))
    
    # Get customer's own serving queue entries
    serving = execute_query("""
        SELECT q.*, s.name as service_name, u.full_name as barber_name
        FROM queue q
        LEFT JOIN services s ON q.service_id = s.id
        LEFT JOIN barbers b ON q.barber_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE q.customer_id = %s AND q.status = 'serving'
    """, (customer_id,))
    
    return render_template('queue/status.html', waiting=waiting, serving=serving, personal_view=True)

@app.route('/queue/join', methods=['GET', 'POST'])
def join_queue():
    """Join the queue (for walk-in customers)"""
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        phone = request.form['phone']
        service_id = request.form.get('service_id')
        
        # Generate queue number
        queue_number = generate_queue_number()
        
        # Check if customer is logged in
        customer_id = session.get('user_id') if session.get('role') == 'customer' else None
        
        # Add to queue
        queue_id = execute_query("""
            INSERT INTO queue (queue_number, customer_id, customer_name, phone, service_id, status)
            VALUES (%s, %s, %s, %s, %s, 'waiting')
        """, (queue_number, customer_id, customer_name, phone, service_id))
        
        if queue_id:
            # Generate QR code
            qr_filename = generate_qr_code(queue_id, queue_number)
            if qr_filename:
                execute_query(
                    "UPDATE queue SET qr_code = %s WHERE id = %s",
                    (qr_filename, queue_id)
                )
            
            flash(f'You are now in queue! Your number is {queue_number}', 'success')
            return redirect(url_for('queue_ticket', queue_id=queue_id))
        else:
            flash('Failed to join queue', 'danger')
    
    services = execute_query("SELECT * FROM services WHERE is_active = TRUE")
    return render_template('queue/join.html', services=services)

@app.route('/queue/ticket/<int:queue_id>')
def queue_ticket(queue_id):
    """Display queue ticket with QR code"""
    ticket = execute_query(
        "SELECT * FROM queue WHERE id = %s",
        (queue_id,), fetch_one=True
    )
    
    if not ticket:
        flash('Ticket not found', 'danger')
        return redirect(url_for('queue_status'))
    
    return render_template('queue/ticket.html', ticket=ticket)

@app.route('/queue/scan')
def scan_qr():
    """QR code scanning page"""
    return render_template('queue/scan.html')

# =====================================================
# ROUTES - BARBER
# =====================================================

@app.route('/barber/dashboard')
@login_required('barber')
def barber_dashboard():
    """Barber dashboard - shows assigned customers"""
    # Get barber ID from user ID
    barber = execute_query(
        "SELECT id FROM barbers WHERE user_id = %s",
        (session['user_id'],), fetch_one=True
    )
    
    if not barber:
        flash('Barber profile not found', 'danger')
        return redirect(url_for('index'))
    
    barber_id = barber['id']
    
    # Get today's appointments
    today = date.today()
    appointments = execute_query("""
        SELECT a.*, s.name as service_name, s.duration_minutes, u.full_name as customer_name, u.phone
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN users u ON a.customer_id = u.id
        WHERE a.barber_id = %s AND a.appointment_date = %s AND a.status IN ('pending', 'confirmed')
        ORDER BY a.appointment_time
    """, (barber_id, today))
    
    # Get queue customers assigned to this barber
    queue_customers = execute_query("""
        SELECT q.*, s.name as service_name
        FROM queue q
        LEFT JOIN services s ON q.service_id = s.id
        WHERE q.barber_id = %s AND q.status IN ('waiting', 'serving')
        ORDER BY q.priority DESC, q.joined_at
    """, (barber_id,))
    
    return render_template('barber/dashboard.html', 
                         appointments=appointments, 
                         queue_customers=queue_customers)

@app.route('/barber/update_status/<int:appointment_id>/<status>')
@login_required('barber')
def update_appointment_status(appointment_id, status):
    """Update appointment status (pending -> confirmed -> completed)"""
    barber = execute_query(
        "SELECT id FROM barbers WHERE user_id = %s",
        (session['user_id'],), fetch_one=True
    )
    
    if not barber:
        flash('Unauthorized', 'danger')
        return redirect(url_for('barber_dashboard'))
    
    # Verify appointment belongs to this barber
    appointment = execute_query(
        "SELECT * FROM appointments WHERE id = %s AND barber_id = %s",
        (appointment_id, barber['id']), fetch_one=True
    )
    
    if appointment:
        execute_query(
            "UPDATE appointments SET status = %s WHERE id = %s",
            (status, appointment_id)
        )
        flash(f'Appointment status updated to {status}', 'success')
    else:
        flash('Appointment not found', 'danger')
    
    return redirect(url_for('barber_dashboard'))

@app.route('/barber/call_queue/<int:queue_id>')
@login_required('barber')
def call_queue_customer(queue_id):
    """Call next customer in queue and announce via voice"""
    barber = execute_query(
        "SELECT id FROM barbers WHERE user_id = %s",
        (session['user_id'],), fetch_one=True
    )
    
    if not barber:
        flash('Unauthorized', 'danger')
        return redirect(url_for('barber_dashboard'))
    
    # Get queue entry
    queue_entry = execute_query(
        "SELECT * FROM queue WHERE id = %s AND barber_id IS NULL",
        (queue_id,), fetch_one=True
    )
    
    if queue_entry:
        # Assign barber and update status
        execute_query("""
            UPDATE queue 
            SET barber_id = %s, status = 'serving', called_at = NOW() 
            WHERE id = %s
        """, (barber['id'], queue_id))
        
        # Make voice announcement
        announce_queue(queue_entry['queue_number'], queue_entry['customer_name'])
        
        flash(f'Called customer {queue_entry["customer_name"]}', 'success')
    else:
        flash('Queue entry not found or already assigned', 'warning')
    
    return redirect(url_for('barber_dashboard'))

@app.route('/barber/complete_queue/<int:queue_id>')
@login_required('barber')
def complete_queue_service(queue_id):
    """Mark queue service as completed"""
    barber = execute_query(
        "SELECT id FROM barbers WHERE user_id = %s",
        (session['user_id'],), fetch_one=True
    )
    
    if barber:
        execute_query("""
            UPDATE queue 
            SET status = 'completed', completed_at = NOW() 
            WHERE id = %s AND barber_id = %s
        """, (queue_id, barber['id']))
        flash('Service completed', 'success')
    
    return redirect(url_for('barber_dashboard'))

# =====================================================
# ROUTES - ADMIN
# =====================================================

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    """Admin dashboard with analytics"""
    today = date.today()
    
    # Today's statistics
    today_stats = execute_query("""
        SELECT 
            COUNT(*) as total_bookings,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM appointments 
        WHERE appointment_date = %s
    """, (today,), fetch_one=True)
    
    # Total customers
    total_customers = execute_query(
        "SELECT COUNT(*) as count FROM users WHERE role = 'customer'",
        fetch_one=True
    )
    
    # Total barbers
    total_barbers = execute_query(
        "SELECT COUNT(*) as count FROM barbers WHERE is_available = TRUE",
        fetch_one=True
    )
    
    # Recent appointments
    recent_appointments = execute_query("""
        SELECT a.*, u.full_name as customer_name, s.name as service_name, barb.full_name as barber_name
        FROM appointments a
        JOIN users u ON a.customer_id = u.id
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users barb ON b.user_id = barb.id
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    # Peak hours analysis
    peak_hours = execute_query("""
        SELECT HOUR(appointment_time) as hour, COUNT(*) as count
        FROM appointments
        WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY HOUR(appointment_time)
        ORDER BY count DESC
        LIMIT 5
    """)
    
    # Barber performance
    barber_performance = execute_query("""
        SELECT u.full_name, COUNT(a.id) as total_appointments,
               AVG(f.rating) as avg_rating
        FROM barbers b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN appointments a ON b.id = a.barber_id AND a.status = 'completed'
        LEFT JOIN feedback f ON b.id = f.barber_id
        GROUP BY b.id, u.full_name
        ORDER BY total_appointments DESC
    """)
    
    # Active queue count
    queue_count = execute_query(
        "SELECT COUNT(*) as count FROM queue WHERE status = 'waiting'",
        fetch_one=True
    )
    
    return render_template('admin/dashboard.html',
                         today_stats=today_stats,
                         total_customers=total_customers,
                         total_barbers=total_barbers,
                         recent_appointments=recent_appointments,
                         peak_hours=peak_hours,
                         barber_performance=barber_performance,
                         queue_count=queue_count)

@app.route('/admin/bookings')
@login_required('admin')
def admin_bookings():
    """View all bookings"""
    bookings = execute_query("""
        SELECT a.*, u.full_name as customer_name, s.name as service_name, barb.full_name as barber_name
        FROM appointments a
        JOIN users u ON a.customer_id = u.id
        JOIN services s ON a.service_id = s.id
        JOIN barbers b ON a.barber_id = b.id
        JOIN users barb ON b.user_id = barb.id
        ORDER BY a.appointment_date DESC, a.appointment_time
    """)
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/queue')
@login_required('admin')
def admin_queue():
    """Monitor and manage queue"""
    queue = execute_query("""
        SELECT q.*, s.name as service_name, u.full_name as barber_name
        FROM queue q
        LEFT JOIN services s ON q.service_id = s.id
        LEFT JOIN barbers b ON q.barber_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        ORDER BY q.status, q.priority DESC, q.joined_at
    """)
    
    available_barbers = execute_query("""
        SELECT b.*, u.full_name 
        FROM barbers b 
        JOIN users u ON b.user_id = u.id 
        WHERE b.is_available = TRUE
    """)
    
    return render_template('admin/queue.html', queue=queue, barbers=available_barbers)

@app.route('/admin/assign_barber/<int:queue_id>', methods=['POST'])
@login_required('admin')
def assign_barber(queue_id):
    """Assign barber to queue entry"""
    barber_id = request.form['barber_id']
    
    execute_query(
        "UPDATE queue SET barber_id = %s WHERE id = %s",
        (barber_id, queue_id)
    )
    
    flash('Barber assigned successfully', 'success')
    return redirect(url_for('admin_queue'))

@app.route('/admin/call/<int:queue_id>')
@login_required('admin')
def admin_call_queue(queue_id):
    """Admin calls queue number with voice announcement"""
    queue_entry = execute_query(
        "SELECT * FROM queue WHERE id = %s",
        (queue_id,), fetch_one=True
    )
    
    if queue_entry:
        # Update status
        execute_query(
            "UPDATE queue SET status = 'serving', called_at = NOW() WHERE id = %s",
            (queue_id,)
        )
        
        # Make voice announcement
        announce_queue(queue_entry['queue_number'], queue_entry['customer_name'])
        
        flash(f'Announced queue number {queue_entry["queue_number"]}', 'success')
    
    return redirect(url_for('admin_queue'))

@app.route('/admin/barbers')
@login_required('admin')
def manage_barbers():
    """Manage barbers"""
    barbers = execute_query("""
        SELECT b.*, u.username, u.email, u.full_name, u.phone
        FROM barbers b
        JOIN users u ON b.user_id = u.id
    """)
    return render_template('admin/barbers.html', barbers=barbers)

@app.route('/admin/barber/toggle/<int:barber_id>')
@login_required('admin')
def toggle_barber_status(barber_id):
    """Toggle barber availability"""
    barber = execute_query(
        "SELECT is_available FROM barbers WHERE id = %s",
        (barber_id,), fetch_one=True
    )
    
    if barber:
        new_status = not barber['is_available']
        execute_query(
            "UPDATE barbers SET is_available = %s WHERE id = %s",
            (new_status, barber_id)
        )
        status_text = 'available' if new_status else 'unavailable'
        flash(f'Barber is now {status_text}', 'success')
    
    return redirect(url_for('manage_barbers'))

@app.route('/admin/services')
@login_required('admin')
def manage_services():
    """Manage services"""
    services = execute_query("SELECT * FROM services")
    return render_template('admin/services.html', services=services)

@app.route('/admin/service/add', methods=['POST'])
@login_required('admin')
def add_service():
    """Add new service"""
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    duration = request.form['duration']
    
    execute_query("""
        INSERT INTO services (name, description, price, duration_minutes)
        VALUES (%s, %s, %s, %s)
    """, (name, description, price, duration))
    
    flash('Service added successfully', 'success')
    return redirect(url_for('manage_services'))

@app.route('/admin/send_reminders')
@login_required('admin')
def send_reminders():
    """Send appointment reminders (simulated)"""
    tomorrow = date.today() + timedelta(days=1)
    
    # Get tomorrow's appointments
    appointments = execute_query("""
        SELECT a.*, u.full_name, u.email, u.phone
        FROM appointments a
        JOIN users u ON a.customer_id = u.id
        WHERE a.appointment_date = %s AND a.reminder_sent = FALSE
    """, (tomorrow,))
    
    count = 0
    for appt in appointments:
        # Create notification
        message = f"Reminder: You have an appointment tomorrow at {appt['appointment_time']}. See you at Rigor Barbershop!"
        execute_query("""
            INSERT INTO notifications (user_id, type, message)
            VALUES (%s, 'appointment_reminder', %s)
        """, (appt['customer_id'], message))
        
        # Mark as sent
        execute_query(
            "UPDATE appointments SET reminder_sent = TRUE WHERE id = %s",
            (appt['id'],)
        )
        
        count += 1
        print(f"Reminder sent to {appt['full_name']} ({appt['email']}): {message}")
    
    flash(f'Sent {count} appointment reminders', 'success')
    return redirect(url_for('admin_dashboard'))

# =====================================================
# ROUTES - PROFILE
# =====================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    """User profile page - for all roles"""
    user_id = session['user_id']
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        
        # Update user profile
        execute_query("""
            UPDATE users 
            SET full_name = %s, email = %s, phone = %s
            WHERE id = %s
        """, (full_name, email, phone, user_id))
        
        # Update session
        session['full_name'] = full_name
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    # Get user info
    user = execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True)
    
    # Get role-specific info
    role_data = None
    if session['role'] == 'barber':
        role_data = execute_query(
            "SELECT * FROM barbers WHERE user_id = %s", (user_id,), fetch_one=True
        )
    
    return render_template('profile.html', user=user, role_data=role_data)

@app.route('/profile/change_password', methods=['POST'])
@login_required()
def change_password():
    """Change user password"""
    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    
    # Verify current password
    user = execute_query(
        "SELECT password_hash FROM users WHERE id = %s", 
        (user_id,), fetch_one=True
    )
    
    if user and check_password_hash(user['password_hash'], current_password):
        # Update password
        new_hash = generate_password_hash(new_password)
        execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, user_id)
        )
        flash('Password changed successfully', 'success')
    else:
        flash('Current password is incorrect', 'danger')
    
    return redirect(url_for('profile'))

# =====================================================
# MAIN ENTRY POINT
# =====================================================

if __name__ == '__main__':
    # Run the Flask application
    # Debug mode should be False in production
    app.run(debug=True, host='0.0.0.0', port=5000)
