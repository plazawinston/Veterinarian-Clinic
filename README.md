Vet Clinic Management System

A comprehensive veterinary clinic management application built with **Python** and **CustomTkinter**. This desktop application helps manage patients (pets), appointments, client reports, and professional invoice generation with a modern, user-friendly interface.

Features

Core Modules

Dashboard
- Overview of clinic statistics (Total Pets, Pet Owners, Appointments)
- Today's appointment schedule
- Real-time clinic overview

Patient Management
- Register and manage pet records
- Store owner information (name, contact details)
- Track pet details (species, breed, age)
- Medical notes and history
- Search patients by name or owner

####Appointment Scheduling
- Interactive calendar interface
- Schedule appointments with pets and veterinarians
- Manage appointment status (scheduled, completed, cancelled)
- View appointments by date
- Track appointment notes and reasons

Client History Reports
- Generate comprehensive client reports
- View complete pet and appointment history
- Calculate total visits and spending
- Export reports to text files
- Search by owner name or contact

Invoice Generation
- Create professional invoices
- Select multiple appointments for billing
- Auto-generated invoice numbers with timestamps
- Detailed breakdown by pet and service
- Save invoices as text files

Getting Started

System Requirements
- Python 3.11+
- CustomTkinter 5.2.2
- tkcalendar 1.6.1
- SQLite3 (built-in with Python)

Installation

1. Install dependencies:
   ```bash
   pip install customtkinter tkcalendar
   ```

2. Run the application:
   ```bash
   python main.py
   ```

### Login

When the application starts, you'll see a login screen:

Default Credentials:
- Username: admin
- Password: vet2106


```

 Project Structure

```
.
├── main.py                  # Application entry point
├── login.py                 # Authentication system
├── database.py              # Database management & schema
├── dashboard.py             # Dashboard module
├── patients.py              # Patient management module
├── appointments.py          # Appointment scheduling module
├── report.py                # Report generation module
├── invoice.py               # Invoice generation module
├── vet_clinic.db            # SQLite database
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

 Database Schema

patients
- `id` (PK) - Unique patient identifier
- `name` - Pet name
- `species` - Pet species
- `breed` - Pet breed
- `age` - Pet age in years
- `owner_name` - Owner's name
- `owner_contact` - Owner's phone/email
- `notes` - Medical notes

doctors
- `id` (PK) - Unique doctor identifier
- `name` - Doctor's name
- `specialization` - Area of specialization
- `fee` - Consultation fee

appointments
- `id` (PK) - Unique appointment identifier
- `patient_id` (FK) - References patients table
- `doctor_id` (FK) - References doctors table
- `date` - Appointment date (YYYY-MM-DD)
- `time` - Appointment time (HH:MM)
- `status` - scheduled/completed/cancelled
- `notes` - Appointment notes

How to Use

Dashboard
1. Select "Dashboard" from the sidebar
2. View clinic statistics and today's appointments at a glance

Managing Patients
1. Click "Patients" in the sidebar
2. Search for existing patients or create new ones
3. Enter pet and owner information
4. Click "Save" to store the record

Scheduling Appointments
1. Click "Appointments" in the sidebar
2. Select a date from the calendar
3. Choose pet, doctor, time, and status
4. Add notes if needed
5. Click "Save" to schedule

Generating Reports
1. Click "Reports" in the sidebar
2. Search for a client by name or phone
3. View their pet list and appointment history
4. Click "Export Report" to save as text file

### Creating Invoices
1. Click "Invoices" in the sidebar
2. Search for and select a client
3. Choose appointments to include
4. Click "Preview" to see the invoice
5. Click "Save Invoice" to export

User Interface

- **Professional Design** - Clean, modern interface with intuitive navigation
- **Color-Coded Sections** - Each module has its own color theme
- **Responsive Layout** - Adapts to different screen sizes
- **Interactive Calendar** - Easy date selection for appointments
- **Real-time Updates** - All changes reflect immediately

Currency

All monetary values are displayed in **Philippine Peso (₱)**

Export Formats

- **Reports:** Text files (.txt)
- **Invoices:** Text files (.txt)
- **Naming Convention:** `report_YYYYMMDD_HHMMSS.txt`, `invoice_YYYYMMDD_HHMMSS.txt`

Security

- Login authentication with credentials file
- User sessions managed per login
- Database stored locally with SQLite

Development

Dependencies

| Package       | Version | Purpose              |
|---------------|---------|----------------------|
| customtkinter | 5.2.2   | Modern UI framework  |
| tkcalendar    | 1.6.1   | Calendar widget      |
| sqlite3       | Built-in | Database management |

Key Features

- OOP Architecture - Modular design with separate concerns
- Database Abstraction - SQL operations through Database class
- Dynamic UI - Responsive layout with CustomTkinter
- Data Persistence - SQLite for reliable data storage

Pre-populated Data

The database comes with 6 sample veterinarians:

[
                    ('Dr. Sarah Geronimo', 'Nutrition', 3500.00),
                    ('Dr. Carlos Garcia', 'Grooming', 2500.00),
                    ('Dr. Princess Valdez', 'Surgery', 1500.00),
                    ('Dr. Robert Tuazon', 'Dentistry', 5000.00),
                    ('Dr. Lisa Badlis', 'Ophthalmology', 4500.00),
                    ('Dr. James Villaluna', 'Dermatology', 5000.00)
                ]

License

This project is for project purposes only.

---

**Last Updated:** November 24, 2025
**Version:** 1.0
**Built with:** Python 3.11 + CustomTkinter
