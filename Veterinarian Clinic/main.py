"""
Vet Clinic Main Application - GUI entry point.

Starts the CustomTkinter-based GUI for the Veterinary Clinic Management System.
Defines the VetClinicApp class which:
- wires application modules (patients, appointments, dashboard, etc.) to the app and Database
- builds the sidebar with buttons for each module view (auto-detects show_*_view functions)
- displays the main dashboard and ensures required DB tables/initial data exist


Requirements:
- customtkinter installed
- database.py in the project (provides Database and vet_clinic.db)

The application first calls show_login(); if login succeeds it launches VetClinicApp.
"""

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

        for module in [patients, appointments, dashboard, report, invoice, doctor, diagnosis, medicine]:
            module.app = self
            module.db = self.db

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

        # Initialize database and tables via Database class (centralized setup & migration)
        try:
            Database.get_connection()  # ensures tables exist and initial data is seeded
            # Apply any small fixes/overrides here using Database helper
            Database.execute("UPDATE doctors SET fee = ? WHERE name = ?", (15000.00, 'Dr. Princess Valdez'))
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

if __name__ == "__main__":
    if show_login():
        app = VetClinicApp()
        app.mainloop()
    else:
        print("Login cancelled or failed")
