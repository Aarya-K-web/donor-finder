-- ============================================================================
-- Blood & Organ Donor Finder Database Schema
-- DBMS Project (MySQL)
-- Designed for College Submission
-- ============================================================================
-- Description:
-- This SQL script creates the full database schema for a Blood and Organ Donor
-- Finder system. It includes tables for users, donors, blood requests, organ 
-- requests, matches, and audit logs. It also implements constraints, a trigger 
-- for automatic auditing, a view for available donors, a stored procedure 
-- for blood compatibility matching, and sample test data.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS blood_organ_donor_db;
USE blood_organ_donor_db;

-- ----------------------------------------------------------------------------
-- 1. Table: users
-- ----------------------------------------------------------------------------
-- Holds basic authentication and profile information for all types of users.
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Storing hashed passwords for security
    user_type ENUM('Donor', 'Recipient', 'Admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. Table: donors
-- ----------------------------------------------------------------------------
-- Stores detailed donor-specific profiles. Links to the users table.
-- Uses SET datatype to represent multiple organs a donor is willing to donate.
-- ----------------------------------------------------------------------------
CREATE TABLE donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE, -- One-to-one relationship with users
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
-- Tracks requests made for blood transfusions by recipients/patients.
-- ----------------------------------------------------------------------------
CREATE TABLE blood_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL, -- Foreign key to users
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
-- Tracks requests made for organ transplants by recipients/patients.
-- ----------------------------------------------------------------------------
CREATE TABLE organ_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL, -- Foreign key to users
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
-- Records successful matches between donors and requests.
-- Includes CHECK constraint to ensure a match links to either a blood request 
-- or an organ request, but never both, ensuring data integrity.
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
-- Audit table to automatically log matches via a trigger.
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

-- ----------------------------------------------------------------------------
-- View: available_donors
-- ----------------------------------------------------------------------------
-- Displays details of only active and currently available blood & organ donors
-- along with their contact information to facilitate quick search.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- Trigger: after_match_insert
-- ----------------------------------------------------------------------------
-- Automatically executes on every new INSERT into the matches table.
-- Resolves the correct request ID and logs the audit event into audit_log.
-- ----------------------------------------------------------------------------
DELIMITER //

CREATE TRIGGER after_match_insert
AFTER INSERT ON matches
FOR EACH ROW
BEGIN
    DECLARE target_req_id INT;
    
    -- Identify the relevant request ID based on match type
    IF NEW.match_type = 'Blood' THEN
        SET target_req_id = NEW.blood_request_id;
    ELSE
        SET target_req_id = NEW.organ_request_id;
    END IF;

    -- Insert record into audit log
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

-- ----------------------------------------------------------------------------
-- Procedure: FindCompatibleDonors
-- ----------------------------------------------------------------------------
-- Finds all available and blood-compatible donors for a given patient's
-- blood type in a specific city. 
-- Implements complete, standard medical blood compatibility rules:
--   - O- is universal donor (can donate to anyone).
--   - AB+ is universal recipient (can receive from anyone).
-- ----------------------------------------------------------------------------
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
          -- AB+ Recipient can receive from all blood types
          p_recipient_blood_type = 'AB+'
          
          -- AB- Recipient can receive from AB-, A-, B-, O-
          OR (p_recipient_blood_type = 'AB-' AND d.blood_type IN ('AB-', 'A-', 'B-', 'O-'))
          
          -- A+ Recipient can receive from A+, A-, O+, O-
          OR (p_recipient_blood_type = 'A+' AND d.blood_type IN ('A+', 'A-', 'O+', 'O-'))
          
          -- A- Recipient can receive from A-, O-
          OR (p_recipient_blood_type = 'A-' AND d.blood_type IN ('A-', 'O-'))
          
          -- B+ Recipient can receive from B+, B-, O+, O-
          OR (p_recipient_blood_type = 'B+' AND d.blood_type IN ('B+', 'B-', 'O+', 'O-'))
          
          -- B- Recipient can receive from B-, O-
          OR (p_recipient_blood_type = 'B-' AND d.blood_type IN ('B-', 'O-'))
          
          -- O+ Recipient can receive from O+, O-
          OR (p_recipient_blood_type = 'O+' AND d.blood_type IN ('O+', 'O-'))
          
          -- O- Recipient can receive only from O-
          OR (p_recipient_blood_type = 'O-' AND d.blood_type = 'O-')
      )
    ORDER BY 
        -- Prioritize exact blood type matches first, then sort by blood type
        CASE WHEN d.blood_type = p_recipient_blood_type THEN 0 ELSE 1 END,
        d.blood_type;
