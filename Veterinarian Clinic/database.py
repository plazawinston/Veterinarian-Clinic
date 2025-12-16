"""
CLASS: 1
"""
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name('vet_clinic.db')

## Lightweight SQLite database wrapper used across modules
class Database:
    _conn = None
    
    ## Obtain a singleton DB connection, initializing schema if needed
    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            cls._conn = sqlite3.connect(str(DB_FILE))
            cls._conn.row_factory = sqlite3.Row
            cls._setup_tables()
        return cls._conn
    
    @classmethod
    ## Internal: create required tables and perform simple migrations
    def _setup_tables(cls):
        cur = cls._conn.cursor()
        cur.executescript('''
            PRAGMA foreign_keys = ON;
            
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, species TEXT, breed TEXT, age INTEGER,
                owner_name TEXT, owner_contact TEXT, notes TEXT,
                is_deleted INTEGER DEFAULT 0
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
                    supplier_name TEXT,
                    supplier_contact TEXT
                );
            
                CREATE TABLE IF NOT EXISTS recent_deleted (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    name TEXT,
                    species TEXT,
                    breed TEXT,
                    age INTEGER,
                    owner_name TEXT,
                    owner_contact TEXT,
                    notes TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
        ''')

        # If the database existed before this migration, ensure `form` column exists
        try:
            cols = [r[1] for r in cur.execute("PRAGMA table_info(medicines)").fetchall()]
            if 'form' not in cols:
                cur.execute("ALTER TABLE medicines ADD COLUMN form TEXT")
                cls._conn.commit()
        except Exception:
            # If table does not exist yet or PRAGMA fails, ignore — table creation above will handle it
            pass

        # Ensure patients table has is_deleted column on older DBs
        try:
            pcols = [r[1] for r in cur.execute("PRAGMA table_info(patients)").fetchall()]
            if 'is_deleted' not in pcols:
                cur.execute("ALTER TABLE patients ADD COLUMN is_deleted INTEGER DEFAULT 0")
                cls._conn.commit()
        except Exception:
            pass

        ## Seed default doctors if table is empty
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
        # Ensure requested General Veterinarians are present (idempotent)
        general_doctors = [
            ('Dr. Miguel Santos', 'General Veterinarian', 1500.00),
            ('Dr. Katrina Dela Cruz', 'General Veterinarian', 1500.00),
            ('Dr. Jerome Bautista', 'General Veterinarian', 1500.00),
        ]
        for name, spec, fee in general_doctors:
            if not cur.execute("SELECT id FROM doctors WHERE name = ?", (name,)).fetchone():
                cur.execute("INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)", (name, spec, fee))
            else:
                # ensure fee is set to requested value (lower price enforcement)
                cur.execute("UPDATE doctors SET fee = ? WHERE name = ?", (fee, name))
        cls._conn.commit()
        cur.close()
    
    @classmethod
    ## Execute a SELECT and return all rows
    def query(cls, sql, params=()):
        return cls.get_connection().execute(sql, params).fetchall()
    
    @classmethod
    ## Execute a statement and commit (no return)
    def execute(cls, sql, params=()):
        cls.get_connection().execute(sql, params)
        cls.get_connection().commit()
        
    @classmethod
    ## Execute a statement and return the cursor's last inserted id
    def execute_returning_id(cls, sql, params=()):
        """
        Execute an INSERT/UPDATE/DELETE and return the last inserted row id.
        Usage: Database.execute_returning_id("INSERT INTO ...", (val1, val2))
        """
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
