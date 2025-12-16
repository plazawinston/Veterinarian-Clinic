"""
CLASS : 2

"""
import customtkinter as ctk
from datetime import datetime, timedelta

app = None
db = None
refs = {}


## Dashboard data accessors and helpers
class Dashboard:
    ## Return total number of patients
    def get_patient_count(self):
        try:
            return len(db.query("SELECT * FROM patients WHERE is_deleted=0"))
        except Exception:
            return 0

    ## Return count of today's non-cancelled appointments
    def get_today_appointments_count(self):
        try:
            return len(db.query(
                "SELECT * FROM appointments WHERE date=? AND status<>?", 
                (datetime.now().strftime('%Y-%m-%d'), 'cancelled')
            ))
        except Exception:
            return 0

    ## Return total number of doctors
    def get_doctor_count(self):
        try:
            return len(db.query("SELECT * FROM doctors"))
        except Exception:
            return 0

    ## List appointments for today with patient and doctor info
    def list_today_appointments(self):
        try:
            return db.query("""
                SELECT a.*, p.name as patient_name, d.name as doctor_name, p.species as patient_species, d.specialization as doctor_specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.date = ?
                ORDER BY a.time
            """, (datetime.now().strftime('%Y-%m-%d'),))
        except Exception:
            return []

    ## Get completed appointments for a given month
    def get_completed_appointments_for_month(self, year, month):
        try:
            start_dt = datetime(year, month, 1)
            if month == 12:
                next_month_dt = datetime(year + 1, 1, 1)
            else:
                next_month_dt = datetime(year, month + 1, 1)
            end_dt = next_month_dt - timedelta(days=1)
            start = start_dt.strftime('%Y-%m-%d')
            end = end_dt.strftime('%Y-%m-%d')
            return db.query(
                """
                SELECT a.*, p.name as patient_name, d.name as doctor_name, p.species as patient_species, d.specialization as doctor_specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.status = ? AND a.date BETWEEN ? AND ?
                ORDER BY a.date, a.time
                """,
                ('completed', start, end)
            )
        except Exception:
            return []


