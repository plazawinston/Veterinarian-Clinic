"""
Appointments Module - Appointment Scheduling for Vet Clinic Management System.

This module provides appointment management with:
- Interactive calendar date selection
- Appointment scheduling and management
- Status tracking (scheduled, completed, cancelled)
- Time slot management
- Doctor and patient assignment
- Comprehensive appointment details display

Features:
- Calendar widget for easy date navigation
- List of appointments for selected date
- Add/edit appointment form
- Status indicators with colors
- Notes tracking for appointments
- Real-time appointment updates
"""

import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime,date

# Module-level variables injected by main.py
app = None
db = None
refs = {}

def show_appointments_view(parent):
    """
    Display appointment scheduling interface with calendar.
    
    Creates a split-view interface:
    - Left side: Interactive calendar and appointment list for selected date
    - Right side: Appointment form for add/edit operations
    
    Args:
        parent (ctk.CTkFrame): Parent frame to display appointment view in
        
    Features:
        - Calendar selection with date highlighting
        - Appointment list with time, patient, doctor, and status
        - Form for scheduling new appointments
        - Dropdown selections for patients and doctors
        - Status selection (scheduled/completed/cancelled)
        - Notes field for appointment details
        
    Database Operations:
        - SELECT appointments for selected date
        - SELECT all patients for dropdown
        - SELECT all doctors for dropdown
        - INSERT new appointment
        - UPDATE appointment details
        - DELETE appointment
        
    Default Date: Current date (today)
    """
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
    ctk.CTkLabel(cal_header, text="📅 Select Date", 
                font=("Arial", 20, "bold"),
                text_color="white").pack(pady=10)

    #yung issue kanina, to avoid appointments on previous dates
    calendar = Calendar(left, selectmode='day', date_pattern='yyyy-mm-dd',
                      background='#3498db', foreground='white',
                      selectbackground='#e74c3c',
                      headersbackground='#2c3e50',
                      normalbackground='white',
                      normalforeground='#2c3e50',
                      weekendbackground='#ecf0f1',
                      weekendforeground='#e74c3e',
                      font=('Arial', 12),
                      headersforeground='white',
                      borderwidth=2,
                      showweeknumbers=False,
                      mindate=datetime.now().date())
    calendar.pack(pady=20, padx=25, fill="both")

    def refresh_calendar_marks():
        # remove existing marks
        try:
            for ev in calendar.get_calevents():
                calendar.calevent_remove(ev)
        except Exception:
            pass
        # query distinct appointment dates (exclude cancelled)
        rows = db.query("SELECT DISTINCT date FROM appointments WHERE status<>?", ('cancelled',))
        for r in rows:
            try:
                d = datetime.strptime(r['date'], '%Y-%m-%d').date()
                calendar.calevent_create(d, 'appt', 'appt')
            except Exception:
                continue
        # style tag for appointments
        try:
            calendar.tag_config('appt', background='#27ae60')
        except Exception:
            pass
            
    apt_header = ctk.CTkFrame(left, fg_color="#34495e", corner_radius=10)
    apt_header.pack(fill="x", padx=15, pady=(15,10))
    ctk.CTkLabel(apt_header, text="📋 Appointments for Selected Date", 
                font=("Arial", 16, "bold"),
                text_color="white").pack(pady=10)

    # Scrollable container for appointment cards
    apt_container = ctk.CTkScrollableFrame(left, fg_color="transparent")
    apt_container.pack(fill="both", expand=True, padx=15, pady=(0,15))

    selected_date = [datetime.now().strftime('%Y-%m-%d')]
    selected_apt = [None]
    selected_card_apt = [None]

    def edit_appointment(aid):
        try:
            apt = db.query("SELECT * FROM appointments WHERE id=?", (aid,))
            if not apt:
                return
            apt = apt[0]
            selected_apt[0] = aid
            p = db.query("SELECT * FROM patients WHERE id=?", (apt['patient_id'],))
            if p:
                p = p[0]
                patient_var.set(f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}")
            d = db.query("SELECT * FROM doctors WHERE id=?", (apt['doctor_id'],))
            if d:
                d = d[0]
                # format doctor display as: "id: Name — Specialization — ₱price"
                try:
                    fee_str = f"₱{float(d['fee']):,.2f}"
                except Exception:
                    fee_str = f"₱{d['fee']}"
                spec = d['specialization'] if ('specialization' in d.keys()) else ""
                doctor_var.set(f"{d['id']}: {d['name']} — {spec} — {fee_str}")
            time_var.set(apt['time'])
            status_var.set(apt['status'])
            notes_text.delete("1.0", "end")
            notes_text.insert("1.0", apt['notes'] or "")
            # update selected appointment label
            try:
                selected_apt_label.configure(text=f"Selected Appointment ID: {aid}")
            except Exception:
                pass
        except Exception:
            pass

    def load_appointments(date_str):
        # clear container
        for w in apt_container.winfo_children():
            w.destroy()
        apts = db.query("""
            SELECT a.id, a.date, a.time, a.status, a.notes,
                   p.id as patient_id, p.name as patient_name, p.species,
                   d.id as doctor_id, d.name as doctor_name, d.specialization, d.fee
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.date = ?
            ORDER BY a.time
        """, (date_str,))
        # render appointment cards
        if apts:
            for i, apt in enumerate(apts, 1):
                try:
                    fee_str = f"₱{float(apt['fee']):,.2f}"
                except Exception:
                    fee_str = f"₱{apt['fee']}"

                card = ctk.CTkFrame(apt_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
                card.pack(fill="x", padx=10, pady=6)

                header_text = f"[{i}] {apt['time']} — {apt['patient_name']} ({apt['species']})"
                ctk.CTkLabel(card, text=header_text, font=("Arial", 13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
                ctk.CTkLabel(card, text=f"Doctor: {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}", font=("Arial", 11), anchor="w").grid(row=1, column=0, sticky="w", padx=10)
                status_icon = "✅" if apt['status'] == 'completed' else "🔔" if apt['status'] == 'scheduled' else "❌"
                ctk.CTkLabel(card, text=f"{status_icon} {apt['status'].upper()}", font=("Arial", 11), anchor="w").grid(row=0, column=1, sticky="e", padx=10, pady=(8,2))

                if apt['notes']:
                    ctk.CTkLabel(card, text=f"Notes: {apt['notes']}", font=("Arial", 11), anchor="w", wraplength=480).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6,8))

                # make the whole card clickable to select/edit (no separate Edit button)
                def on_card_click(e=None, aid=apt['id'], card_ref=card):
                    try:
                        # un-highlight previous
                        if selected_card_apt[0] and selected_card_apt[0] != card_ref:
                            selected_card_apt[0].configure(fg_color="#f8f9fa")
                    except Exception:
                        pass
                    try:
                        card_ref.configure(fg_color="#e8f8f5")
                    except Exception:
                        pass
                    selected_card_apt[0] = card_ref
                    # populate form directly (avoid timing/scope issues)
                    try:
                        row = db.query("SELECT * FROM appointments WHERE id=?", (aid,))
                        if not row:
                            return
                        a = row[0]
                        selected_apt[0] = aid
                        # make sure the form knows which date this appointment belongs to
                        try:
                            selected_date[0] = a['date']
                            try:
                                # update calendar selection to the appointment's date
                                calendar.selection_set(datetime.strptime(a['date'], '%Y-%m-%d').date())
                            except Exception:
                                pass
                        except Exception:
                            pass

                        p = db.query("SELECT * FROM patients WHERE id=?", (a['patient_id'],))
                        if p:
                            p = p[0]
                            val = f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}"
                            # set both the StringVar and the combobox visible value for robustness
                            try:
                                patient_var.set(val)
                            except Exception:
                                pass
                            try:
                                patient_dd.set(val)
                            except Exception:
                                pass
                        d = db.query("SELECT * FROM doctors WHERE id=?", (a['doctor_id'],))
                        if d:
                            d = d[0]
                            try:
                                fee_str = f"₱{float(d['fee']):,.2f}"
                            except Exception:
                                fee_str = f"₱{d['fee']}"
                            spec = d['specialization'] if ('specialization' in d.keys()) else ""
                            dval = f"{d['id']}: {d['name']} — {spec} — {fee_str}"
                            try:
                                doctor_var.set(dval)
                            except Exception:
                                pass
                            try:
                                doctor_dd.set(dval)
                            except Exception:
                                pass
                        # also set time and status dropdowns explicitly
                        # set time and status on both the widget and the variable to ensure visible update
                        try:
                            time_var.set(a['time'])
                        except Exception:
                            pass
                        try:
                            time_dd.set(a['time'])
                        except Exception:
                            pass
                        try:
                            status_var.set(a['status'])
                        except Exception:
                            pass
                        try:
                            status_dd.set(a['status'])
                        except Exception:
                            pass
                        notes_text.delete("1.0", "end")
                        notes_text.insert("1.0", a['notes'] or "")
                        try:
                            selected_apt_label.configure(text=f"Selected Appointment ID: {aid}")
                        except Exception:
                            pass
                        # enable delete button if present
                        try:
                            delete_btn.configure(state="normal")
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # debug confirmation removed — card now only populates the form

                card.bind("<Button-1>", on_card_click)
                for child in card.winfo_children():
                    child.bind("<Button-1>", on_card_click)
        else:
            ctk.CTkLabel(apt_container, text=f"No appointments scheduled for {date_str}", font=("Arial", 12)).pack(padx=10, pady=10)

    def on_date_select(event):
        selected_date[0] = calendar.get_date()
        load_appointments(selected_date[0])

    calendar.bind("<<CalendarSelected>>", on_date_select)

    def clear_selection():
        selected_apt[0] = None
        patient_var.set(patient_options[0] if patient_options else "")
        doctor_var.set(doctor_options[0] if doctor_options else "")
        time_var.set("09:00")
        status_var.set("scheduled")
        notes_text.delete("1.0", "end")
        try:
            delete_btn.configure(state="disabled")
        except Exception:
            pass

    right = ctk.CTkFrame(container, fg_color="white", corner_radius=15,
                        border_width=2, border_color="#e0e0e0", width=450)
    right.pack(side="right", fill="both", padx=(15,0))
    right.pack_propagate(False)
    
    form_header = ctk.CTkFrame(right, fg_color="#2ecc71", corner_radius=15, height=50)
    form_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(form_header, text="📝 Appointment Form", 
                font=("Arial", 20, "bold"),
                text_color="white").pack(pady=10)
    
    form_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
    form_container.pack(fill="both", expand=True, padx=15, pady=(0,15))
    
    ctk.CTkLabel(form_container, text="Patient:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(15,5))
    patients = db.query("SELECT * FROM patients ORDER BY id ASC")
    patient_options = [f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}" for p in patients]
    patient_var = ctk.StringVar(value=patient_options[0] if patient_options else "")
    patient_dd = ctk.CTkComboBox(form_container, variable=patient_var, values=patient_options, 
                             state="readonly", height=35, font=("Arial", 12),
                             dropdown_font=("Arial", 11))
    patient_dd.pack(fill="x", padx=10, pady=(0,10))

    ctk.CTkLabel(form_container, text="Doctor:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    # format visible doctor entries: "id: Name — Specialization — ₱price"
    doctor_options = []
    for d in doctors:
        try:
            fee_str = f"₱{float(d['fee']):,.2f}"
        except Exception:
            fee_str = f"₱{d['fee']}"
        spec = d['specialization'] if ('specialization' in d.keys()) else ""
        doctor_options.append(f"{d['id']}: {d['name']} — {spec} — {fee_str}")
    # use slightly smaller font so long entries fit better
    doctor_var = ctk.StringVar(value=doctor_options[0] if doctor_options else "")
    doctor_dd = ctk.CTkComboBox(form_container, variable=doctor_var, values=doctor_options,
                                state="readonly", height=34, font=("Arial", 11),
                                dropdown_font=("Arial", 10))
    doctor_dd.pack(fill="x", padx=10, pady=(0,10))
    # small helper label under the combobox (optional) can be added if needed to show more details
    
    ctk.CTkLabel(form_container, text="Time:", 
                font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    time_var = ctk.StringVar(value="08:00 AM")
    time_dd = ctk.CTkComboBox(form_container, variable=time_var,
                             values=["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
                                    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"],
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
    # Selected appointment display
    selected_apt_label = ctk.CTkLabel(form_container, text="Selected Appointment ID: None", font=("Arial", 11))
    selected_apt_label.pack(anchor="e", padx=10, pady=(0,6))
    
    def save_appointment():
        try:
            if not patient_var.get() or not doctor_var.get():
                messagebox.showerror("Error", "Please select both patient and doctor")
                return

            # Prefer the visible combobox value (user choice) over the StringVar
            def safe_get(dd_widget, var):
                try:
                    # CTkComboBox supports .get()
                    val = dd_widget.get()
                    if val:
                        return val
                except Exception:
                    pass
                try:
                    return var.get()
                except Exception:
                    return ""

            # robust ID parsing: handle values like "3: Name (...) - Owner" or plain ids
            def parse_id(value):
                if not value:
                    return ""
                v = str(value)
                try:
                    # if the value contains a colon, the id is before it
                    if ":" in v:
                        return v.split(":")[0].strip()
                    return v.strip()
                except Exception:
                    return v

            patient_raw = safe_get(patient_dd, patient_var)
            doctor_raw = safe_get(doctor_dd, doctor_var)
            patient_id = parse_id(patient_raw)
            doctor_id = parse_id(doctor_raw)
            time_selected = safe_get(time_dd, time_var)  # Get time from combobox directly
            status_selected = safe_get(status_dd, status_var)  # Get status from combobox directly
            notes = notes_text.get("1.0", "end").strip()
            
            import uuid
            apt_id = str(uuid.uuid4())[:8]

            # Check if doctor already has an appointment at this time on this date
            try:
                did = int(doctor_id)
            except Exception:
                did = doctor_id

            try:
                pid = int(patient_id)
            except Exception:
                pid = patient_id

            # Query for conflicting appointments - check BOTH doctor and patient
            conflict_check = db.query("""
                SELECT * FROM appointments 
                WHERE (doctor_id=? OR patient_id=?) 
                AND date=? AND time=? AND status<>'cancelled'
            """, (did, pid, selected_date[0], time_selected))

            if conflict_check:
                # If we're editing and it's the same appointment, allow it
                if not selected_apt[0] or selected_apt[0] != conflict_check[0]['id']:
                    conflicted_apt = conflict_check[0]
                    conflicted_entity = "Doctor" if conflicted_apt['doctor_id'] == did else "Patient"
                    messagebox.showerror("Schedule Conflict", 
                        f"{conflicted_entity} already has an appointment at {time_selected} on {selected_date[0]}")
                    return

            # If an appointment is selected, update that row. Otherwise insert a new appointment.
            if selected_apt[0]:
                # ensure we update the existing appointment rather than creating a new one
                # coerce numeric ids when possible
                try:
                    pid = int(patient_id)
                except Exception:
                    pid = patient_id
                try:
                    did = int(doctor_id)
                except Exception:
                    did = doctor_id

                db.execute("""
                    UPDATE appointments SET patient_id=?, doctor_id=?, date=?, time=?, status=?, notes=? WHERE id=?
                """, (pid, did, selected_date[0], time_selected, status_selected, notes, selected_apt[0]))
            else:
                try:
                    pid = int(patient_id)
                except Exception:
                    pid = patient_id
                try:
                    did = int(doctor_id)
                except Exception:
                    did = doctor_id

                db.execute("""
                    INSERT INTO appointments (id, patient_id, doctor_id, date, time, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (apt_id, pid, did, selected_date[0], time_selected, status_selected, notes))

            # After write, verify by re-reading the saved row and refresh the UI
            try:
                read_id = selected_apt[0] if selected_apt[0] else apt_id
                saved = db.query("SELECT * FROM appointments WHERE id=?", (read_id,))
                if saved and len(saved) > 0:
                    s = saved[0]
                    saved_pid = s.get('patient_id')
                    saved_did = s.get('doctor_id')
                    # compare canonicalized ids
                    ok = (str(saved_pid) == str(patient_id)) and (str(saved_did) == str(doctor_id)) and (s.get('time') == time_selected)
                    if ok:
                        messagebox.showinfo("✅ Success", "Appointment saved and verified!")
                    else:
                        messagebox.showwarning("Warning", f"Appointment saved but verification mismatch. Saved patient:{saved_pid} doctor:{saved_did} time:{s.get('time')}")
                else:
                    messagebox.showwarning("Warning", "Appointment write completed but could not verify saved row.")
            except Exception:
                pass

            clear_selection()
            # refresh calendar marks (in case date changed) and reload visible appointments
            try:
                refresh_calendar_marks()
            except Exception:
                pass
            load_appointments(selected_date[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    btn_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=(10,5))

    ctk.CTkButton(btn_frame, text="💾 Save", command=save_appointment,
                 fg_color="#2ecc71", hover_color="#27ae60",
                 height=45, font=("Arial", 14, "bold")).pack(side="left", padx=5, expand=True, fill="x")
    ctk.CTkButton(btn_frame, text="📄 New", command=clear_selection,
                 fg_color="#3498db", hover_color="#2980b9",
                 height=45, font=("Arial", 14, "bold")).pack(side="left", padx=5, expand=True, fill="x")

    def cancel_selected():
        try:
            if not selected_apt[0]:
                messagebox.showerror("Error", "Please select an appointment to cancel")
                return
            if messagebox.askyesno("Confirm Cancellation", "Are you sure you want to cancel this appointment?"):
                db.execute("UPDATE appointments SET status=? WHERE id=?", ("cancelled", selected_apt[0]))
                messagebox.showinfo("✅ Success", "Appointment cancelled successfully!")
                clear_selection()
                load_appointments(selected_date[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_selected_appointment():
        try:
            if not selected_apt[0]:
                messagebox.showerror("Error", "Please select an appointment to delete")
                return
            if messagebox.askyesno("Confirm Delete", "This will permanently delete the appointment. Continue?"):
                db.execute("DELETE FROM appointments WHERE id=?", (selected_apt[0],))
                messagebox.showinfo("✅ Success", "Appointment deleted successfully!")
                clear_selection()
                try:
                    refresh_calendar_marks()
                except Exception:
                    pass
                load_appointments(selected_date[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(form_container, text="❌ Cancel Appointment", command=cancel_selected,
                 fg_color="#e74c3c", hover_color="#c0392b",
                 height=45, font=("Arial", 14, "bold")).pack(fill="x", padx=10, pady=(5,8))

    # Permanent delete button
    delete_btn = ctk.CTkButton(form_container, text="🗑️ Delete Appointment", command=delete_selected_appointment,
                 fg_color="#c0392b", hover_color="#a93226",
                 height=45, font=("Arial", 14, "bold"))
    delete_btn.pack(fill="x", padx=10, pady=(0,15))
    try:
        delete_btn.configure(state="disabled")
    except Exception:
        pass
    
    load_appointments(selected_date[0])

def init_appointments(app_ref, db_ref):
    global app, db
    app = app_ref
    db = db_ref
