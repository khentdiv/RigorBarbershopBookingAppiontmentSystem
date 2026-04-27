# Rigor Barbershop Online Booking and AI-Powered Queue Management System

A complete web-based barbershop management system built with Flask, MySQL, and modern web technologies. This system provides online appointment booking, digital queue management with QR codes, AI-powered recommendations, and voice announcements.

## Features

### Core Features (9 Total)
1. **Online Appointment Booking System** - Customers can book appointments online
2. **Conflict-Free Scheduling** - No double booking with smart time slot management
3. **Real-Time Barber Availability** - See which barbers are available
4. **Digital Queue System** - Walk-in customers get queue numbers
5. **QR Code-Based Queue Entry** - Generate and scan QR codes for queue management
6. **Automated Appointment Reminders** - Notification system for upcoming appointments
7. **AI Recommendation System** - Smart suggestions based on booking history
8. **Voice Queue Announcement** - Text-to-speech calling system using pyttsx3
9. **Admin Dashboard with Analytics** - Daily bookings, peak hours, and barber performance

### User Roles
- **Admin** - Full system control, analytics, manage barbers/services
- **Barber** - View appointments, update status, serve queue customers
- **Customer** - Book appointments, view history, join queue

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | HTML, CSS, JavaScript (Vanilla) |
| Backend | Python Flask |
| Database | MySQL |
| QR Codes | qrcode library |
| Voice | pyttsx3 (text-to-speech) |

## Project Structure

```
/project
├── app.py              # Main Flask application
├── database.sql        # MySQL database schema and sample data
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/         # HTML templates (Jinja2)
│   ├── base.html      # Base template
│   ├── index.html     # Home page
│   ├── login.html     # Login page
│   ├── register.html  # Registration page
│   ├── customer/      # Customer templates
│   │   ├── dashboard.html
│   │   └── book.html
│   ├── barber/        # Barber templates
│   │   └── dashboard.html
│   ├── admin/         # Admin templates
│   │   ├── dashboard.html
│   │   ├── bookings.html
│   │   ├── queue.html
│   │   ├── barbers.html
│   │   └── services.html
│   └── queue/         # Queue templates
│       ├── status.html
│       ├── join.html
│       ├── ticket.html
│       └── scan.html
├── static/            # Static assets
│   ├── css/
│   │   └── style.css  # Main stylesheet
│   ├── js/
│   │   └── main.js    # JavaScript functionality
│   ├── uploads/       # Upload directory
│   └── qr_codes/      # Generated QR codes
```

## Setup Instructions

### Prerequisites

1. **XAMPP** (includes Apache, MySQL, PHP) - Download from [apachefriends.org](https://www.apachefriends.org)
2. **Python 3.8+** - Download from [python.org](https://python.org)

### Step 1: Install Python Dependencies

Open Command Prompt and navigate to the project folder:

```bash
cd c:\xampp\htdocs\rigorbabaedor
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- mysql-connector-python (MySQL database driver)
- qrcode (QR code generation)
- Pillow (image processing)
- pyttsx3 (text-to-speech)

### Step 2: Setup MySQL Database

1. **Start XAMPP Control Panel** and start **Apache** and **MySQL**

2. **Open phpMyAdmin** in your browser:
   - Go to: http://localhost/phpmyadmin

3. **Create the database**:
   - Click "New" to create a database
   - Name it: `rigor_barbershop`
   - Click "Create"

4. **Import the database schema**:
   - Click on the `rigor_barbershop` database
   - Go to "Import" tab
   - Choose file: `c:\xampp\htdocs\rigorbabaedor\database.sql`
   - Click "Go"

### Step 3: Configure Database Connection

The default database configuration in `app.py` uses XAMPP defaults:
- Host: localhost
- User: root
- Password: (empty)
- Database: rigor_barbershop

If your MySQL setup is different, edit the `DB_CONFIG` in `app.py`.

### Step 4: Run the Flask Application

In Command Prompt, from the project directory:

```bash
cd c:\xampp\htdocs\rigorbabaedor
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### Step 5: Access the System

Open your web browser and go to:

```
http://localhost:5000
```

## Sample Login Accounts

Use these accounts to test the system:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Barber | juan | barber123 |
| Barber | pedro | barber123 |
| Barber | miguel | barber123 |
| Customer | customer1 | customer123 |
| Customer | customer2 | customer123 |

## Usage Guide

### For Customers:
1. Register a new account or login
2. Go to "My Dashboard" to view bookings
3. Click "Book Now" to schedule an appointment
4. Select barber, service, date, and time
5. For walk-ins, go to "Join Queue" to get a queue number

### For Barbers:
1. Login with barber credentials
2. View today's appointments on the dashboard
3. Confirm or complete appointments
4. Call queue customers when ready
5. Mark services as complete

### For Admins:
1. Login with admin credentials
2. View dashboard with analytics
3. Manage all bookings
4. Monitor and manage queue
5. Manage barbers (availability)
6. Manage services and pricing
7. Send appointment reminders

## Features in Detail

### 1. Online Appointment Booking
- Select from available barbers
- Choose services with pricing
- Pick date and available time slots
- Add special notes

### 2. Conflict-Free Scheduling
- System checks for existing bookings
- Shows only available time slots
- Prevents double-booking

### 3. Real-Time Barber Availability
- Barber profiles with specialties
- Working hours display
- Rating system

### 4. Digital Queue System
- Walk-in customers get queue numbers
- Priority queue support
- Status tracking (waiting/serving/completed)

### 5. QR Code System
- Generate QR codes for queue tickets
- Scan QR codes to check status
- Mobile-friendly

### 6. Appointment Reminders
- Automated notifications
- Email simulation (logs to console)
- Admin can manually send reminders

### 7. AI Recommendations
- Analyzes booking history
- Suggests favorite services
- Recommends preferred barber
- Suggests off-peak times

### 8. Voice Announcements
- Uses pyttsx3 for text-to-speech
- Announces queue numbers
- Calls customer by name

### 9. Admin Analytics
- Daily booking statistics
- Peak hours analysis
- Barber performance metrics
- Revenue tracking

## Database Schema

### Tables:
- **users** - All system users (admin, barbers, customers)
- **barbers** - Extended barber profiles
- **services** - Available services and pricing
- **appointments** - Customer bookings
- **queue** - Walk-in queue entries
- **feedback** - Customer reviews
- **analytics** - Daily statistics
- **notifications** - System notifications

See `database.sql` for complete schema with relationships and sample data.

## Troubleshooting

### Common Issues:

1. **MySQL Connection Error**
   - Check if MySQL is running in XAMPP
   - Verify database name in `app.py`
   - Check username and password

2. **Port Already in Use**
   - Change port in `app.py`: `app.run(port=5001)`

3. **QR Codes Not Generating**
   - Ensure `static/qr_codes` directory exists
   - Check write permissions

4. **Voice Not Working**
   - pyttsx3 requires system TTS support
   - On Windows: Should work automatically
   - Check audio output

5. **Module Not Found Error**
   - Run: `pip install -r requirements.txt` again
   - Check Python version (3.8+)

## Development Notes

### For Beginners:
- All code is commented for easy understanding
- Follows Flask best practices
- Uses Jinja2 templating
- CSS uses modern flexbox and grid
- JavaScript is vanilla (no frameworks needed)

### Security:
- Passwords are hashed using Werkzeug
- SQL injection prevention via parameterized queries
- Session management with Flask

## License

This project is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Check Flask/MySQL documentation

---

**Happy Coding!** - Rigor Barbershop System
