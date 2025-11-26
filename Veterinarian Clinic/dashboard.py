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
    today_apts = len(db.query("SELECT * FROM appointments WHERE date=?", 
                               (datetime.now().strftime('%Y-%m-%d'),)))
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
    
    text_box = ctk.CTkTextbox(parent, height=400, font=("Arial", 12))
    text_box.pack(fill="both", expand=True, padx=20, pady=10)
    
    apts = db.query("""
        SELECT a.*, p.name as patient_name, d.name as doctor_name 
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.date = ?
        ORDER BY a.time
    """, (datetime.now().strftime('%Y-%m-%d'),))
    
    if apts:
        for apt in apts:
            text_box.insert("end", f"* {apt['time']} - {apt['patient_name']} with {apt['doctor_name']}\n")
            text_box.insert("end", f"  Status: {apt['status'].upper()}\n")
            if apt['notes']:
                text_box.insert("end", f"  Notes: {apt['notes']}\n")
            text_box.insert("end", "\n")
    else:
        text_box.insert("end", "No appointments today.")
