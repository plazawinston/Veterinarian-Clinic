# 🏥 Veterinary Clinic Management System

A comprehensive desktop application built with Python for managing veterinary clinic operations, including patient records, appointments, diagnoses, medications, and invoicing.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Module Overview](#module-overview)
- [Default Credentials](#default-credentials)
- [Database Schema](#database-schema)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

## Features

### Core Functionality

- ** Secure Login System** - Protected access with user authentication
- ** Interactive Dashboard** - Real-time overview of clinic statistics and today's appointments
- ** Patient Management** - Comprehensive pet and owner records with search and filtering
- ** Appointment Scheduling** - Calendar-based scheduling with conflict detection
- ** Diagnosis & Treatment** - Medical records with diagnosis tracking and medication prescriptions
- ** Medicine Inventory** - Stock management with supplier information
- ** Doctor View** - Personalized view for veterinarians with appointment calendar
- ** Report Generation** - Client visit history and clinic statistics
- ** Invoice Generation** - Professional invoices with service and medication breakdowns

##  System Requirements

### Software Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux

### Required Python Packages

```
customtkinter
tkcalendar
sqlite3 (included with Python)
```

##  Installation

### Step 1: Install Python

Download and install Python from [python.org](https://www.python.org/downloads/)

### Step 2: Install Dependencies

```bash
pip install customtkinter tkcalendar
```

### Step 3: Download the Application

Clone or download all the project files to a single directory:

```
vet_clinic/
├── main.py
├── login.py
├── database.py
├── dashboard.py
├── patients.py
├── appointments.py
├── diagnosis.py
├── medicine.py
├── doctor.py
├── report.py
└── invoice.py
```

### Step 4: Run the Application

```bash
python main.py
```

## Getting Started

### First Launch

1. Run `python main.py`
2. The database (`vet_clinic.db`) will be created automatically
3. Sample doctors will be pre-loaded
4. Use default credentials to log in (see below)

### Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `vet2106`

## Module Overview

### 1. Dashboard (`dashboard.py`)

**Purpose:** Provides a quick overview of clinic operations

**Features:**
- Total patient count
- Today's appointment count
- Active doctor count
- List of today's appointments with status indicators

### 2. Patient Management (`patients.py`)

**Purpose:** Manage pet patient records and owner information

**Features:**
- Add, edit, and delete patient records
- Search by patient name or owner name
- Filter by species
- Track patient details: name, species, breed, age, owner information, notes
- Input validation for numeric fields

**Key Functions:**
- `show_patients_view()` - Main patient management interface
- `Patient.save()` - Create or update patient records
- `Patient.delete()` - Remove patient records
- `Patient.list_all()` - Search and filter patients

### 3. Appointment Scheduling (`appointments.py`)

**Purpose:** Schedule and manage veterinary appointments

**Features:**
- Interactive calendar with date highlighting
- Visual status indicators (scheduled, completed, cancelled)
- Conflict detection (prevents double-booking)
- Time slot management
- Appointment notes
- Prevents scheduling in the past

**Key Functions:**
- `Appointment.save()` - Create or update appointments
- `Appointment.delete()` - Remove appointments
- `Appointment.cancel()` - Cancel appointments
- `Appointment.conflict_exists()` - Check for scheduling conflicts

**Appointment Status:**
-  **Completed** - Appointment finished
-  **Scheduled** - Upcoming appointment
-  **Cancelled** - Appointment cancelled

### 4. Diagnosis & Medication (`diagnosis.py`)

**Purpose:** Record diagnoses and prescribe medications

**Features:**
- Link diagnoses to completed appointments
- Medication prescription with inventory integration
- Automatic stock deduction
- Medical certificate generation
- Medication browser for easy selection
- Price and quantity tracking

**Key Functions:**
- `Diagnosis.save()` - Save diagnosis records
- `Medication.save()` - Prescribe medications
- `print_medical_certificate()` - Generate printable certificates

**Workflow:**
1. Select a completed appointment
2. Enter diagnosis
3. Save diagnosis
4. Add medications (automatically deducts from inventory)
5. Generate medical certificate

### 5. Medicine Inventory (`medicine.py`)

**Purpose:** Manage medication stock and suppliers

**Features:**
- Medicine registration with details (name, stock, price, form, use)
- Supplier information tracking
- Stock level monitoring
- Search and filter functionality
- Sample medicine loader

**Medicine Forms:**
- Tablet
- Injection
- Syrup
- Cream
- Ointment
- Drops
- Suppository
- Other

**Key Functions:**
- `Medicine.save()` - Add or update medicine records
- `Medicine.delete()` - Remove medicines
- `Medicine.list_all()` - View all medicines

### 6. Doctor View (`doctor.py`)

**Purpose:** Personalized view for veterinarians

**Features:**
- Select doctor from dropdown
- Color-coded appointment calendar:
  -  Green: Completed appointments
  -  Yellow: Upcoming appointments
- Day-by-day appointment details
- Patient and appointment information

### 7. Reports (`report.py`)

**Purpose:** Generate client history and statistics

**Features:**
- Client search functionality
- Completed appointment history per pet
- Clinic statistics dashboard
- Top clients by visit count
- Export reports to text files

**Report Types:**
- Individual client reports
- All clients with completed appointments
- Clinic-wide statistics

### 8. Invoice Generation (`invoice.py`)

**Purpose:** Create professional invoices for services

**Features:**
- Multi-appointment invoice generation
- Service fee breakdown
- Medication cost itemization
- Grand total calculation
- Export to printable text format

**Invoice Includes:**
- Client information
- Appointment details
- Doctor's fees
- Prescribed medications
- Diagnosis summary
- Total costs

## 🗄️ Database Schema

The application uses SQLite with the following tables:

### Patients Table
```sql
- id (PRIMARY KEY)
- name
- species
- breed
- age
- owner_name
- owner_contact
- notes
```

### Doctors Table
```sql
- id (PRIMARY KEY)
- name
- specialization
- fee
```

**Pre-loaded Doctors:**
- Dr. Sarah Geronimo (Nutrition) - ₱3,500
- Dr. Carlos Garcia (Grooming) - ₱2,500
- Dr. Princess Valdez (Surgery) - ₱15,000
- Dr. Robert Tuazon (Dentistry) - ₱5,000
- Dr. Lisa Badlis (Ophthalmology) - ₱4,500
- Dr. James Villaluna (Dermatology) - ₱5,000
- Dr. Miguel Santos (General Veterinarian) - ₱1,500
- Dr. Katrina Dela Cruz (General Veterinarian) - ₱1,500
- Dr. Jerome Bautista (General Veterinarian) - ₱1,500

### Appointments Table
```sql
- id (PRIMARY KEY)
- patient_id (FOREIGN KEY)
- doctor_id (FOREIGN KEY)
- date
- time
- status
- notes
```

### Diagnoses Table
```sql
- id (PRIMARY KEY)
- appointment_id (FOREIGN KEY)
- patient_id
- doctor_id
- diagnosis_text
- diagnosis_date
- created_at
```

### Medications Table
```sql
- id (PRIMARY KEY)
- diagnosis_id (FOREIGN KEY)
- medicine_name
- quantity
- price
```

### Medicines Table
```sql
- id (PRIMARY KEY)
- name (UNIQUE)
- stock
- price
- form
- use
- supplier_name
- supplier_contact
```

## 📖 Usage Guide

### Adding a New Patient

1. Navigate to **Patients** module
2. Click **New** to clear the form
3. Enter patient details (Name and Owner Name are required)
4. Click **Save**

### Scheduling an Appointment

1. Navigate to **Appointments** module
2. Select a date from the calendar
3. Choose patient and doctor from dropdowns
4. Select time slot
5. Add notes if needed
6. Click **Save**

**Note:** The system prevents double-booking and scheduling in the past.

### Recording a Diagnosis

1. Navigate to **Diagnosis & Medication** module
2. Search for completed appointments
3. Click on an appointment card
4. Enter diagnosis in the text area
5. Click **Save Diagnosis**
6. Select medicines from the browser
7. Enter quantity (price auto-fills)
8. Click **Add Medication**
9. Click **Print Certificate** to generate medical certificate

### Generating an Invoice

1. Navigate to **Invoices** module
2. Search for a client by name or contact
3. Select appointments to include (checkboxes)
4. Click **Generate Invoice**
5. Review the invoice preview
6. Click **Save & Print** to export

### Managing Medicine Inventory

1. Navigate to **Medicines** module
2. Click **New** to add new medicine
3. Enter medicine details (name, stock, price, form, use)
4. Add supplier information
5. Click **Save**

##  UI Elements

### Color Coding

- **Blue (#3498db)** - Primary actions, headers
- **Green (#2ecc71)** - Save, completed status
- **Yellow (#f39c12)** - Scheduled status
- **Red (#e74c3c)** - Delete, cancel actions
- **Purple (#9b59b6)** - Special features
- **Orange (#e67e22)** - Medications, export

### Status Indicators

- Completed
- Scheduled
- Cancelled
- Has Diagnosis
- No Diagnosis

## 📝 File Structure

```
vet_clinic/
├── main.py                  # Application entry point
├── login.py                 # Authentication module
├── database.py              # Database management
├── dashboard.py             # Dashboard module
├── patients.py              # Patient management
├── appointments.py          # Appointment scheduling
├── diagnosis.py             # Diagnosis and medications
├── medicine.py              # Medicine inventory
├── doctor.py                # Doctor view
├── report.py                # Report generation
├── invoice.py               # Invoice generation
├── vet_clinic.db            # SQLite database (auto-created)
├── invoice_*.txt            # Generated invoices
└── medical_certificate_*.txt # Generated certificates
```


## License

This is a clinic management system for educational and internal use.

## Updates

**Current Version:** 1.0

**Recent Improvements:**
- Added medicine inventory management
- Implemented diagnosis-medication integration
- Enhanced invoice generation with medications
- Added medical certificate printing
- Improved conflict detection for appointments
- Added past date prevention for scheduling