END //

DELIMITER ;


-- ============================================================================
-- DUMMY DATA FOR DEMONSTRATION & TESTING
-- ============================================================================

-- Insert Test Users (Donors, Recipients, and Admins)
INSERT INTO users (name, email, phone, password_hash, user_type) VALUES
('John Doe', 'john.doe@example.com', '9876543210', 'hashed_pass_1', 'Donor'),
('Jane Smith', 'jane.smith@example.com', '9876543211', 'hashed_pass_2', 'Donor'),
('Robert Johnson', 'robert.j@example.com', '9876543212', 'hashed_pass_3', 'Donor'),
('Alice Brown', 'alice.b@example.com', '9876543213', 'hashed_pass_4', 'Recipient'),
('Charlie Davis', 'charlie.d@example.com', '9876543214', 'hashed_pass_5', 'Recipient'),
('Emily Wilson', 'emily.w@example.com', '9876543215', 'hashed_pass_6', 'Donor'),
('Frank Miller', 'frank.m@example.com', '9876543216', 'hashed_pass_7', 'Recipient'),
('Admin User', 'admin@donorfinder.com', '9876543200', 'hashed_pass_admin', 'Admin');

-- Insert Test Donors corresponding to users (with blood type, organs, city, availability)
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date) VALUES
(1, 'O-', 'Kidney,Cornea', 'Mumbai', 'Available', '2026-01-15'),  -- John Doe (Universal Blood Donor, willing to donate Kidney and Cornea)
(2, 'A+', 'Liver,Lung', 'Delhi', 'Available', '2026-02-10'),      -- Jane Smith
(3, 'B+', 'Heart,Kidney', 'Mumbai', 'Unavailable', '2025-12-05'),  -- Robert Johnson (Not available currently)
(6, 'AB+', 'Kidney,Liver,Lung,Heart,Pancreas,Cornea', 'Mumbai', 'Available', NULL); -- Emily Wilson (Universal blood recipient but can donate to AB+)

-- Insert Blood Requests (Recipient ID, Blood Type, Quantity, Hospital, City, Urgency, Status)
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status) VALUES
(4, 'A+', 450, 'City Heart Hospital', 'Delhi', 'Urgent', 'Pending'),      -- Alice Brown needs A+ in Delhi
(5, 'O+', 900, 'Metro General Hospital', 'Mumbai', 'Critical', 'Pending'); -- Charlie Davis needs O+ in Mumbai

-- Insert Organ Requests (Recipient ID, Organ Type, Hospital, City, Urgency, Status)
INSERT INTO organ_requests (recipient_id, organ_type, hospital_name, city, urgency_level, status) VALUES
(7, 'Kidney', 'Apex Multi-speciality', 'Mumbai', 'Critical', 'Pending'); -- Frank Miller needs Kidney in Mumbai

-- Insert a test Match to verify the Trigger and Foreign Keys
-- John Doe (Donor ID: 1, willing to donate Kidney in Mumbai) matches Frank Miller's Kidney Request (Organ Request ID: 1)
INSERT INTO matches (donor_id, organ_request_id, match_type, status) VALUES
(1, 1, 'Organ', 'Pending');

-- ============================================================================
-- VERIFICATION COMMANDS (For Professor's execution/verification)
-- ============================================================================
-- Run the following queries to test components after importing the schema:
--
-- 1. View all available donors:
--    SELECT * FROM available_donors;
--
-- 2. Verify that the match trigger successfully inserted into the audit log:
--    SELECT * FROM audit_log;
--
-- 3. Execute the stored procedure to find compatible blood donors for Charlie (O+ in Mumbai):
--    CALL FindCompatibleDonors('O+', 'Mumbai');
--
-- 4. Execute the stored procedure to find compatible blood donors in Delhi (should show Jane Smith):
--    CALL FindCompatibleDonors('A+', 'Delhi');
-- ============================================================================
