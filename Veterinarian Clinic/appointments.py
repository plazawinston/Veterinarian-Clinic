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
    ...
    """
    for w in parent.winfo_children():
        w.destroy()

    # Slight scale up for this module (add +5 to sizes)
    module_scale = 5
    def F(size, weight=None):
        # returns a font tuple with module scale applied
        s = int(size + module_scale)
        if weight:
            return ("Arial", s, weight)
        return ("Arial", s)

    ctk.CTkLabel(parent, text="Appointment Scheduling",
                font=F(38, "bold"),
                text_color="#2c3e50").pack(pady=25)

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=30, pady=(0,20))

    left = ctk.CTkFrame(container, fg_color="white", corner_radius=15, 
                       border_width=2, border_color="#e0e0e0")
    left.pack(side="left", fill="both", expand=True, padx=(0,15))

    cal_header = ctk.CTkFrame(left, fg_color="#3498db", corner_radius=15, height=50 + module_scale)
    cal_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(cal_header, text="📅 Select Date", 
                font=F(20, "bold"),
                text_color="white").pack(pady=10)

    # prevent appointments on previous dates; scaled calendar font
    calendar = Calendar(left, selectmode='day', date_pattern='yyyy-mm-dd',
                      background='#3498db', foreground='white',
                      selectbackground='#e74c3c',
                      headersbackground='#2c3e50',
                      normalbackground='white',
                      normalforeground='#2c3e50',
                      weekendbackground='#ecf0f1',
                      weekendforeground='#2c3e',
                      font=F(12),
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
                font=F(16, "bold"),
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
                ctk.CTkLabel(card, text=header_text, font=F(13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
                ctk.CTkLabel(card, text=f"Doctor: {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}", font=F(11), anchor="w").grid(row=1, column=0, sticky="w", padx=10)
                status_icon = "✅" if apt['status'] == 'completed' else "🔔" if apt['status'] == 'scheduled' else "❌"
                ctk.CTkLabel(card, text=f"{status_icon} {apt['status'].upper()}", font=F(11), anchor="w").grid(row=0, column=1, sticky="e", padx=10, pady=(8,2))

                if apt['notes']:
                    ctk.CTkLabel(card, text=f"Notes: {apt['notes']}", font=F(11), anchor="w", wraplength=480 + module_scale * 8).grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(6,8))

                def on_card_click(e=None, aid=apt['id'], card_ref=card):
                    try:
                        if selected_card_apt[0] and selected_card_apt[0] != card_ref:
                            selected_card_apt[0].configure(fg_color="#f8f9fa")
                    except Exception:
                        pass
                    try:
                        card_ref.configure(fg_color="#e8f8f5")
                    except Exception:
                        pass
                    selected_card_apt[0] = card_ref
                    try:
                        row = db.query("SELECT * FROM appointments WHERE id=?", (aid,))
                        if not row:
                            return
                        a = row[0]
                        selected_apt[0] = aid
                        try:
                            selected_date[0] = a['date']
                            try:
                                calendar.selection_set(datetime.strptime(a['date'], '%Y-%m-%d').date())
                            except Exception:
                                pass
                        except Exception:
                            pass

                        p = db.query("SELECT * FROM patients WHERE id=?", (a['patient_id'],))
                        if p:
                            p = p[0]
                            val = f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}"
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
                        try:
                            delete_btn.configure(state="normal")
                        except Exception:
                            pass
                    except Exception:
                        pass

                card.bind("<Button-1>", on_card_click)
                for child in card.winfo_children():
                    child.bind("<Button-1>", on_card_click)
        else:
            ctk.CTkLabel(apt_container, text=f"No appointments scheduled for {date_str}", font=F(12)).pack(padx=10, pady=10)

    def on_date_select(event):
        selected_date[0] = calendar.get_date()
        load_appointments(selected_date[0])

    calendar.bind("<<CalendarSelected>>", on_date_select)

    def clear_selection():
        selected_apt[0] = None
        selected_card_apt[0] = None
        patient_var.set(patient_options[0] if patient_options else "")
        doctor_var.set(doctor_options[0] if doctor_options else "")
        time_var.set("09:00")
        status_var.set("scheduled")
        notes_text.delete("1.0", "end")
        try:
            delete_btn.configure(state="disabled")
        except Exception:
            pass
        try:
            selected_apt_label.configure(text="Selected Appointment ID: None")
        except Exception:
            pass
        try:
            load_appointments(selected_date[0])
        except Exception:
            pass

    refresh_calendar_marks()

    right = ctk.CTkFrame(container, fg_color="white", corner_radius=15,
                        border_width=2, border_color="#e0e0e0", width=450 + module_scale * 6)
    right.pack(side="right", fill="both", padx=(15,0))
    right.pack_propagate(False)

    form_header = ctk.CTkFrame(right, fg_color="#2ecc71", corner_radius=15, height=50 + module_scale)
    form_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(form_header, text="📝 Appointment Form", 
                font=F(20, "bold"),
                text_color="white").pack(pady=10)

    form_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
    form_container.pack(fill="both", expand=True, padx=15, pady=(0,15))

    ctk.CTkLabel(form_container, text="Patient:", 
                font=F(13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(15,5))
    patients = db.query("SELECT * FROM patients ORDER BY id ASC")
    patient_options = [f"{p['id']}: {p['name']} ({p['species']}) - {p['owner_name']}" for p in patients]
    patient_var = ctk.StringVar(value=patient_options[0] if patient_options else "")
    patient_dd = ctk.CTkComboBox(form_container, variable=patient_var, values=patient_options, 
                             state="readonly", height=35 + module_scale, font=F(12),
                             dropdown_font=F(11))
    patient_dd.pack(fill="x", padx=10, pady=(0,10))

    ctk.CTkLabel(form_container, text="Doctor:", 
                font=F(13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    doctor_options = []
    for d in doctors:
        try:
            fee_str = f"₱{float(d['fee']):,.2f}"
        except Exception:
            fee_str = f"₱{d['fee']}"
        spec = d['specialization'] if ('specialization' in d.keys()) else ""
        doctor_options.append(f"{d['id']}: {d['name']} — {spec} — {fee_str}")
    doctor_var = ctk.StringVar(value=doctor_options[0] if doctor_options else "")
    doctor_dd = ctk.CTkComboBox(form_container, variable=doctor_var, values=doctor_options,
                                state="readonly", height=34 + module_scale, font=F(11),
                                dropdown_font=F(10))
    doctor_dd.pack(fill="x", padx=10, pady=(0,10))

    ctk.CTkLabel(form_container, text="Time:", 
                font=F(13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    time_var = ctk.StringVar(value="08:00 AM")
    time_dd = ctk.CTkComboBox(form_container, variable=time_var,
                             values=["08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
                                    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"],
                             state="readonly", height=35 + module_scale, font=F(12))
    time_dd.pack(fill="x", padx=10, pady=(0,10))

    ctk.CTkLabel(form_container, text="Status:", 
                font=F(13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    status_var = ctk.StringVar(value="scheduled")
    status_dd = ctk.CTkComboBox(form_container, variable=status_var,
                               values=["scheduled", "completed", "cancelled"],
                               state="readonly", height=35 + module_scale, font=F(12))
    status_dd.pack(fill="x", padx=10, pady=(0,10))

    ctk.CTkLabel(form_container, text="Notes:", 
                font=F(13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=10, pady=(10,5))
    notes_text = ctk.CTkTextbox(form_container, height=100 + module_scale*4, font=F(11),
                                 fg_color="#f8f9fa", border_width=2,
                                 border_color="#dee2e6")
    notes_text.pack(fill="x", padx=10, pady=(0,15))
    selected_apt_label = ctk.CTkLabel(form_container, text="Selected Appointment ID: None", font=F(11))
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

            # normalize time (preserve AM/PM or exact input; do not convert to 24h)
            def normalize_time(t):
                if not t:
                    return ""
                s = str(t).strip()
                import re
                # collapse whitespace
                s = re.sub(r'\s+', ' ', s)
                # ensure AM/PM is uppercase and separated by a space if present
                s = re.sub(r'(?i)\s*(am|pm)$', lambda m: ' ' + m.group(1).upper(), s)
                # add colon if user typed hours and minutes without one (e.g. 0800 or 800)
                s = re.sub(r'^(?P<h>\d{1,2})(?P<m>\d{2})(?:\s*(?P<ap>(AM|PM|am|pm)))?$', 
                           lambda m: f"{int(m.group('h')):02d}:{m.group('m')}{(' ' + m.group('ap').upper()) if m.group('ap') else ''}", s)
                return s

            patient_raw = safe_get(patient_dd, patient_var)
            doctor_raw = safe_get(doctor_dd, doctor_var)
            patient_id = parse_id(patient_raw)
            doctor_id = parse_id(doctor_raw)
            time_raw = safe_get(time_dd, time_var)  # Get time from combobox directly
            time_selected = normalize_time(time_raw)
            status_selected = safe_get(status_dd, status_var)  # Get status from combobox directly
            notes = notes_text.get("1.0", "end").strip()

            import uuid
            apt_id = str(uuid.uuid4())[:8]

            # Coerce numeric ids when possible for DB operations
            try:
                did = int(doctor_id)
            except Exception:
                did = doctor_id

            try:
                pid = int(patient_id)
            except Exception:
                pid = patient_id

            # Query for conflicting appointments - check BOTH doctor and patient with normalized time
            conflict_check = db.query("""
                SELECT * FROM appointments 
                WHERE (doctor_id=? OR patient_id=?) 
                AND date=? AND time=? AND status<>'cancelled'
            """, (did, pid, selected_date[0], time_selected))

            if conflict_check:
                # If we're editing and it's the same appointment, allow it
                if not selected_apt[0] or selected_apt[0] != conflict_check[0]['id']:
                    conflicted_apt = conflict_check[0]
                    conflicted_entity = "Doctor" if str(conflicted_apt['doctor_id']) == str(did) else "Patient"
                    messagebox.showerror("Schedule Conflict", 
                        f"{conflicted_entity} already has an appointment at {time_raw} on {selected_date[0]}")
                    return

            # If an appointment is selected, update that row. Otherwise insert a new appointment.
            if selected_apt[0]:
                db.execute("""
                    UPDATE appointments SET patient_id=?, doctor_id=?, date=?, time=?, status=?, notes=? WHERE id=?
                """, (pid, did, selected_date[0], time_selected, status_selected, notes, selected_apt[0]))
                read_id = selected_apt[0]
            else:
                db.execute("""
                    INSERT INTO appointments (id, patient_id, doctor_id, date, time, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (apt_id, pid, did, selected_date[0], time_selected, status_selected, notes))
                read_id = apt_id

            # After write, verify by re-reading the saved row. If direct id lookup fails, fallback to selecting by unique fields.
            try:
                saved = db.query("SELECT * FROM appointments WHERE id=?", (read_id,))
                if not saved or len(saved) == 0:
                    # fallback: find by date/time/patient/doctor (new row)
                    fallback = db.query("""
                        SELECT * FROM appointments
                        WHERE date=? AND time=? AND patient_id=? AND doctor_id=?
                        ORDER BY rowid DESC LIMIT 1
                    """, (selected_date[0], time_selected, pid, did))
                    if fallback and len(fallback) > 0:
                        saved = fallback

                if saved and len(saved) > 0:
                    s = saved[0]
                    # canonicalize and compare
                    saved_pid = s.get('patient_id')
                    saved_did = s.get('doctor_id')
                    saved_time = s.get('time')
                    try:
                        ok = (str(int(saved_pid)) == str(int(pid))) and (str(int(saved_did)) == str(int(did))) and (saved_time == time_selected)
                    except Exception:
                        ok = (str(saved_pid) == str(pid)) and (str(saved_did) == str(did)) and (saved_time == time_selected)

                    if ok:
                        messagebox.showinfo("✅ Success", "Appointment saved and verified!")
                    else:
                        messagebox.showwarning("Warning", f"Appointment saved but verification mismatch. Saved patient:{saved_pid} doctor:{saved_did} time:{saved_time}")
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
                 height=45 + module_scale, font=F(14, "bold")).pack(side="left", padx=5, expand=True, fill="x")
    ctk.CTkButton(btn_frame, text="📄 New", command=clear_selection,
                 fg_color="#3498db", hover_color="#2980b9",
                 height=45 + module_scale, font=F(14, "bold")).pack(side="left", padx=5, expand=True, fill="x")

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
                 height=45 + module_scale, font=F(14, "bold")).pack(fill="x", padx=10, pady=(5,8))

    delete_btn = ctk.CTkButton(form_container, text="🗑️ Delete Appointment", command=delete_selected_appointment,
                 fg_color="#c0392b", hover_color="#a93226",
                 height=45 + module_scale, font=F(14, "bold"))
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
