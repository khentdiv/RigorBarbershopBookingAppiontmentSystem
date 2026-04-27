-- =====================================================
-- Rigor Barbershop Online Booking and AI-Powered Queue Management System
-- MySQL Database Schema
-- =====================================================

-- Create database
CREATE DATABASE IF NOT EXISTS rigor_barbershop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rigor_barbershop;

-- =====================================================
-- TABLE: users
-- Stores all system users (customers, barbers, admins)
-- =====================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- Store hashed passwords only
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin', 'customer', 'barber') NOT NULL DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: barbers
-- Extended profile for barber users
-- =====================================================
CREATE TABLE barbers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    specialty VARCHAR(100),              -- Barber's specialty (e.g., "Fade Expert")
    bio TEXT,                            -- Short biography
    experience_years INT,                -- Years of experience
    rating DECIMAL(3,2) DEFAULT 5.00,   -- Average rating (0.00 to 5.00)
    is_available BOOLEAN DEFAULT TRUE,   -- Currently working?
    working_hours_start TIME DEFAULT '09:00:00',
    working_hours_end TIME DEFAULT '18:00:00',
    profile_image VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: services
-- Available barbershop services
-- =====================================================
CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration_minutes INT NOT NULL,       -- Estimated service duration
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: appointments
-- Customer bookings
-- =====================================================
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    barber_id INT NOT NULL,
    service_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled', 'no_show') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reminder_sent BOOLEAN DEFAULT FALSE,  -- Track if reminder was sent
    is_walkin BOOLEAN DEFAULT FALSE,  -- Track if appointment is walk-in
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (barber_id) REFERENCES barbers(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
) ENGINE=InnoDB;

-- Index for conflict checking
CREATE INDEX idx_appointments_date_time ON appointments(barber_id, appointment_date, appointment_time);
CREATE INDEX idx_appointments_customer ON appointments(customer_id);

-- =====================================================
-- TABLE: queue
-- Digital queue for walk-in customers
-- =====================================================
CREATE TABLE queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    queue_number VARCHAR(10) NOT NULL,   -- e.g., "A001", "W005"
    customer_id INT,                      -- NULL for walk-ins without account
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    service_id INT,
    barber_id INT,
    status ENUM('waiting', 'serving', 'completed', 'cancelled') DEFAULT 'waiting',
    priority INT DEFAULT 0,              -- Higher = served first
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    called_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    qr_code VARCHAR(255),                 -- Path to generated QR code image
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (barber_id) REFERENCES barbers(id)
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: feedback
-- Customer reviews and ratings
-- =====================================================
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    customer_id INT NOT NULL,
    barber_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (barber_id) REFERENCES barbers(id)
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: analytics
-- Daily statistics for dashboard
-- =====================================================
CREATE TABLE analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_bookings INT DEFAULT 0,
    walk_ins INT DEFAULT 0,
    completed_services INT DEFAULT 0,
    cancelled_appointments INT DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0.00,
    peak_hour VARCHAR(10),
    avg_wait_time_minutes INT DEFAULT 0
) ENGINE=InnoDB;

-- =====================================================
-- TABLE: notifications
-- System notifications and reminders
-- =====================================================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('appointment_reminder', 'queue_call', 'promotion', 'system') NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================
-- INSERT SAMPLE DATA
-- =====================================================

-- Admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES
('admin', 'admin@rigorbarbershop.com', 'scrypt:32768:8:1$MjvPu6dhiaG66MAw$b5bab71a29c084b64482a69132dcf00cf2335300e8c15af04d74e540fc6c02f4498131f226d6c673cee80638a867d447084f2ee5a90a4561d8d53abc9f0a1dc8', 'System Administrator', '09123456789', 'admin');

