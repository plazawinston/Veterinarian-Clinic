import customtkinter as ctk
from datetime import datetime

app = None
db = None
refs = {}

def show_dashboard_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Dashboard", font=("Arial", 32, "bold"),
                text_color="#2c3e50").pack(pady=20)
    
    stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
    stats_frame.pack(fill="x", padx=20, pady=10)
    
    patients = len(db.query("SELECT * FROM patients"))
    # Count only non-cancelled appointments for today
    today_apts = len(db.query(
        "SELECT * FROM appointments WHERE date=? AND status<>?", 
        (datetime.now().strftime('%Y-%m-%d'), 'cancelled')
    ))
    doctors = len(db.query("SELECT * FROM doctors"))
    
    for label, value, color in [
        ("Patients", patients, "#3498db"),
        ("Today's Appointments", today_apts, "#2ecc71"),
        ("Doctors", doctors, "#e74c3c")
    ]:
        card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
        card.pack(side="left", padx=10, expand=True, fill="both")
        ctk.CTkLabel(card, text=label, font=("Arial", 14), 
                    text_color="white").pack(pady=(10,5))
        ctk.CTkLabel(card, text=str(value), font=("Arial", 36, "bold"),
                    text_color="white").pack(pady=(5,10))
    
    ctk.CTkLabel(parent, text="Today's Appointments", 
                font=("Arial", 20, "bold")).pack(pady=(20,10))

    # Use a scrollable frame with per-appointment cards for a cleaner look
    appt_list_container = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    appt_list_container.pack(fill="both", expand=True, padx=20, pady=10)

    apts = db.query("""
        SELECT a.*, p.name as patient_name, d.name as doctor_name, p.species as patient_species, d.specialization as doctor_specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.date = ?
        ORDER BY a.time
    """, (datetime.now().strftime('%Y-%m-%d'),))

    if apts:
        for apt in apts:
            card = ctk.CTkFrame(appt_list_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
            card.pack(fill="x", padx=6, pady=6)

            # sqlite3.Row doesn't have .get(), access keys directly and handle None
            patient_species = apt['patient_species'] if apt['patient_species'] is not None else ''
            header = f"{apt['time']} — {apt['patient_name']} ({patient_species})"
            ctk.CTkLabel(card, text=header, font=("Arial", 13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))

            doctor_spec = apt['doctor_specialization'] if apt['doctor_specialization'] is not None else ''
            doctor_text = f"{apt['doctor_name']} ({doctor_spec})"
            ctk.CTkLabel(card, text=f"Doctor: {doctor_text}", font=("Arial", 11), anchor="w").grid(row=1, column=0, sticky="w", padx=10)

            status_icon = "✅" if apt['status'] == 'completed' else "🔔" if apt['status'] == 'scheduled' else "❌"
            ctk.CTkLabel(card, text=f"{status_icon} {apt['status'].upper()}", font=("Arial", 11), anchor="e").grid(row=0, column=1, sticky="e", padx=10, pady=(8,2))

            if apt['notes']:
                ctk.CTkLabel(card, text=f"Notes: {apt['notes']}", font=("Arial", 11), anchor="w", wraplength=720).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6,8))
    else:
        ctk.CTkLabel(appt_list_container, text="No appointments today.", font=("Arial", 12)).pack(padx=10, pady=10)
