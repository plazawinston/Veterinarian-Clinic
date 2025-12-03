"""
Dashboard Module - Overview and Summary for Vet Clinic Management System.

This module provides a dashboard view with:
- Real-time statistics on patients, doctors, and appointments
- Quick overview of today's appointment schedule
- Patient and doctor count tracking
- Appointment status indicators
- Detailed appointment information display

Features:
- Statistics cards showing key metrics
- Today's appointments list with scrolling
- Patient and doctor information display
- Appointment status with visual indicators (✅, 🔔, ❌)
- Notes display for each appointment
- Error handling for database queries
"""
import customtkinter as ctk
from datetime import datetime

app = None
db = None
refs = {}


class Dashboard:
    """Dashboard data retrieval class for clinic statistics and appointment information."""
    
    def get_patient_count(self):
        """
        Get total number of patients in the system.
        
        Returns:
            int: Total patient count. Returns 0 if query fails.
        """
        try:
            return len(db.query("SELECT * FROM patients"))
        except Exception:
            return 0

    def get_today_appointments_count(self):
        """
        Get count of appointments scheduled for today.
        
        Returns:
            int: Number of non-cancelled appointments for today. Returns 0 if query fails.
        """
        try:
            return len(db.query(
                "SELECT * FROM appointments WHERE date=? AND status<>?", 
                (datetime.now().strftime('%Y-%m-%d'), 'cancelled')
            ))
        except Exception:
            return 0

    def get_doctor_count(self):
        """
        Get total number of doctors in the system.
        
        Returns:
            int: Total doctor count. Returns 0 if query fails.
        """
        try:
            return len(db.query("SELECT * FROM doctors"))
        except Exception:
            return 0

    def list_today_appointments(self):
        """
        Get detailed list of all appointments scheduled for today.
        
        Returns:
            list: List of appointment records with patient name, species, doctor name,
                  and specialization. Sorted by appointment time. Returns empty list if query fails.
        """
        try:
            return db.query("""
                SELECT a.*, p.name as patient_name, d.name as doctor_name, 
                       p.species as patient_species, d.specialization as doctor_specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.date = ?
                ORDER BY a.time
            """, (datetime.now().strftime('%Y-%m-%d'),))
        except Exception:
            return []


class DashboardView:
    """Dashboard UI view for displaying clinic statistics and today's appointments."""
    
    def __init__(self, parent, dashboard=None):
        """
        Initialize dashboard view.
        
        Args:
            parent (ctk.CTkFrame): Parent frame to display dashboard in
            dashboard (Dashboard, optional): Dashboard instance. Creates new if not provided.
        """
        self.parent = parent
        self.dashboard = dashboard or Dashboard()
        self.build_ui()

    def build_ui(self):
        """
        Build and render the dashboard UI.
        
        Creates:
        - Header with title
        - Statistics cards (Patients, Today's Appointments, Doctors)
        - Today's appointments list with details:
          - Appointment time
          - Patient name and species
          - Doctor name and specialization
          - Appointment status indicator
          - Notes (if available)
        - Empty state message if no appointments scheduled
        """
        for w in self.parent.winfo_children():
            w.destroy()

        # Main title
        ctk.CTkLabel(
            self.parent, 
            text="Dashboard", 
            font=("Arial", 32, "bold"),
            text_color="#2c3e50"
        ).pack(pady=20)

        # Statistics cards frame
        stats_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)

        patients = self.dashboard.get_patient_count()
        today_apts = self.dashboard.get_today_appointments_count()
        doctors = self.dashboard.get_doctor_count()

        # Create stat cards
        stats_data = [
            ("Patients", patients, "#3498db"),
            ("Today's Appointments", today_apts, "#2ecc71"),
            ("Doctors", doctors, "#e74c3c")
        ]
        
        for label, value, color in stats_data:
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            card.pack(side="left", padx=10, expand=True, fill="both")
            
            ctk.CTkLabel(
                card, 
                text=label, 
                font=("Arial", 14), 
                text_color="white"
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                card, 
                text=str(value), 
                font=("Arial", 36, "bold"),
                text_color="white"
            ).pack(pady=(5, 10))

        # Today's Appointments section
        ctk.CTkLabel(
            self.parent, 
            text="Today's Appointments", 
            font=("Arial", 20, "bold")
        ).pack(pady=(20, 10))

        # Appointments list
        appt_list_container = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        appt_list_container.pack(fill="both", expand=True, padx=20, pady=10)

        apts = self.dashboard.list_today_appointments()

        if apts:
            for apt in apts:
                self._create_appointment_card(appt_list_container, apt)
        else:
            ctk.CTkLabel(
                appt_list_container, 
                text="No appointments today.", 
                font=("Arial", 12)
            ).pack(padx=10, pady=10)

    def _create_appointment_card(self, container, apt):
        """Create a single appointment card."""
        card = ctk.CTkFrame(
            container, 
            fg_color="#f8f9fa", 
            corner_radius=8, 
            border_width=1, 
            border_color="#e0e0e0"
        )
        card.pack(fill="x", padx=6, pady=6)

        # Patient info header
        patient_species = apt['patient_species'] or ''
        header = f"{apt['time']} — {apt['patient_name']} ({patient_species})"
        ctk.CTkLabel(
            card, 
            text=header, 
            font=("Arial", 13, "bold"), 
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))

        # Status indicator
        status_icon = "✅" if apt['status'] == 'completed' else "🔔" if apt['status'] == 'scheduled' else "❌"
        ctk.CTkLabel(
            card, 
            text=f"{status_icon} {apt['status'].upper()}", 
            font=("Arial", 11), 
            anchor="e"
        ).grid(row=0, column=1, sticky="e", padx=10, pady=(8, 2))

        # Doctor info
        doctor_spec = apt['doctor_specialization'] or ''
        doctor_text = f"{apt['doctor_name']} ({doctor_spec})"
        ctk.CTkLabel(
            card, 
            text=f"Doctor: {doctor_text}", 
            font=("Arial", 11), 
            anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=10)

        # Notes (if available)
        if apt['notes']:
            ctk.CTkLabel(
                card, 
                text=f"Notes: {apt['notes']}", 
                font=("Arial", 11), 
                anchor="w", 
                wraplength=720
            ).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 8))


def show_dashboard_view(parent):
    """
    Display dashboard view in the provided parent frame.
    
    Args:
        parent (ctk.CTkFrame): Parent frame to display dashboard in
    """
    DashboardView(parent)
