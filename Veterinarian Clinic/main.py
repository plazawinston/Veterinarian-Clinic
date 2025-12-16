"""
CLASS : 1

Veterinary Clinic Management System - Main Application

Main entry point for the veterinary clinic management system with modular architecture.

Features:
    - User authentication via login system
    - Modular navigation sidebar with 8 main sections
    - Dashboard for overview and statistics
    - Patient record management
    - Appointment scheduling and tracking
    - Diagnosis recording and management
    - Medicine inventory and prescription tracking
    - Doctor profile and schedule management
    - Report generation and viewing
    - Invoice creation and management
    - Automatic database initialization and schema setup
    - Confirmation prompt on exit
    - Responsive layout (1400x850 default window)
"""
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
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
import namtrash
from login import show_login


ctk.set_appearance_mode("dark")

class VetClinicApp(ctk.CTk):
    ## Initialize the main application window, set up database and UI
    def __init__(self):
        super().__init__()

        # create a Database instance instead of assigning the class
        try:
            self.db = Database()  # preferred: if Database requires a path, use Database(str(db_path))
        except TypeError:
            # fallback: if Database expects a file path, instantiate with the DB file used later
            db_path = Path(__file__).with_name('vet_clinic.db')
            self.db = Database(str(db_path))

        # Module instances will be assigned their `app` and `db` below

        self.title("VETERINARY CLINIC MANAGEMENT SYSTEM")
        self.geometry("1400x850")

        # base UI size (increase this to scale UI; set slightly larger)
        self.base_size = 21

        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#2c3e50")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="Vet Clinic", font=("Arial", self.base_size + 5, "bold"),
                    text_color="white").pack(pady=36)

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
            ("Trash", namtrash),
        ]

        for text, module_obj in modules:
            # ensure each module receives the application and database references
            try:
                module_obj.app = self
                module_obj.db = self.db
            except Exception:
                pass
            view_func = None
            for name in dir(module_obj):
                if name.startswith("show_") and name.endswith("_view"):
                    view_func = getattr(module_obj, name)
                    break

            if view_func is None:
                ## Show an error dialog when a requested module view is missing
                def missing_fn(label=text):
                    messagebox.showerror("Missing View", f"No view function found for: {label}")
                cmd = missing_fn
            else:
                ## Return a zero-arg callable that invokes the module view
                def make_cmd(f):
                    return lambda: f(self.content)
                cmd = make_cmd(view_func)

            btn = ctk.CTkButton(sidebar, text=text, command=cmd,
                                font=("Arial", self.base_size),
                                fg_color="#3498db", height=max(44, int(self.base_size * 2.2)))
            btn.pack(fill="x", padx=12, pady=6)

        ## Ask user to confirm exit and perform clean shutdown
        def confirm_exit():
            if messagebox.askyesno("Exit", "Are you sure you want to exit the application?"):
                self.quit()  # Changed from destroy() to quit()
                self.destroy()

        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=12)
        ctk.CTkButton(bottom_frame, text="Logout", command=confirm_exit,
                 fg_color="#3498db", hover_color="#2980b9",
                 font=("Arial", self.base_size, "bold"), height=max(48, int(self.base_size * 2.4))).pack(fill="x", padx=12)

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

## Application entry point: show login, initialize and run the app
def main():
    """Main entry point with proper cleanup"""
    # Destroy any existing root windows
    try:
        root = tk._default_root
        if root:
            root.destroy()
            tk._default_root = None
    except (AttributeError, tk.TclError):
        pass
    
    if show_login():
        # Clean up login window
        try:
            for widget in tk._default_root.winfo_children() if tk._default_root else []:
                if isinstance(widget, ctk.CTkToplevel):
                    widget.destroy()
        except (AttributeError, tk.TclError):
            pass
        
        app = VetClinicApp()
        app.protocol("WM_DELETE_WINDOW", app.quit)  # Handle window close button
        
        try:
            app.mainloop()
        finally:
            # Clean shutdown
            try:
                app.quit()
            except:
                pass
            try:
                app.destroy()
            except:
                pass
    else:
        print("Login cancelled or failed")

if __name__ == "__main__":
    main()
    