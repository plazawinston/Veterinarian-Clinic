import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

app = None
db = None
refs = {}

def show_diagnosis_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Diagnosis & Medication",
                font=("Arial", 32, "bold"),
                text_color="#2c3e50").pack(pady=20)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(search_frame, text="Search Completed Appointments:",
                font=("Arial", 14, "bold")).pack(side="left", padx=5)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Patient or Owner name...", width=200)
    search_entry.pack(side="left", padx=5)
    
    apt_header = ctk.CTkFrame(left, fg_color="#9b59b6", corner_radius=10)
    apt_header.pack(fill="x", padx=10, pady=(10,5))
    ctk.CTkLabel(apt_header, text="Completed Appointments (Click to Add Diagnosis)",
                font=("Arial", 14, "bold"), text_color="white").pack(pady=10)
    
    apt_container = ctk.CTkScrollableFrame(left, fg_color="transparent", height=250)
    apt_container.pack(fill="both", expand=True, padx=10, pady=5)
    
    selected_apt = [None]
    selected_card = [None]
    
    def load_appointments(search_query=""):
        for w in apt_container.winfo_children():
            w.destroy()
        selected_apt[0] = None
        
        sql = """
            SELECT a.*, p.name as pet_name, p.species, p.owner_name, p.owner_contact,
                   d.name as doctor_name, d.specialization, d.fee
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.status = 'completed'
        """
        params = []
        
        if search_query:
            sql += " AND (p.name LIKE ? OR p.owner_name LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        sql += " ORDER BY a.date DESC, a.time DESC"
        
        appointments = db.query(sql, tuple(params))
        
        if not appointments:
            ctk.CTkLabel(apt_container, text="No completed appointments found.",
                        text_color="gray").pack(pady=20)
            return
        
        for apt in appointments:
            existing_diagnosis = db.query(
                "SELECT id FROM diagnoses WHERE appointment_id = ?", (apt['id'],))
            has_diagnosis = len(existing_diagnosis) > 0
            
            card_color = "#e8f8f5" if has_diagnosis else "#f8f9fa"
            card = ctk.CTkFrame(apt_container, fg_color=card_color, corner_radius=8,
                               border_width=1, border_color="#e0e0e0")
            card.pack(fill="x", padx=5, pady=4)
            
            fee_str = f"P{float(apt['fee']):,.2f}" if apt['fee'] else "P0.00"
            status_text = "Has Diagnosis" if has_diagnosis else "No Diagnosis"
            status_color = "#27ae60" if has_diagnosis else "#e74c3c"
            
            header = f"{apt['date']} {apt['time']} - {apt['pet_name']} ({apt['species']})"
            ctk.CTkLabel(card, text=header, font=("Arial", 12, "bold"),
                        anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
            
            ctk.CTkLabel(card, text=status_text, font=("Arial", 10, "bold"),
                        text_color=status_color).grid(row=0, column=1, sticky="e", padx=10, pady=(8,2))
            
            ctk.CTkLabel(card, text=f"Owner: {apt['owner_name']} | Dr. {apt['doctor_name']} | Fee: {fee_str}",
                        font=("Arial", 10), anchor="w").grid(row=1, column=0, columnspan=2,
                                                            sticky="w", padx=10, pady=(0,8))
            
            def on_card_click(e=None, apt_data=apt, card_ref=card):
                if selected_card[0] and selected_card[0] != card_ref:
                    try:
                        existing = db.query("SELECT id FROM diagnoses WHERE appointment_id = ?",
                                          (selected_apt[0]['id'],)) if selected_apt[0] else []
                        prev_color = "#e8f8f5" if existing else "#f8f9fa"
                        selected_card[0].configure(fg_color=prev_color)
                    except Exception:
                        pass
                
                card_ref.configure(fg_color="#d5dbdb")
                selected_card[0] = card_ref
                selected_apt[0] = apt_data
                
                apt_info_label.configure(
                    text=f"Selected: {apt_data['pet_name']} - {apt_data['date']} {apt_data['time']}")
                
                load_diagnosis_for_appointment(apt_data['id'])
            
            card.bind("<Button-1>", on_card_click)
            for child in card.winfo_children():
                child.bind("<Button-1>", on_card_click)
    
    ctk.CTkButton(search_frame, text="Search",
                 command=lambda: load_appointments(search_entry.get()),
                 fg_color="#9b59b6", width=80).pack(side="left", padx=5)
    
    ctk.CTkButton(search_frame, text="Clear",
                 command=lambda: [search_entry.delete(0, "end"), load_appointments()],
                 fg_color="#95a5a6", width=80).pack(side="left", padx=5)
    
    diag_header = ctk.CTkFrame(left, fg_color="#3498db", corner_radius=10)
    diag_header.pack(fill="x", padx=10, pady=(10,5))
    ctk.CTkLabel(diag_header, text="Diagnosis History",
                font=("Arial", 14, "bold"), text_color="white").pack(pady=10)
    
    diag_container = ctk.CTkScrollableFrame(left, fg_color="transparent", height=200)
    diag_container.pack(fill="both", expand=True, padx=10, pady=(5,10))
    
    selected_diagnosis = [None]
    
    def load_diagnosis_for_appointment(apt_id):
        for w in diag_container.winfo_children():
            w.destroy()
        selected_diagnosis[0] = None
        
        diagnoses = db.query("""
            SELECT diag.*, d.name as doctor_name, p.name as pet_name
            FROM diagnoses diag
            JOIN doctors d ON diag.doctor_id = d.id
            JOIN patients p ON diag.patient_id = p.id
            WHERE diag.appointment_id = ?
            ORDER BY diag.created_at DESC
        """, (apt_id,))
        
        if not diagnoses:
            ctk.CTkLabel(diag_container, text="No diagnosis recorded for this appointment.",
                        text_color="gray").pack(pady=20)
            diagnosis_text.delete("1.0", "end")
            load_medications(None)
            return
        
        for diag in diagnoses:
            card = ctk.CTkFrame(diag_container, fg_color="#f0f9ff", corner_radius=8,
                               border_width=1, border_color="#3498db")
            card.pack(fill="x", padx=5, pady=4)
            
            ctk.CTkLabel(card, text=f"Date: {diag['diagnosis_date']} | Dr. {diag['doctor_name']}",
                        font=("Arial", 11, "bold"), anchor="w").grid(row=0, column=0,
                                                                    sticky="w", padx=10, pady=(8,2))
            
            ctk.CTkLabel(card, text=f"Diagnosis: {diag['diagnosis_text'][:100]}...",
                        font=("Arial", 10), anchor="w", wraplength=400).grid(row=1, column=0,
                                                                              sticky="w", padx=10, pady=(0,8))
            
            def on_diag_click(e=None, diag_data=diag, card_ref=card):
                selected_diagnosis[0] = diag_data
                diagnosis_text.delete("1.0", "end")
                diagnosis_text.insert("1.0", diag_data['diagnosis_text'])
                load_medications(diag_data['id'])
            
            card.bind("<Button-1>", on_diag_click)
            for child in card.winfo_children():
                child.bind("<Button-1>", on_diag_click)
        
        if diagnoses:
            selected_diagnosis[0] = diagnoses[0]
            diagnosis_text.delete("1.0", "end")
            diagnosis_text.insert("1.0", diagnoses[0]['diagnosis_text'])
            load_medications(diagnoses[0]['id'])
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=500)
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)
    
    ctk.CTkLabel(right, text="Diagnosis Entry", font=("Arial", 20, "bold"),
                text_color="#2c3e50").pack(pady=15)
    
    apt_info_label = ctk.CTkLabel(right, text="Select an appointment from the left panel",
                                  font=("Arial", 11), text_color="#7f8c8d")
    apt_info_label.pack(anchor="w", padx=15)
    
    form_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
    form_container.pack(fill="both", expand=True, padx=15, pady=10)
    
    ctk.CTkLabel(form_container, text="Diagnosis:",
                font=("Arial", 13, "bold"), text_color="#2c3e50").pack(anchor="w", pady=(10,5))
    diagnosis_text = ctk.CTkTextbox(form_container, height=100, font=("Arial", 11),
                                    fg_color="#f8f9fa", border_width=2, border_color="#dee2e6")
    diagnosis_text.pack(fill="x", pady=(0,10))
    
    med_header = ctk.CTkFrame(form_container, fg_color="#e67e22", corner_radius=8)
    med_header.pack(fill="x", pady=(10,5))
    ctk.CTkLabel(med_header, text="Medications", font=("Arial", 13, "bold"),
                text_color="white").pack(pady=8)
    
    med_input_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    med_input_frame.pack(fill="x", pady=5)
    
    ctk.CTkLabel(med_input_frame, text="Medicine Name:", font=("Arial", 11)).grid(row=0, column=0,
                                                                                   sticky="w", padx=5)
    medicine_entry = ctk.CTkEntry(med_input_frame, placeholder_text="Medicine name...", width=200)
    medicine_entry.grid(row=0, column=1, padx=5, pady=5)
    
    ctk.CTkLabel(med_input_frame, text="Price (P):", font=("Arial", 11)).grid(row=1, column=0,
                                                                               sticky="w", padx=5)
    price_entry = ctk.CTkEntry(med_input_frame, placeholder_text="0.00", width=100)
    price_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    
    ctk.CTkLabel(med_input_frame, text="Qty:", font=("Arial", 11)).grid(row=1, column=2,
                                                                        sticky="w", padx=5)
    qty_entry = ctk.CTkEntry(med_input_frame, placeholder_text="1", width=50)
    qty_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)
    qty_entry.insert(0, "1")
    
    med_list_frame = ctk.CTkScrollableFrame(form_container, height=120, fg_color="#fdf2e9")
    med_list_frame.pack(fill="x", pady=10)
    
    medications_data = []
    
    def load_medications(diagnosis_id):
        for w in med_list_frame.winfo_children():
            w.destroy()
        medications_data.clear()
        
        if not diagnosis_id:
            ctk.CTkLabel(med_list_frame, text="No medications yet",
                        text_color="gray").pack(pady=10)
            update_total()
            return
        
        meds = db.query("SELECT * FROM medications WHERE diagnosis_id = ? ORDER BY id",
                       (diagnosis_id,))
        
        if not meds:
            ctk.CTkLabel(med_list_frame, text="No medications prescribed",
                        text_color="gray").pack(pady=10)
            update_total()
            return
        
        for med in meds:
            medications_data.append(dict(med))
            med_row = ctk.CTkFrame(med_list_frame, fg_color="#fff5eb", corner_radius=5)
            med_row.pack(fill="x", padx=5, pady=2)
            
            price = float(med['price']) if med['price'] else 0.0
            qty = int(med['quantity']) if med['quantity'] else 1
            subtotal = price * qty
            
            ctk.CTkLabel(med_row, text=f"{med['medicine_name']} x{qty}",
                        font=("Arial", 11), anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(med_row, text=f"P{subtotal:,.2f}",
                        font=("Arial", 11, "bold"), anchor="e").pack(side="right", padx=10, pady=5)
            
            def delete_med(mid=med['id']):
                if messagebox.askyesno("Confirm", "Delete this medication?"):
                    db.execute("DELETE FROM medications WHERE id = ?", (mid,))
                    if selected_diagnosis[0]:
                        load_medications(selected_diagnosis[0]['id'])
            
            ctk.CTkButton(med_row, text="X", width=25, height=25, fg_color="#e74c3c",
                         command=delete_med).pack(side="right", padx=5, pady=5)
        
        update_total()
    
    total_label = ctk.CTkLabel(form_container, text="Medication Total: P0.00",
                               font=("Arial", 14, "bold"), text_color="#e67e22")
    total_label.pack(anchor="e", pady=5)
    
    def update_total():
        total = sum(float(m.get('price', 0)) * int(m.get('quantity', 1)) for m in medications_data)
        total_label.configure(text=f"Medication Total: P{total:,.2f}")
    
    def add_medication():
        if not selected_diagnosis[0]:
            messagebox.showerror("Error", "Please save a diagnosis first before adding medications.")
            return
        
        med_name = medicine_entry.get().strip()
        price_str = price_entry.get().strip()
        qty_str = qty_entry.get().strip()
        
        if not med_name:
            messagebox.showerror("Error", "Please enter medicine name.")
            return
        
        try:
            price = float(price_str) if price_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "Invalid price format.")
            return
        
        try:
            qty = int(qty_str) if qty_str else 1
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity format.")
            return
        
        db.execute("""
            INSERT INTO medications (diagnosis_id, medicine_name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (selected_diagnosis[0]['id'], med_name, qty, price))
        
        medicine_entry.delete(0, "end")
        price_entry.delete(0, "end")
        qty_entry.delete(0, "end")
        qty_entry.insert(0, "1")
        
        load_medications(selected_diagnosis[0]['id'])
        messagebox.showinfo("Success", f"Medication '{med_name}' added successfully!")
    
    ctk.CTkButton(med_input_frame, text="Add Medication", command=add_medication,
                 fg_color="#e67e22", width=120).grid(row=2, column=0, columnspan=4, pady=10)
    
    def save_diagnosis():
        if not selected_apt[0]:
            messagebox.showerror("Error", "Please select an appointment first.")
            return
        
        diag_text = diagnosis_text.get("1.0", "end").strip()
        if not diag_text:
            messagebox.showerror("Error", "Please enter a diagnosis.")
            return
        
        apt = selected_apt[0]
        today = datetime.now().strftime('%Y-%m-%d')
        
        if selected_diagnosis[0] and selected_diagnosis[0]['appointment_id'] == apt['id']:
            db.execute("""
                UPDATE diagnoses SET diagnosis_text = ?, diagnosis_date = ?
                WHERE id = ?
            """, (diag_text, today, selected_diagnosis[0]['id']))
            messagebox.showinfo("Success", "Diagnosis updated successfully!")
        else:
            existing = db.query("SELECT id FROM diagnoses WHERE appointment_id = ?", (apt['id'],))
            if existing:
                if messagebox.askyesno("Existing Diagnosis",
                                       "A diagnosis already exists for this appointment. Update it?"):
                    db.execute("""
                        UPDATE diagnoses SET diagnosis_text = ?, diagnosis_date = ?
                        WHERE appointment_id = ?
                    """, (diag_text, today, apt['id']))
                    messagebox.showinfo("Success", "Diagnosis updated successfully!")
                else:
                    return
            else:
                diag_id = db.execute_returning_id("""
                    INSERT INTO diagnoses (appointment_id, patient_id, doctor_id, diagnosis_text, diagnosis_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (apt['id'], apt['patient_id'], apt['doctor_id'], diag_text, today))
                
                selected_diagnosis[0] = {
                    'id': diag_id,
                    'appointment_id': apt['id'],
                    'patient_id': apt['patient_id'],
                    'doctor_id': apt['doctor_id'],
                    'diagnosis_text': diag_text,
                    'diagnosis_date': today
                }
                messagebox.showinfo("Success", "Diagnosis saved successfully! You can now add medications.")
        
        load_appointments(search_entry.get())
        load_diagnosis_for_appointment(apt['id'])
    
    def print_medical_certificate():
        if not selected_apt[0] or not selected_diagnosis[0]:
            messagebox.showerror("Error", "Please select an appointment with a diagnosis first.")
            return
        
        apt = selected_apt[0]
        diag = selected_diagnosis[0]
        
        patient = db.query("SELECT * FROM patients WHERE id = ?", (apt['patient_id'],))
        doctor = db.query("SELECT * FROM doctors WHERE id = ?", (apt['doctor_id'],))
        
        if not patient or not doctor:
            messagebox.showerror("Error", "Could not retrieve patient or doctor information.")
            return
        
        patient = patient[0]
        doctor = doctor[0]
        
        meds = db.query("SELECT * FROM medications WHERE diagnosis_id = ?", (diag['id'],))
        
        lines = []
        lines.append("=" * 70)
        lines.append("                    VET CLINIC MANAGEMENT SYSTEM")
        lines.append("                      MEDICAL CERTIFICATE")
        lines.append("=" * 70)
        lines.append(f"Certificate Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("-" * 70)
        lines.append("")
        lines.append("PATIENT INFORMATION:")
        lines.append(f"  Pet Name:     {patient['name']}")
        lines.append(f"  Species:      {patient['species']}")
        lines.append(f"  Breed:        {patient['breed'] or 'N/A'}")
        lines.append(f"  Age:          {patient['age'] or 'N/A'}")
        lines.append("")
        lines.append("OWNER INFORMATION:")
        lines.append(f"  Owner Name:   {patient['owner_name']}")
        lines.append(f"  Contact:      {patient['owner_contact']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("ATTENDING VETERINARIAN:")
        lines.append(f"  Name:           {doctor['name']}")
        lines.append(f"  Specialization: {doctor['specialization']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("APPOINTMENT DETAILS:")
        lines.append(f"  Date:    {apt['date']}")
        lines.append(f"  Time:    {apt['time']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("DIAGNOSIS:")
        lines.append(f"  {diag['diagnosis_text']}")
        lines.append("")
        
        if meds:
            lines.append("-" * 70)
            lines.append("PRESCRIBED MEDICATIONS:")
            med_total = 0.0
            for idx, med in enumerate(meds, 1):
                price = float(med['price']) if med['price'] else 0.0
                qty = int(med['quantity']) if med['quantity'] else 1
                subtotal = price * qty
                med_total += subtotal
                lines.append(f"  {idx}. {med['medicine_name']}")
                lines.append(f"     Quantity: {qty} | Unit Price: P{price:,.2f} | Subtotal: P{subtotal:,.2f}")
            lines.append("")
            lines.append(f"  MEDICATION TOTAL: P{med_total:,.2f}")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("")
        lines.append("This is to certify that the above-mentioned patient has been")
        lines.append("examined and diagnosed at our veterinary clinic.")
        lines.append("")
        lines.append("")
        lines.append("_______________________________")
        lines.append(f"         {doctor['name']}")
        lines.append(f"     Licensed Veterinarian")
        lines.append("")
        lines.append("=" * 70)
        lines.append("This is a computer-generated medical certificate.")
        lines.append("=" * 70)
        
        certificate_text = "\n".join(lines)
        
        try:
            filename = f"medical_certificate_{apt['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(certificate_text)
            messagebox.showinfo("Success",
                              f"Medical Certificate saved to {filename}\n\nYou can print this file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save certificate: {str(e)}")
    
    btn_frame = ctk.CTkFrame(right, fg_color="transparent")
    btn_frame.pack(fill="x", padx=15, pady=(0,15))
    
    ctk.CTkButton(btn_frame, text="Save Diagnosis", command=save_diagnosis,
                 fg_color="#2ecc71", height=40).pack(side="left", padx=5, expand=True, fill="x")
    
    ctk.CTkButton(btn_frame, text="Print Certificate", command=print_medical_certificate,
                 fg_color="#3498db", height=40).pack(side="left", padx=5, expand=True, fill="x")
    
    def clear_form():
        diagnosis_text.delete("1.0", "end")
        medicine_entry.delete(0, "end")
        price_entry.delete(0, "end")
        qty_entry.delete(0, "end")
        qty_entry.insert(0, "1")
        selected_diagnosis[0] = None
        apt_info_label.configure(text="Select an appointment from the left panel")
        for w in med_list_frame.winfo_children():
            w.destroy()
        medications_data.clear()
        update_total()
    
    ctk.CTkButton(btn_frame, text="Clear", command=clear_form,
                 fg_color="#95a5a6", height=40).pack(side="left", padx=5, expand=True, fill="x")
    
    load_appointments()

def diagnosis(parent):
    """Compatibility alias: older code may call diagnosis(parent)."""
    return show_diagnosis_view(parent)