-- Sample barbers (passwords: barber123)
INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES
('juan', 'juan@rigorbarbershop.com', 'scrypt:32768:8:1$caGu2z71HUIyPT02$a25372063644d92bb05f99884fd833d4754225c6e21db581bef5b68ab5588d0d3b7e8ec2bad902e5e04e037f576fe4659caea634b7fe42097d51ad6e4505f67e', 'Juan Dela Cruz', '09111111111', 'barber'),
('pedro', 'pedro@rigorbarbershop.com', 'scrypt:32768:8:1$FYIWut82CVb8ZRIu$f4e164767b7ca56be7d7c92faee836bb2f6fe5cf25eff235dbb6a4896c0e2d746d44eec671d68fb7aa7aff2e36af53a9afcad60ba590b2ae0fe94256018bab2d', 'Pedro Santos', '09222222222', 'barber'),
('miguel', 'miguel@rigorbarbershop.com', 'scrypt:32768:8:1$iKOeMwz9K7pUh12N$7f1c56f22d45280e35c69355e97cf2b86172c3ad88441efaae608eb91ec3eb5182ccea5434cd0a527b4fbd5ac97a151e86cdf8da21ef602d8f45b318048b49f6', 'Miguel Reyes', '09333333333', 'barber');

-- Barber profiles
INSERT INTO barbers (user_id, specialty, bio, experience_years, working_hours_start, working_hours_end) VALUES
(2, 'Classic Cuts & Fades', 'Master barber with 5 years experience in modern and classic hairstyles', 5, '09:00:00', '18:00:00'),
(3, 'Beard Styling', 'Specialist in beard grooming and hot towel shaves', 3, '10:00:00', '19:00:00'),
(4, 'Kids Haircuts', 'Patient and skilled with children of all ages', 4, '09:00:00', '17:00:00');

-- Sample customers (passwords: customer123)
INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES
('customer1', 'john@gmail.com', 'scrypt:32768:8:1$IJ9l0p1YHPH2dKfk$d339fa3c0fd8f64e4cc1699adccf6c1ce5c550a560d5340dabd4f6a540eb6639d7b1578bbc3d6bd4e703c14ed67dc61a59bf9056576dcfda229960195681599f', 'John Smith', '09444444444', 'customer'),
('customer2', 'maria@gmail.com', 'scrypt:32768:8:1$GR7dQYQT5tfEjW1w$95c144e39f03619252c5a4329b5957ed28fecc5a5e30d73c8a0c799c109ba6f683656d4694a31a2a633dbab13df3048921a35a6b8fb7d1991032ccb3a6ddc187', 'Maria Garcia', '09555555555', 'customer');

-- Sample services
INSERT INTO services (name, description, price, duration_minutes) VALUES
('Haircut', 'Standard men\'s haircut with styling', 250.00, 30),
('Haircut + Beard Trim', 'Complete package with haircut and beard grooming', 350.00, 45),
('Hot Towel Shave', 'Traditional straight razor shave with hot towel treatment', 300.00, 30),
('Beard Trim', 'Professional beard shaping and trimming', 150.00, 20),
('Kids Haircut', 'Haircut for children under 12', 200.00, 25),
('Hair Coloring', 'Full hair coloring service', 500.00, 60),
('Hair Treatment', 'Deep conditioning hair treatment', 400.00, 45);

-- Sample appointments
INSERT INTO appointments (customer_id, barber_id, service_id, appointment_date, appointment_time, status) VALUES
(5, 1, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '10:00:00', 'confirmed'),
(5, 2, 2, DATE_ADD(CURDATE(), INTERVAL 3 DAY), '14:00:00', 'pending'),
(6, 3, 5, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '11:00:00', 'confirmed');

-- Sample queue entries
INSERT INTO queue (queue_number, customer_name, phone, service_id, status, priority) VALUES
('W001', 'Walk-in Customer', '09666666666', 1, 'waiting', 0);

-- =====================================================
-- TABLE: payments
-- Payment transactions for appointments
-- =====================================================
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    customer_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'gcash', 'paymaya', 'card', 'grabpay') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    transaction_reference VARCHAR(255),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (customer_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- Index for payment lookups
CREATE INDEX idx_payments_appointment ON payments(appointment_id);
CREATE INDEX idx_payments_customer ON payments(customer_id);

-- Note: Password hashes are placeholders. The application uses Flask's generate_password_hash()
-- Run this SQL in phpMyAdmin or MySQL command line to create the database and tables.
