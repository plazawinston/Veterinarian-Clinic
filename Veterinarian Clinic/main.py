import customtkinter as ctk
from tkinter import messagebox
from database import Database
import sqlite3
from pathlib import Path

import patients
import appointments
import dashboard
import report
import invoice
import doctor
import diagnosis
import medicine
from login import show_login


ctk.set_appearance_mode("light")

class VetClinicApp(ctk. CTk):
    def __init__(self):
        super().__init__()

        self.db = Database

        for module in [patients, appointments, dashboard, report, invoice, doctor, diagnosis]:
            module.app = self
            module.db = self.db

        # register medicine module
        medicine.app = self
        medicine.db = self.db

        self.title("VETERINARY CLINIC MANAGEMENT SYSTEM")
        self.geometry("1400x850")

        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#2c3e50")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="Vet Clinic", font=("Arial", 24, "bold"), 
                    text_color="white").pack(pady=30)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#f0f0f0")
        self.content.pack(side="right", fill="both", expand=True)

        modules = [
            ("Dashboard", dashboard),
            ("Patients", patients),
            ("Appointments", appointments),
            ("Diagnosis", diagnosis),
            ("Medicines", medicine),
            ("Doctor View", doctor),
            ("Reports", report),
            ("Invoices", invoice),
        ]

        for text, module_obj in modules:
            view_func = None
            for name in dir(module_obj):
                if name.startswith("show_") and name.endswith("_view"):
                    view_func = getattr(module_obj, name)
                    break

            if view_func is None:
                def missing_fn(label=text):
                    messagebox.showerror("Missing View", f"No view function found for: {label}")
                cmd = missing_fn
            else:
                def make_cmd(f):
                    return lambda: f(self.content)
                cmd = make_cmd(view_func)

            ctk.CTkButton(sidebar, text=text, command=cmd, font=("Arial", 16),
                         fg_color="#3498db", height=50).pack(fill="x", padx=10, pady=5)

        def confirm_exit():
            if messagebox.askyesno("Exit", "Are you sure you want to exit the application?"):
                self.destroy()

        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=12)
        ctk.CTkButton(bottom_frame, text="Logout", command=confirm_exit,
                 fg_color="#3498db", hover_color="#2980b9",
                 font=("Arial", 16, "bold"), height=50).pack(fill="x", padx=10)

        dashboard.show_dashboard_view(self.content)

        db = Path(__file__).with_name('vet_clinic.db')
        conn = sqlite3.connect(str(db))
        cur = conn.cursor()

        # Ensure required tables exist to prevent "no such table: diagnoses" errors
        cur.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            patient_id INTEGER,
            doctor_id INTEGER,
            diagnosis_text TEXT,
            diagnosis_date TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            diagnosis_id INTEGER NOT NULL,
            medicine_name TEXT,
            quantity INTEGER DEFAULT 1,
            price REAL DEFAULT 0.0,
            FOREIGN KEY(diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
        );
        """)

        cur.execute("UPDATE doctors SET fee=? WHERE name=?", (15000.00, 'Dr. Princess Valdez'))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    if show_login():
        app = VetClinicApp()
        app.mainloop()
    else:
        print("Login cancelled or failed")
