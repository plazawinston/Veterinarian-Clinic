import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime
import uuid

app = None
db = None
refs = {}

def show_appointments_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Appointment Scheduling",
                font=("Arial", 38, "bold"),
                text_color="#2c3e50").pack(pady=25)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=30, pady=(0,20))
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=15, 
                       border_width=2, border_color="#e0e0e0")
    left.pack(side="left", fill="both", expand=True, padx=(0,15))
    
    cal_header = ctk.CTkFrame(left, fg_color="#3498db", corner_radius=15, height=50)
    cal_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(cal_header, text="Select Date", 
                font=("Arial", 20, "bold"),
                text_color="white").pack(pady=10)
    
    calendar = Calendar(left, selectmode='day', date_pattern='yyyy-mm-dd',
                      background='#3498db', foreground='white',
                      selectbackground='#e74c3c',
                      headersbackground='#2c3e50',
                      normalbackground='white',
                      normalforeground='#2c3e50',
                      weekendbackground='#ecf0f1',
                      weekendforeground='#e74c3c',
                      font=('Arial', 12),
                      headersforeground='white',
                      borderwidth=2,
                      showweeknumbers=False)
    calendar.pack(pady=20, padx=25, fill="both")
    
    apt_header = ctk.CTkFrame(left, fg_color="#34495e", corner_radius=10)
    apt_header.pack(fill="x", padx=15, pady=(15,10))
    ctk.CTkLabel(apt_header, text="Appointments for Selected Date", 
                font=("Arial", 16, "bold"),
                text_color="white").pack(pady=10)
    
    apt_list = ctk.CTkTextbox(left, font=("Arial", 12), 
                             fg_color="#f8f9fa",
                             border_width=2,
                             border_color="#dee2e6",
                             corner_radius=10)
    apt_list.pack(fill="both", expand=True, padx=15, pady=(0,15))
    
    selected_date = [datetime.now().strftime('%Y-%m-%d')]
    selected_apt = [None]
    
    def load_appointments(date_str):
        apt_list.delete("1.0", "end")
        apts = db.query("""
            SELECT a.id, a.date, a.time, a.status, a.notes,
                   COALESCE(CAST(p.id AS TEXT), 'N/A') as patient_id, 
                   COALESCE(p.name, 'Unknown') as patient_name, 
                   COALESCE(p.species, 'Unknown') as species,
                   COALESCE(CAST(d.id AS TEXT), 'N/A') as doctor_id, 
                   COALESCE(d.name, 'Unknown') as doctor_name, 
                   COALESCE(d.specialization, 'N/A') as specialization, 
                   COALESCE(d.fee, 0.0) as fee
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN doctors d ON a.doctor_id = d.id
            WHERE a.date = ?
            ORDER BY a.time
        """, (date_str,))
        
        apt_list.insert("end", f"=== Appointments for {date_str} ===\n\n", "header")
        
        if apts:
            for i, apt in enumerate(apts, 1):
                fee_value = float(apt['fee']) if apt['fee'] else 0.0
                fee_str = f"P{fee_value:,.2f}"
                
                apt_list.insert("end", f"[{i}] ID:{apt['id']}\n", "bold")
                apt_list.insert("end", f"    Time: {apt['time']}\n")
                apt_list.insert("end", f"    Patient: {apt['patient_name']} ({apt['species']})\n")
                apt_list.insert("end", f"    Doctor: {apt['doctor_name']} ({apt['specialization']})\n")
                apt_list.insert("end", f"    Fee: {fee_str}\n")
                
                status_icon = "[OK]" if apt['status'] == 'completed' else "[PENDING]" if apt['status'] == 'scheduled' else "[X]"
                apt_list.insert("end", f"    {status_icon} Status: {apt['status'].upper()}\n")
                
                if apt['notes']:
                    apt_list.insert("end", f"    Notes: {apt['notes']}\n")
                apt_list.insert("end", "\n" + "-"*60 + "\n\n")
        else:
            apt_list.insert("end", f"    No appointments scheduled for {date_str}\n\n")
            apt_list.insert("end", "    Click 'New' to create an appointment\n")
        
        apt_list.insert("end", "=" * 58 + "\n")
    
    def on_date_select(event):
        selected_date[0] = calendar.get_date()
        date_label.configure(text=selected_date[0])
        load_appointments(selected_date[0])
    
    calendar.bind("<<CalendarSelected>>", on_date_select)
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=15,
                        border_width=2, border_color="#e0e0e0", width=450)
    right.pack(side="right", fill="both", padx=(15,0))
    right.pack_propagate(False)
    
    form_header = ctk.CTkFrame(right, fg_color="#2ecc71", corner_radius=15, height=50)
    form_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(form_header, text="Appointment Form", 
                font=("Arial", 20, "bold"),
                text_color="white").pack(pady=10)
    
    form_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
    form_container.pack(fill="both", expand=True, padx=15, pady=(0,15))
    
    ctk.CTkLabel(form_container, text="Appointment Date:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(15,5))
    
    date_display_frame = ctk.CTkFrame(form_container, fg_color="#e8f4fd", corner_radius=8,
                                       border_width=2, border_color="#3498db")
    date_display_frame.pack(fill="x", padx=10, pady=(0,10))
    
    date_label = ctk.CTkLabel(date_display_frame, 
                              text=selected_date[0],
                              font=("Arial", 16, "bold"),
                              text_color="#2980b9")
    date_label.pack(pady=12)
    
    ctk.CTkLabel(form_container, text="Patient:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(15,5))
    patients = db.query("SELECT * FROM patients ORDER BY name")
    patient_options = [f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}" for p in patients]
    patient_var = ctk.StringVar(value=patient_options[0] if patient_options else "")
    patient_dd = ctk.CTkComboBox(form_container, variable=patient_var, values=patient_options, 
                             state="readonly", height=35, font=("Arial", 12),
                             dropdown_font=("Arial", 11))
    patient_dd.pack(fill="x", padx=10, pady=(0,10))
    
    ctk.CTkLabel(form_container, text="Doctor:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    doctors = db.query("SELECT * FROM doctors ORDER BY name")
    doctor_options = []
    for d in doctors:
        fee_value = float(d['fee']) if d['fee'] else 0.0
        fee_display = f"P{fee_value:,.2f}"
        doctor_options.append(f"{d['id']}: {d['name']} ({d['specialization']}) - {fee_display}")
    doctor_var = ctk.StringVar(value=doctor_options[0] if doctor_options else "")
    doctor_dd = ctk.CTkComboBox(form_container, variable=doctor_var, values=doctor_options,
                            state="readonly", height=35, font=("Arial", 12),
                            dropdown_font=("Arial", 11))
    doctor_dd.pack(fill="x", padx=10, pady=(0,10))
    
    ctk.CTkLabel(form_container, text="Time:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    time_var = ctk.StringVar(value="8:00 AM")
    time_dd = ctk.CTkComboBox(form_container, variable=time_var,
                             values=["8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", 
                                    "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"],
                             state="readonly", height=35, font=("Arial", 12))
    time_dd.pack(fill="x", padx=10, pady=(0,10))
    
    ctk.CTkLabel(form_container, text="Status:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    status_var = ctk.StringVar(value="scheduled")
    status_dd = ctk.CTkComboBox(form_container, variable=status_var,
                               values=["scheduled", "completed", "cancelled"],
                               state="readonly", height=35, font=("Arial", 12))
    status_dd.pack(fill="x", padx=10, pady=(0,10))
    
    ctk.CTkLabel(form_container, text="Notes:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    notes_text = ctk.CTkTextbox(form_container, height=100, font=("Arial", 11),
                                 fg_color="#f8f9fa", border_width=2,
                                 border_color="#dee2e6")
    notes_text.pack(fill="x", padx=10, pady=(0,15))
    
    def clear_selection():
        selected_apt[0] = None
        patient_var.set(patient_options[0] if patient_options else "")
        doctor_var.set(doctor_options[0] if doctor_options else "")
        time_var.set("8:00 AM")
        status_var.set("scheduled")
        notes_text.delete("1.0", "end")
    
    def save_appointment():
        try:
            patient_selection = patient_dd.get()
            doctor_selection = doctor_dd.get()
            time_selection = time_dd.get()
            status_selection = status_dd.get()
            appointment_date = calendar.get_date()
            
            if not patient_selection or not doctor_selection:
                messagebox.showerror("Error", "Please select both patient and doctor")
                return

            patient_id = int(patient_selection.split(":")[0])
            doctor_id = int(doctor_selection.split(":")[0])
            notes = notes_text.get("1.0", "end").strip()
            
            apt_id = str(uuid.uuid4())[:8]

            if selected_apt[0]:
                db.execute("""
                    UPDATE appointments SET patient_id=?, doctor_id=?, date=?, time=?, status=?, notes=? WHERE id=?
                """, (patient_id, doctor_id, appointment_date, time_selection, status_selection, notes, selected_apt[0]))
                messagebox.showinfo("Success", "Appointment updated successfully!")
            else:
                db.execute("""
                    INSERT INTO appointments (id, patient_id, doctor_id, date, time, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (apt_id, patient_id, doctor_id, appointment_date, time_selection, status_selection, notes))
                messagebox.showinfo("Success", "Appointment scheduled successfully!")

            selected_date[0] = appointment_date
            date_label.configure(text=appointment_date)
            clear_selection()
            load_appointments(appointment_date)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    btn_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=(10,5))

    ctk.CTkButton(btn_frame, text="Save", command=save_appointment,
                 fg_color="#2ecc71", hover_color="#27ae60",
                 height=45, font=("Arial", 14, "bold")).pack(side="left", padx=5, expand=True, fill="x")
    ctk.CTkButton(btn_frame, text="New", command=clear_selection,
                 fg_color="#3498db", hover_color="#2980b9",
                 height=45, font=("Arial", 14, "bold")).pack(side="left", padx=5, expand=True, fill="x")

    def cancel_selected():
        try:
            if not selected_apt[0]:
                messagebox.showerror("Error", "Please select an appointment to cancel")
                return
            if messagebox.askyesno("Confirm Cancellation", "Are you sure you want to cancel this appointment?"):
                db.execute("UPDATE appointments SET status=? WHERE id=?", ("cancelled", selected_apt[0]))
                messagebox.showinfo("Success", "Appointment cancelled successfully!")
                clear_selection()
                load_appointments(selected_date[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(form_container, text="Cancel Appointment", command=cancel_selected,
                 fg_color="#e74c3c", hover_color="#c0392b",
                 height=45, font=("Arial", 14, "bold")).pack(fill="x", padx=10, pady=(5,15))
    
    def on_select(event):
        try:
            idx = apt_list.index(f"@{event.x},{event.y}")
            line = apt_list.get(idx.split('.')[0] + ".0", idx.split('.')[0] + ".end")
            if "ID:" in line:
                aid = line.split("ID:")[1].split()[0].strip()
                apt = db.query("SELECT * FROM appointments WHERE id=?", (aid,))
                if apt:
                    apt = apt[0]
                    selected_apt[0] = aid
                    
                    p = db.query("SELECT * FROM patients WHERE id=?", (apt['patient_id'],))
                    if p:
                        p = p[0]
                        patient_var.set(f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}")
                    
                    d = db.query("SELECT * FROM doctors WHERE id=?", (apt['doctor_id'],))
                    if d:
                        d = d[0]
                        fee_value = float(d['fee']) if d['fee'] else 0.0
                        doctor_var.set(f"{d['id']}: {d['name']} ({d['specialization']}) - P{fee_value:,.2f}")
                    
                    time_var.set(apt['time'])
                    status_var.set(apt['status'])
                    notes_text.delete("1.0", "end")
                    notes_text.insert("1.0", apt['notes'] or "")
        except Exception:
            pass

    apt_list.bind("<Button-1>", on_select)
    load_appointments(selected_date[0])

def init_appointments(app_ref, db_ref):
    global app, db
    app = app_ref
    db = db_ref
