"""
Database Module - SQLite Database Management for Veterinarian Clinic System.

This module handles all database operations for the vet clinic including:
- Patient records (name, species, breed, age, owner information)
- Doctor information (name, specialization, consultation fees)
- Appointment scheduling and management
- Diagnosis records linked to appointments
- Medication prescriptions
- Medicine inventory and stock management

Features:
- Automatic table creation on first run
- Foreign key constraints for data integrity
- Auto-generated IDs for all records
- Pre-loaded specialty doctors and general veterinarians
- Migration support for adding new columns to existing databases
- Connection pooling to reuse database connections
- Row factory for easy dictionary-style access to query results

Database File: vet_clinic.db (stored in same directory as this module)
"""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name('vet_clinic.db')


class Database:
    """SQLite database management class for veterinarian clinic operations."""
    
    _conn = None
    
    @classmethod
    def get_connection(cls):
        """Get or create database connection and initialize tables."""
        if cls._conn is None:
            cls._conn = sqlite3.connect(str(DB_FILE))
            cls._conn.row_factory = sqlite3.Row
            cls._setup_tables()
        return cls._conn
    
    @classmethod
    def _setup_tables(cls):
        """Create database tables and load initial doctor data if database is new."""
        cur = cls._conn.cursor()
        cur.executescript('''
            PRAGMA foreign_keys = ON;
            
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, species TEXT, breed TEXT, age INTEGER,
                owner_name TEXT, owner_contact TEXT, notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, specialization TEXT, fee REAL NOT NULL DEFAULT 0.0
            );
            
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                patient_id INTEGER, doctor_id INTEGER,
                date TEXT, time TEXT, status TEXT, notes TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(doctor_id) REFERENCES doctors(id)
            );
            
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL,
                patient_id INTEGER,
                doctor_id INTEGER,
                diagnosis_text TEXT,
                diagnosis_date TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(appointment_id) REFERENCES appointments(id)
            );

            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diagnosis_id INTEGER NOT NULL,
                medicine_name TEXT,
                quantity INTEGER DEFAULT 1,
                price REAL DEFAULT 0.0,
                FOREIGN KEY(diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                stock INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0,
                form TEXT,
                use TEXT,
                supplier_name TEXT,
                supplier_contact TEXT
            );
        ''')

        # Migration: Add missing columns to medicines table if they don't exist
        try:
            cur.execute("PRAGMA foreign_keys=OFF")
            cols = [r[1] for r in cur.execute("PRAGMA table_info(medicines)").fetchall()]
            if 'form' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN form TEXT")
            if 'use' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN use TEXT")
            cls._conn.commit()
            cur.execute("PRAGMA foreign_keys=ON")
        except Exception as e:
            try:
                cur.execute("PRAGMA foreign_keys=ON")
            except:
                pass

        # Load initial specialty doctors if database is new
        if not cur.execute("SELECT * FROM doctors").fetchone():
            cur.executemany(
                "INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)",
                [
                    ('Dr. Sarah Geronimo', 'Nutrition', 3500.00),
                    ('Dr. Carlos Garcia', 'Grooming', 2500.00),
                    ('Dr. Princess Valdez', 'Surgery', 15000.00),
                    ('Dr. Robert Tuazon', 'Dentistry', 5000.00),
                    ('Dr. Lisa Badlis', 'Ophthalmology', 4500.00),
                    ('Dr. James Villaluna', 'Dermatology', 5000.00)
                ]
            )
            cls._conn.commit()
        
        # Ensure general veterinarians are present
        general_doctors = [
            ('Dr. Miguel Santos', 'General Veterinarian', 1500.00),
            ('Dr. Katrina Dela Cruz', 'General Veterinarian', 1500.00),
            ('Dr. Jerome Bautista', 'General Veterinarian', 1500.00),
        ]
        for name, spec, fee in general_doctors:
            if not cur.execute("SELECT id FROM doctors WHERE name = ?", (name,)).fetchone():
                cur.execute("INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)", (name, spec, fee))
            else:
                cur.execute("UPDATE doctors SET fee = ? WHERE name = ?", (fee, name))
        cls._conn.commit()
        cur.close()
    
    @classmethod
    def query(cls, sql, params=()):
        """Execute SELECT query and return all results."""
        return cls.get_connection().execute(sql, params).fetchall()
    
    @classmethod
    def execute(cls, sql, params=()):
        """Execute INSERT, UPDATE, or DELETE query and commit changes."""
        cls.get_connection().execute(sql, params)
        cls.get_connection().commit()
        
    @classmethod
    def execute_returning_id(cls, sql, params=()):
        """Execute INSERT query and return the auto-generated ID of the new row."""
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
