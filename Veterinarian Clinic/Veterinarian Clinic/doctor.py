"""
Doctor Module - Doctor View and Patient Management for Vet Clinic Management System.

This module provides doctor-focused views with:
- Doctor selection
- View all patients of selected doctor with history
- Calendar showing doctor's appointments with color coding
- Green for completed appointments
- Yellow for upcoming appointments
"""

import customtkinter as ctk
from tkcalendar import Calendar
from datetime import datetime, date

app = None
db = None
refs = {}

def show_doctor_view(parent):
    """Display doctor view with appointment calendar only (patient list removed)."""
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Doctor View", font=("Arial", 32, "bold"),
                text_color="#2c3e50").pack(pady=20)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Left side - Doctor selection only (patient/history removed)
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=15, border_width=2, border_color="#e0e0e0")
    left.pack(side="left", fill="y", expand=False, padx=(0, 15))
    
    # Doctor selection
    doctor_frame = ctk.CTkFrame(left, fg_color="transparent")
    doctor_frame.pack(fill="x", padx=15, pady=15)
    
    ctk.CTkLabel(doctor_frame, text="Select Doctor:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))
    
    # populate doctor dropdown and include specialization (and fee) in the visible text
    try:
        doctors = db.query("SELECT * FROM doctors ORDER BY id ASC")
    except Exception:
        doctors = []

    doctor_options = []
    for d in doctors:
        # convert sqlite3.Row to plain dict so .get() works reliably
        row = dict(d)
        try:
            fee_val = row.get('fee', 0)
            fee_str = f"₱{float(fee_val):,.2f}"
        except Exception:
            # fallback to a safe string representation
            fee_raw = row.get('fee', '')
            fee_str = f"₱{fee_raw}"
        spec = row.get('specialization', '') or ''
        doctor_options.append(f"{row.get('id')}: {row.get('name')} — {spec} ({fee_str})")
    
    selected_doctor = [None]
    doctor_var = ctk.StringVar(value=doctor_options[0] if doctor_options else "")
    def on_doctor_select(choice):
        if not choice or ':' not in choice:
            return
        try:
            selected_doctor[0] = int(choice.split(':', 1)[0].strip())
        except Exception:
            selected_doctor[0] = choice.split(':', 1)[0].strip()
        try:
            refresh_calendar()
        except Exception:
            pass

    doctor_dd = ctk.CTkComboBox(doctor_frame, variable=doctor_var, values=doctor_options,
                               state="readonly", command=on_doctor_select, font=("Arial", 12))
    doctor_dd.pack(fill="x", pady=(0, 10))
    
    ctk.CTkLabel(left, text="Calendar shows color-coded days.\nGreen = completed, Yellow = upcoming",
                font=("Arial", 11), text_color="#7f8c8d", wraplength=180, justify="left").pack(padx=15, pady=(0,10))
    
    # Right side - Calendar with appointment color coding and day details
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=15, border_width=2, border_color="#e0e0e0")
    right.pack(side="right", fill="both", expand=True, padx=(15, 0))
    
    cal_header = ctk.CTkFrame(right, fg_color="#3498db", corner_radius=15, height=50)
    cal_header.pack(fill="x", padx=15, pady=15)
    ctk.CTkLabel(cal_header, text="Appointment Calendar", font=("Arial", 14, "bold"),
                text_color="white").pack(pady=10)
    
    # calendar container with larger calendar + day details side-by-side
    calendar_container = ctk.CTkFrame(right, fg_color="transparent")
    calendar_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    cal_holder = ctk.CTkFrame(calendar_container, fg_color="white", corner_radius=8)
    cal_holder.pack(side="left", fill="y", padx=(0,10), pady=5)
    
    # Larger calendar (fixed display size) for better visibility
    calendar = Calendar(cal_holder, selectmode='day', date_pattern='yyyy-mm-dd',
                       background='#3498db', foreground='white',
                       selectbackground='#e74c3c', headersbackground='#2c3e50',
                       normalbackground='white', normalforeground='#2c3e50',
                       weekendbackground='#ecf0f1', weekendforeground='#2c3e50',
                       font=('Arial', 12), headersforeground='white', borderwidth=2,
                       width=420, height=380)
    calendar.pack(padx=8, pady=8)
    
    # Right-side pane shows appointments for the selected day
    day_details = ctk.CTkFrame(calendar_container, fg_color="white", corner_radius=8, border_width=1, border_color="#e0e0e0")
    day_details.pack(side="right", fill="both", expand=True, pady=5)
    
    ctk.CTkLabel(day_details, text="Appointments for Selected Day", font=("Arial", 13, "bold"),
                text_color="#2c3e50").pack(anchor="w", padx=12, pady=(12,6))
    day_list = ctk.CTkScrollableFrame(day_details, height=300)
    day_list.pack(fill="both", expand=True, padx=12, pady=(0,12))
    
    def show_day_appointments(date_str):
        # populate the right pane with appointments for the selected doctor and date
        for w in day_list.winfo_children():
            w.destroy()
        if not selected_doctor[0]:
            ctk.CTkLabel(day_list, text="Select a doctor to view appointments", font=("Arial", 11), text_color="gray").pack(pady=10)
            return
        try:
            apts = db.query("""
                SELECT a.*, p.name as pet_name, d.name as doctor_name, d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.doctor_id = ? AND a.date = ? AND a.status <> ?
                ORDER BY a.time
            """, (selected_doctor[0], date_str, 'cancelled'))
        except Exception:
            apts = []

        if not apts:
            ctk.CTkLabel(day_list, text="No appointments for this day", font=("Arial", 11), text_color="gray").pack(pady=10)
            return

        for apt in apts:
            card = ctk.CTkFrame(day_list, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e6e6e6")
            card.pack(fill="x", pady=6, padx=6)
            time_label = apt['time'] or ""
            status = apt['status'] or ""
            status_color = "#27ae60" if status == "completed" else "#f39c12" if status == "scheduled" else "#95a5a6"
            # top line: time, pet, status
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=8, pady=(8,4))
            ctk.CTkLabel(top, text=f"{time_label}", font=("Arial", 12, "bold"), text_color="#2c3e50").pack(side="left")
            ctk.CTkLabel(top, text=f"{apt['pet_name']}", font=("Arial", 11), text_color="#2c3e50").pack(side="left", padx=(12,0))
            ctk.CTkLabel(top, text=f"{status.capitalize()}", font=("Arial", 10, "bold"), text_color="white",
                         fg_color=status_color, corner_radius=6).pack(side="right")
            # second line: doctor & notes
            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=8, pady=(0,8))
            ctk.CTkLabel(bottom, text=f"Dr. {apt['doctor_name']} ({apt['specialization']})", font=("Arial", 10), text_color="#7f8c8d").pack(anchor="w")
            notes = apt['notes'] if 'notes' in apt.keys() else None
            if notes:
                ctk.CTkLabel(bottom, text=f"Notes: {notes}", font=("Arial", 10), text_color="#7f8c8d", wraplength=360, justify="left").pack(anchor="w", pady=(4,0))

    # refresh_calendar updates calendar tags and the day pane
    def refresh_calendar():
        if not selected_doctor[0]:
            # clear events and day pane when no doctor selected
            calendar.calevent_remove('all')
            for w in day_list.winfo_children():
                w.destroy()
            return
        try:
            apts = db.query("""
                SELECT date, status FROM appointments
                WHERE doctor_id=? AND status<>?
                ORDER BY date
            """, (selected_doctor[0], 'cancelled'))
        except Exception:
            apts = []

        # remove existing events
        calendar.calevent_remove('all')
        completed_dates = set()
        upcoming_dates = set()
        for apt in apts:
            try:
                apt_date = datetime.strptime(apt['date'], '%Y-%m-%d').date()
                if apt['status'] == 'completed':
                    completed_dates.add(apt_date)
                else:
                    upcoming_dates.add(apt_date)
            except:
                pass

        if completed_dates:
            calendar.tag_config('completed', background='#27ae60', foreground='white')
            for d in completed_dates:
                calendar.calevent_create(d, 'Completed', 'completed')
        if upcoming_dates:
            calendar.tag_config('upcoming', background='#f39c12', foreground='white')
            for d in upcoming_dates:
                calendar.calevent_create(d, 'Upcoming', 'upcoming')

        # show appointments for the currently selected calendar date
        try:
            sel_date = calendar.get_date()
            show_day_appointments(sel_date)
        except Exception:
            pass

    # bind selection event so clicking a day updates the right pane
    calendar.bind("<<CalendarSelected>>", lambda e: show_day_appointments(calendar.get_date()))
     
    # Initialize with first doctor and today's view
    if doctor_options:
        selected_doctor[0] = int(doctor_options[0].split(':')[0].strip())
        refresh_calendar()
        # ensure a date is selected and day details are shown
        try:
            calendar.selection_set(datetime.today().date())
            show_day_appointments(calendar.get_date())
        except Exception:
            pass
