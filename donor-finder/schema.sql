-- ============================================================================
-- Blood & Organ Donor Finder Database Schema
-- DBMS Project (MySQL)
-- Designed for College Submission
-- ============================================================================

CREATE DATABASE IF NOT EXISTS blood_organ_donor_db;
USE blood_organ_donor_db;

-- ----------------------------------------------------------------------------
-- 1. Table: users
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('Donor', 'Recipient', 'Admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. Table: donors
-- ----------------------------------------------------------------------------
CREATE TABLE donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    organs_willing_to_donate SET('Kidney', 'Liver', 'Lung', 'Heart', 'Pancreas', 'Cornea') DEFAULT NULL,
    city VARCHAR(100) NOT NULL,
    availability_status ENUM('Available', 'Unavailable', 'Suspended') DEFAULT 'Available' NOT NULL,
    last_donation_date DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. Table: blood_requests
-- ----------------------------------------------------------------------------
CREATE TABLE blood_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    quantity_ml INT NOT NULL CHECK (quantity_ml > 0),
    hospital_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    urgency_level ENUM('Normal', 'Urgent', 'Critical') DEFAULT 'Normal' NOT NULL,
    status ENUM('Pending', 'Matched', 'Fulfilled', 'Cancelled') DEFAULT 'Pending' NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4. Table: organ_requests
-- ----------------------------------------------------------------------------
CREATE TABLE organ_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL,
    organ_type ENUM('Kidney', 'Liver', 'Lung', 'Heart', 'Pancreas', 'Cornea') NOT NULL,
    hospital_name VARCHAR(150) NOT NULL,
    city VARCHAR(100) NOT NULL,
    urgency_level ENUM('Normal', 'Urgent', 'Critical') DEFAULT 'Normal' NOT NULL,
    status ENUM('Pending', 'Matched', 'Fulfilled', 'Cancelled') DEFAULT 'Pending' NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. Table: matches
-- ----------------------------------------------------------------------------
CREATE TABLE matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    blood_request_id INT DEFAULT NULL,
    organ_request_id INT DEFAULT NULL,
    match_type ENUM('Blood', 'Organ') NOT NULL,
    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Accepted', 'Rejected', 'Completed') DEFAULT 'Pending' NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (blood_request_id) REFERENCES blood_requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (organ_request_id) REFERENCES organ_requests(request_id) ON DELETE CASCADE,
    CONSTRAINT chk_match_request CHECK (
        (match_type = 'Blood' AND blood_request_id IS NOT NULL AND organ_request_id IS NULL) OR
        (match_type = 'Organ' AND blood_request_id IS NULL AND organ_request_id IS NOT NULL)
    )
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. Table: audit_log
-- ----------------------------------------------------------------------------
CREATE TABLE audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    match_id INT NOT NULL,
    donor_id INT NOT NULL,
    request_id INT NOT NULL,
    match_type ENUM('Blood', 'Organ') NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT NOT NULL
) ENGINE=InnoDB;


-- ============================================================================
-- VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW available_donors AS
SELECT 
    d.donor_id,
    u.name AS donor_name,
    d.blood_type,
    d.organs_willing_to_donate,
    d.city,
    d.availability_status,
    u.phone AS donor_phone,
    u.email AS donor_email
FROM donors d
JOIN users u ON d.user_id = u.user_id
WHERE d.availability_status = 'Available';


-- ============================================================================
-- TRIGGERS
-- ============================================================================

DELIMITER //

CREATE TRIGGER after_match_insert
AFTER INSERT ON matches
FOR EACH ROW
BEGIN
    DECLARE target_req_id INT;
    
    IF NEW.match_type = 'Blood' THEN
        SET target_req_id = NEW.blood_request_id;
    ELSE
        SET target_req_id = NEW.organ_request_id;
    END IF;

    INSERT INTO audit_log (action_type, match_id, donor_id, request_id, match_type, details)
    VALUES (
        'CREATE_MATCH',
        NEW.match_id,
        NEW.donor_id,
        target_req_id,
        NEW.match_type,
        CONCAT('A new ', LOWER(NEW.match_type), ' match was created. Match ID: ', NEW.match_id, 
               ', Donor ID: ', NEW.donor_id, ', Request ID: ', target_req_id, 
               ', Initial Status: ', NEW.status)
    );