class DashboardView:
    ## View class: builds dashboard UI and navigation
    def __init__(self, parent, dashboard=None):
        self.parent = parent
        self.dashboard = dashboard or Dashboard()
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        self.build_ui()

    ## Construct UI elements for the dashboard
    def build_ui(self):
        for w in self.parent.winfo_children():
            w.destroy()

        # small scale increase for this module
        module_scale = 4
        ## Font helper for dashboard module
        def F(size, weight=None):
            s = int(size + module_scale)
            return ("Arial", s, weight) if weight else ("Arial", s)

        ctk.CTkLabel(self.parent, text="Dashboard", font=F(32, "bold"),
                    text_color="#2c3e50").pack(pady=20 + module_scale)

        stats_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)

        patients = self.dashboard.get_patient_count()
        today_apts = self.dashboard.get_today_appointments_count()
        doctors = self.dashboard.get_doctor_count()

        for label, value, color in [
            ("Patients", patients, "#3498db"),
            ("Today's Appointments", today_apts, "#2ecc71"),
            ("Doctors", doctors, "#e74c3c")
        ]:
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            card.pack(side="left", padx=10, expand=True, fill="both")
            ctk.CTkLabel(card, text=label, font=F(14), 
                        text_color="white").pack(pady=(10 + module_scale, 5))
            ctk.CTkLabel(card, text=str(value), font=F(36, "bold"),
                        text_color="white").pack(pady=(5, 10 + module_scale))

        # Monthly completed appointments section
        monthly_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        monthly_frame.pack(fill="x", padx=20, pady=(10, 0))

        ## Navigate to previous month and rebuild UI
        def prev_month():
            m = self.current_month - 1
            y = self.current_year
            if m < 1:
                m = 12
                y -= 1
            self.current_month = m
            self.current_year = y
            self.build_ui()

        ## Navigate to next month and rebuild UI
        def next_month():
            m = self.current_month + 1
            y = self.current_year
            if m > 12:
                m = 1
                y += 1
            self.current_month = m
            self.current_year = y
            self.build_ui()

        header_frame = ctk.CTkFrame(monthly_frame, fg_color="transparent")
        header_frame.pack(fill="x")
        ctk.CTkLabel(header_frame, text="Monthly Completed Appointments", font=F(16, "bold")).pack(side="left")
        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.pack(side="right")
        ctk.CTkButton(nav_frame, text="<", width=28, command=prev_month).pack(side="left", padx=4)
        ctk.CTkLabel(nav_frame, text=datetime(self.current_year, self.current_month, 1).strftime('%B %Y'), font=F(12)).pack(side="left", padx=6)
        ctk.CTkButton(nav_frame, text=">", width=28, command=next_month).pack(side="left", padx=4)

        completed_apts = self.dashboard.get_completed_appointments_for_month(self.current_year, self.current_month)
        count = len(completed_apts)
        count_card = ctk.CTkFrame(monthly_frame, fg_color="#34495e", corner_radius=8)
        count_card.pack(fill="x", pady=(8, 6))
        ctk.CTkLabel(count_card, text=f"Completed this month: {count}", font=F(14), text_color="white").pack(padx=10, pady=8)

        monthly_list = ctk.CTkScrollableFrame(self.parent, fg_color="transparent", height=120)
        monthly_list.pack(fill="x", padx=20, pady=(0, 10))
        if completed_apts:
            for apt in completed_apts:
                card = ctk.CTkFrame(monthly_list, fg_color="#f6f8fa", corner_radius=6, border_width=1, border_color="#e0e0e0")
                card.pack(fill="x", padx=6, pady=4)
                date_text = apt['date'] if apt['date'] is not None else ''
                time_text = apt['time'] if apt['time'] is not None else ''
                patient = apt['patient_name'] if apt['patient_name'] is not None else ''
                doctor = apt['doctor_name'] if apt['doctor_name'] is not None else ''
                header = f"{date_text} {time_text} — {patient}"
                ctk.CTkLabel(card, text=header, font=F(12, "bold"), anchor="w").pack(fill="x", padx=8, pady=(6,2))
                ctk.CTkLabel(card, text=f"Doctor: {doctor}", font=F(11), anchor="w").pack(fill="x", padx=8, pady=(0,6))
        else:
            ctk.CTkLabel(monthly_list, text="No completed appointments this month.", font=F(12)).pack(padx=10, pady=8)

        ctk.CTkLabel(self.parent, text="Today's Appointments", 
                    font=F(20, "bold")).pack(pady=(20 + module_scale, 10))

        appt_list_container = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        appt_list_container.pack(fill="both", expand=True, padx=20, pady=10)

        apts = self.dashboard.list_today_appointments()

        if apts:
            for apt in apts:
                card = ctk.CTkFrame(appt_list_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
                card.pack(fill="x", padx=6, pady=6)

                patient_species = apt['patient_species'] if apt['patient_species'] is not None else ''
                header = f"{apt['time']} — {apt['patient_name']} ({patient_species})"
                ctk.CTkLabel(card, text=header, font=F(13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10 + module_scale, pady=(8,2))

                doctor_spec = apt['doctor_specialization'] if apt['doctor_specialization'] is not None else ''
                doctor_text = f"{apt['doctor_name']} ({doctor_spec})"
                ctk.CTkLabel(card, text=f"Doctor: {doctor_text}", font=F(11), anchor="w").grid(row=1, column=0, sticky="w", padx=10 + module_scale)

                status_icon = "✅" if apt['status'] == 'completed' else "🔔" if apt['status'] == 'scheduled' else "❌"
                ctk.CTkLabel(card, text=f"{status_icon} {apt['status'].upper()}", font=F(11), anchor="e").grid(row=0, column=1, sticky="e", padx=10 + module_scale, pady=(8,2))

                if apt['notes']:
                    ctk.CTkLabel(card, text=f"Notes: {apt['notes']}", font=F(11), anchor="w", wraplength=720 + module_scale * 20).grid(row=2, column=0, columnspan=2, sticky="w", padx=10 + module_scale, pady=(6,8))
        else:
            ctk.CTkLabel(appt_list_container, text="No appointments today.", font=F(12)).pack(padx=10, pady=10)


## Show the dashboard view in the provided parent container
def show_dashboard_view(parent):
    DashboardView(parent)
