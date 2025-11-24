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
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY,
                name TEXT, species TEXT, breed TEXT, age INTEGER,
                owner_name TEXT, owner_contact TEXT, notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT, specialization TEXT, fee REAL
            );
            
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER, doctor_id INTEGER,
                date TEXT, time TEXT, status TEXT, notes TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id),
                FOREIGN KEY(doctor_id) REFERENCES doctors(id)
            );
        ''')
        
        # doctors if empty
        if not cur.execute("SELECT * FROM doctors").fetchone():
            cur.executemany(
                "INSERT INTO doctors (name, specialization, fee) VALUES (?, ?, ?)",
                [
                    ('Dr. Sarah Johnson', 'Nutrition', 3500.00),
                    ('Dr. Mike Brown', 'Grooming', 2500.00),
                    ('Dr. Emily Davis', 'Surgery', 1500.00),
                    ('Dr. Robert Wilson', 'Dentistry', 5000.00),
                    ('Dr. Lisa Anderson', 'Ophthalmology', 4500.00),
                    ('Dr. James Martinez', 'Dermatology', 5000.00)
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