END //

DELIMITER ;


-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

DELIMITER //

CREATE PROCEDURE FindCompatibleDonors(
    IN p_recipient_blood_type VARCHAR(5),
    IN p_city VARCHAR(100)
)
BEGIN
    SELECT 
        d.donor_id,
        u.name AS donor_name,
        d.blood_type AS donor_blood_type,
        d.organs_willing_to_donate,
        d.city,
        u.phone AS donor_phone,
        u.email AS donor_email
    FROM donors d
    JOIN users u ON d.user_id = u.user_id
    WHERE d.availability_status = 'Available'
      AND (p_city IS NULL OR LOWER(d.city) = LOWER(p_city))
      AND (
          p_recipient_blood_type = 'AB+'
          OR (p_recipient_blood_type = 'AB-' AND d.blood_type IN ('AB-', 'A-', 'B-', 'O-'))
          OR (p_recipient_blood_type = 'A+' AND d.blood_type IN ('A+', 'A-', 'O+', 'O-'))
          OR (p_recipient_blood_type = 'A-' AND d.blood_type IN ('A-', 'O-'))
          OR (p_recipient_blood_type = 'B+' AND d.blood_type IN ('B+', 'B-', 'O+', 'O-'))
          OR (p_recipient_blood_type = 'B-' AND d.blood_type IN ('B-', 'O-'))
          OR (p_recipient_blood_type = 'O+' AND d.blood_type IN ('O+', 'O-'))
          OR (p_recipient_blood_type = 'O-' AND d.blood_type = 'O-')
      )
    ORDER BY 
        CASE WHEN d.blood_type = p_recipient_blood_type THEN 0 ELSE 1 END,
        d.blood_type;
END //

DELIMITER ;


-- ============================================================================
-- DUMMY DATA
-- ============================================================================

INSERT INTO users (name, email, phone, password_hash, user_type) VALUES
('John Doe', 'john.doe@example.com', '9876543210', 'hashed_pass_1', 'Donor'),
('Jane Smith', 'jane.smith@example.com', '9876543211', 'hashed_pass_2', 'Donor'),
('Robert Johnson', 'robert.j@example.com', '9876543212', 'hashed_pass_3', 'Donor'),
('Alice Brown', 'alice.b@example.com', '9876543213', 'hashed_pass_4', 'Recipient'),
('Charlie Davis', 'charlie.d@example.com', '9876543214', 'hashed_pass_5', 'Recipient'),
('Emily Wilson', 'emily.w@example.com', '9876543215', 'hashed_pass_6', 'Donor'),
('Frank Miller', 'frank.m@example.com', '9876543216', 'hashed_pass_7', 'Recipient'),
('Admin User', 'admin@donorfinder.com', '9876543200', 'hashed_pass_admin', 'Admin');

INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date) VALUES
(1, 'O-', 'Kidney,Cornea', 'Mumbai', 'Available', '2026-01-15'),
(2, 'A+', 'Liver,Lung', 'Delhi', 'Available', '2026-02-10'),
(3, 'B+', 'Heart,Kidney', 'Mumbai', 'Unavailable', '2025-12-05'),
(6, 'AB+', 'Kidney,Liver,Lung,Heart,Pancreas,Cornea', 'Mumbai', 'Available', NULL);

INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status) VALUES
(4, 'A+', 450, 'City Heart Hospital', 'Delhi', 'Urgent', 'Pending'),
(5, 'O+', 900, 'Metro General Hospital', 'Mumbai', 'Critical', 'Pending');

INSERT INTO organ_requests (recipient_id, organ_type, hospital_name, city, urgency_level, status) VALUES
(7, 'Kidney', 'Apex Multi-speciality', 'Mumbai', 'Critical', 'Pending');

INSERT INTO matches (donor_id, organ_request_id, match_type, status) VALUES
(1, 1, 'Organ', 'Pending');
