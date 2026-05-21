-- ============================================================================
-- Blood & Organ Donor Finder - Realistic Sample Data INSERTs
-- DBMS Project (MySQL)
-- Designed for College Submission
-- ============================================================================
-- Description:
-- This SQL script inserts 15 realistic donors (with corresponding users) and 
-- 5 emergency blood requests. It maintains complete relational integrity using
-- the LAST_INSERT_ID() function to link tables dynamically.
-- ============================================================================

USE blood_organ_donor_db;

-- ----------------------------------------------------------------------------
-- PART 1: 15 Realistic Donors (Users + Donors profiles)
-- ----------------------------------------------------------------------------

-- 1. Rajesh Kumar (Mumbai, A+, Available, Kidney & Liver)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Rajesh Kumar', 'rajesh.kumar@example.com', '9812345670', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'A+', 'Kidney,Liver', 'Mumbai', 'Available', '2026-03-01');

-- 2. Sneha Patil (Pune, O-, Available, Cornea)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Sneha Patil', 'sneha.patil@example.com', '9823456781', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'O-', 'Cornea', 'Pune', 'Available', '2026-02-15');

-- 3. Arjun Mehta (Delhi, B+, Unavailable, Heart & Lung)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Arjun Mehta', 'arjun.mehta@example.com', '9834567892', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'B+', 'Heart,Lung', 'Delhi', 'Unavailable', '2025-12-10');

-- 4. Pooja Hegde (Bangalore, AB+, Available, Kidney, Liver & Cornea)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Pooja Hegde', 'pooja.hegde@example.com', '9845678903', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'AB+', 'Kidney,Liver,Cornea', 'Bangalore', 'Available', NULL);

-- 5. Rohan Deshmukh (Mumbai, A-, Available, Blood Only)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Rohan Deshmukh', 'rohan.deshmukh@example.com', '9856789014', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'A-', NULL, 'Mumbai', 'Available', '2026-01-20');

-- 6. Neha Gupta (Pune, B-, Available, Liver)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Neha Gupta', 'neha.gupta@example.com', '9867890125', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'B-', 'Liver', 'Pune', 'Available', '2026-04-05');

-- 7. Vikram Malhotra (Delhi, O+, Unavailable, Kidney)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Vikram Malhotra', 'vikram.m@example.com', '9878901236', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'O+', 'Kidney', 'Delhi', 'Unavailable', '2025-11-30');

-- 8. Ananya Bhat (Bangalore, AB-, Available, Cornea & Lung)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Ananya Bhat', 'ananya.bhat@example.com', '9889012347', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'AB-', 'Cornea,Lung', 'Bangalore', 'Available', NULL);

-- 9. Sanjay Rao (Mumbai, B+, Available, Blood Only)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Sanjay Rao', 'sanjay.rao@example.com', '9890123458', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'B+', NULL, 'Mumbai', 'Available', '2026-03-25');

-- 10. Deepa Nair (Pune, A+, Available, Kidney & Pancreas)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Deepa Nair', 'deepa.nair@example.com', '9801234569', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'A+', 'Kidney,Pancreas', 'Pune', 'Available', NULL);

-- 11. Aditya Sen (Delhi, O-, Available, Cornea)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Aditya Sen', 'aditya.sen@example.com', '9712345678', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'O-', 'Cornea', 'Delhi', 'Available', '2026-02-28');

-- 12. Meera Iyer (Bangalore, B-, Unavailable, Heart)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Meera Iyer', 'meera.iyer@example.com', '9723456789', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'B-', 'Heart', 'Bangalore', 'Unavailable', '2025-10-15');

-- 13. Yash Vardhan (Mumbai, AB+, Available, Liver & Kidney)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Yash Vardhan', 'yash.vardhan@example.com', '9734567890', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'AB+', 'Kidney,Liver', 'Mumbai', 'Available', '2026-04-10');

-- 14. Tanvi Joshi (Pune, O+, Available, Blood Only)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Tanvi Joshi', 'tanvi.joshi@example.com', '9745678901', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'O+', NULL, 'Pune', 'Available', '2026-03-12');

-- 15. Kunal Shah (Delhi, A-, Available, Kidney & Cornea)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Kunal Shah', 'kunal.shah@example.com', '9756789012', 'password123', 'Donor');
INSERT INTO donors (user_id, blood_type, organs_willing_to_donate, city, availability_status, last_donation_date)
VALUES (LAST_INSERT_ID(), 'A-', 'Kidney,Cornea', 'Delhi', 'Available', NULL);


-- ----------------------------------------------------------------------------
-- PART 2: 5 Sample Blood Requests (Users + Blood Requests profiles)
-- ----------------------------------------------------------------------------

-- 1. Karan Sharma (Mumbai, B+, 450ml, Critical, Lilavati Hospital)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Karan Sharma', 'karan.sharma@example.com', '9112345601', 'password123', 'Recipient');
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status)
VALUES (LAST_INSERT_ID(), 'B+', 450, 'Lilavati Hospital', 'Mumbai', 'Critical', 'Pending');

-- 2. Sunita Rao (Pune, O-, 900ml, Urgent, KEM Hospital)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Sunita Rao', 'sunita.rao@example.com', '9123456702', 'password123', 'Recipient');
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status)
VALUES (LAST_INSERT_ID(), 'O-', 900, 'KEM Hospital', 'Pune', 'Urgent', 'Pending');

-- 3. Amit Verma (Delhi, A+, 300ml, Normal, Max Healthcare)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Amit Verma', 'amit.verma@example.com', '9134567803', 'password123', 'Recipient');
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status)
VALUES (LAST_INSERT_ID(), 'A+', 300, 'Max Healthcare', 'Delhi', 'Normal', 'Pending');

-- 4. Preeti Shenoy (Bangalore, AB-, 600ml, Critical, Fortis Hospital)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Preeti Shenoy', 'preeti.shenoy@example.com', '9145678904', 'password123', 'Recipient');
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status)
VALUES (LAST_INSERT_ID(), 'AB-', 600, 'Fortis Hospital', 'Bangalore', 'Critical', 'Pending');

-- 5. Vijay Mallya (Mumbai, O+, 450ml, Urgent, Apollo Hospital)
INSERT INTO users (name, email, phone, password_hash, user_type)
VALUES ('Vijay Mallya', 'vijay.mallya@example.com', '9156789005', 'password123', 'Recipient');
INSERT INTO blood_requests (recipient_id, blood_type, quantity_ml, hospital_name, city, urgency_level, status)
VALUES (LAST_INSERT_ID(), 'O+', 450, 'Apollo Hospital', 'Mumbai', 'Urgent', 'Pending');
