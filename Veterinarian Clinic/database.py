import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name('vet_clinic.db')

class Database:
    _conn = None
    
    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            cls._conn = sqlite3.connect(str(DB_FILE))
            cls._conn.row_factory = sqlite3.Row
            cls._setup_tables()
        return cls._conn
    
    @classmethod
    def _setup_tables(cls):
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
        ''')
        
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
        cur.close()
    
    @classmethod
    def query(cls, sql, params=()):
        return cls.get_connection().execute(sql, params).fetchall()
    
    @classmethod
    def execute(cls, sql, params=()):
        cls.get_connection().execute(sql, params)
        cls.get_connection().commit()
        
    @classmethod
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
