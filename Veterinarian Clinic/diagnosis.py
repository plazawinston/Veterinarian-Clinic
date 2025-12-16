"""
CLASS : 4
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from abc import ABC, abstractmethod

app = None
db = None
refs = {}


## Normalize doctor display name (avoid doubling 'Dr.' prefix)
def format_doctor_name(name):
    """Avoid doubling the 'Dr.' prefix when doctor name already includes it."""
    if not name:
        return ""
    n = str(name).strip()
    if n.lower().startswith("dr"):
        return n
    return f"Dr. {n}"


## Abstract base for diagnosis records
class DiagnosisBase(ABC):
    def __init__(self, id=None, appointment_id=None, patient_id=None, doctor_id=None, diagnosis_text=None, diagnosis_date=None):
        self.id = id
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.diagnosis_text = diagnosis_text
        self.diagnosis_date = diagnosis_date

    @abstractmethod
    ## Persist the diagnosis (override in concrete classes)
    def save(self):
        raise NotImplementedError()

    @abstractmethod
    ## Remove the diagnosis record (override in concrete classes)
    def delete(self):
        raise NotImplementedError()


## Concrete diagnosis model: save and delete operations
class Diagnosis(DiagnosisBase):
    ## Save new or update existing diagnosis row
    def save(self):
        today = datetime.now().strftime('%Y-%m-%d')
        if self.id:
            db.execute("""
                UPDATE diagnoses SET diagnosis_text = ?, diagnosis_date = ? WHERE id = ?
            """, (self.diagnosis_text, today, self.id))
        else:
            diag_id = db.execute_returning_id("""
                INSERT INTO diagnoses (appointment_id, patient_id, doctor_id, diagnosis_text, diagnosis_date)
                VALUES (?, ?, ?, ?, ?)
            """, (self.appointment_id, self.patient_id, self.doctor_id, self.diagnosis_text, today))
            self.id = diag_id
            self.diagnosis_date = today

    ## Delete diagnosis from database
    def delete(self):
        if not self.id:
            raise ValueError('Diagnosis id required')
        db.execute("DELETE FROM diagnoses WHERE id = ?", (self.id,))


## Medication model for prescribed medicines
class Medication:
    def __init__(self, id=None, diagnosis_id=None, medicine_name=None, quantity=1, price=0.0):
        self.id = id
        self.diagnosis_id = diagnosis_id
        self.medicine_name = medicine_name
        self.quantity = int(quantity or 1)
        self.price = float(price or 0.0)

    ## Insert or update a medication row
    def save(self):
        if self.id:
            db.execute("UPDATE medications SET medicine_name=?, quantity=?, price=? WHERE id = ?",
                       (self.medicine_name, self.quantity, self.price, self.id))
        else:
            self.id = db.execute_returning_id(
                "INSERT INTO medications (diagnosis_id, medicine_name, quantity, price) VALUES (?, ?, ?, ?)",
                (self.diagnosis_id, self.medicine_name, self.quantity, self.price)
            )

    ## Remove medication row
    def delete(self):
        if not self.id:
            return
        db.execute("DELETE FROM medications WHERE id = ?", (self.id,))

    @staticmethod
    ## List medications for a given diagnosis id
    def list_for_diagnosis(diagnosis_id):
        return db.query("SELECT * FROM medications WHERE diagnosis_id = ? ORDER BY id", (diagnosis_id,))


class DiagnosisView:
    """Helper class to encapsulate diagnosis-related DB operations.
    This keeps UI code intact while providing encapsulated methods for save/add/delete logic.
    """
    ## Save or update diagnosis logic used by the UI
    def save_diagnosis_logic(self, apt, diag_text, selected_diagnosis):
        today = datetime.now().strftime('%Y-%m-%d')
        if selected_diagnosis:
            # Convert sqlite3.Row to dict if needed
            diag_dict = dict(selected_diagnosis) if hasattr(selected_diagnosis, 'keys') else selected_diagnosis
            if diag_dict.get('appointment_id') == apt['id']:
                db.execute("""
                    UPDATE diagnoses SET diagnosis_text = ?, diagnosis_date = ?
                    WHERE id = ?
                """, (diag_text, today, diag_dict['id']))
                return {'updated': True}
        
        existing = db.query("SELECT id FROM diagnoses WHERE appointment_id = ?", (apt['id'],))
        if existing:
            db.execute("""
                UPDATE diagnoses SET diagnosis_text = ?, diagnosis_date = ?
                WHERE appointment_id = ?
            """, (diag_text, today, apt['id']))
            return {'updated': True}
        else:
            diag_id = db.execute_returning_id("""
                INSERT INTO diagnoses (appointment_id, patient_id, doctor_id, diagnosis_text, diagnosis_date)
                VALUES (?, ?, ?, ?, ?)
            """, (apt['id'], apt['patient_id'], apt['doctor_id'], diag_text, today))
            return {
                'created': True,
                'id': diag_id,
                'appointment_id': apt['id'],
                'patient_id': apt['patient_id'],
                'doctor_id': apt['doctor_id'],
                'diagnosis_text': diag_text,
                'diagnosis_date': today
            }

    ## Add medication to a diagnosis, update inventory stock
    def add_medication_logic(self, diagnosis_id, med_name, price, qty):
        # Check inventory
        inv = db.query("SELECT * FROM medicines WHERE name = ?", (med_name,))
        if not inv:
            return {'ok': False, 'error': f"Medicine '{med_name}' not found in inventory. Please register it in Medicines view first."}
        inv = inv[0]
        available = int(inv['stock'] or 0)
        if qty > available:
            return {'ok': False, 'error': f"Requested quantity ({qty}) exceeds available stock ({available})."}
        try:
            db.execute("INSERT INTO medications (diagnosis_id, medicine_name, quantity, price) VALUES (?, ?, ?, ?)",
                       (diagnosis_id, med_name, qty, price))
            db.execute("UPDATE medicines SET stock = stock - ? WHERE id = ?", (qty, inv['id']))
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    ## Delete medication and restore inventory stock
    def delete_med_logic(self, med_id):
        try:
            mrow = db.query("SELECT * FROM medications WHERE id = ?", (med_id,))
            if mrow:
                mrow = mrow[0]
                med_name = mrow['medicine_name']
                qty = int(mrow['quantity'] or 0)
                inv = db.query("SELECT * FROM medicines WHERE name = ?", (med_name,))
                if inv:
                    db.execute("UPDATE medicines SET stock = stock + ? WHERE name = ?", (qty, med_name))
            db.execute("DELETE FROM medications WHERE id = ?", (med_id,))
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}


def show_diagnosis_view(parent):
    ## Build and display the diagnosis UI (left: completed appts, right: entry)
    for w in parent.winfo_children():
        w.destroy()
    
    # Slight scale increase for this module
    module_scale = 4
    ## Font helper for this module
    def F(size, weight=None):
        s = int(size + module_scale)
        return ("Arial", s, weight) if weight else ("Arial", s)
    
    ctk.CTkLabel(parent, text="Diagnosis & Medication",
                font=F(32, "bold"),
                text_color="#2c3e50").pack(pady=20 + module_scale)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(search_frame, text="Search Completed Appointments:",
                font=F(14, "bold")).pack(side="left", padx=5)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Patient or Owner name...", width=240 + module_scale*6, font=F(12))
    search_entry.pack(side="left", padx=5)
    
    apt_header = ctk.CTkFrame(left, fg_color="#9b59b6", corner_radius=10)
    apt_header.pack(fill="x", padx=10, pady=(10,5))
    ctk.CTkLabel(apt_header, text="Completed Appointments (Click to Add Diagnosis)",
                font=F(14, "bold"), text_color="white").pack(pady=10)
    
    apt_container = ctk.CTkScrollableFrame(left, fg_color="transparent", height=260 + module_scale*6)
    apt_container.pack(fill="both", expand=True, padx=10, pady=5)
    
    selected_apt = [None]
    selected_card = [None]
    
    ## Load completed appointments for selection and display
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
                        text_color="gray", font=F(12)).pack(pady=20)
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
            ctk.CTkLabel(card, text=header, font=F(13, "bold"),
                        anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
            
            ctk.CTkLabel(card, text=status_text, font=F(11, "bold"),
                        text_color=status_color).grid(row=0, column=1, sticky="e", padx=10, pady=(8,2))
            
            ctk.CTkLabel(card, text=f"Owner: {apt['owner_name']} | {apt['doctor_name']} | Fee: {fee_str}",
                        font=F(11), anchor="w").grid(row=1, column=0, columnspan=2,
                                                            sticky="w", padx=10, pady=(0,8))
            
            ## When appointment card clicked, select and load diagnosis
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
                    text=f"Selected: {apt_data['pet_name']} - {apt_data['date']} {apt_data['time']}", font=F(11))
                
                load_diagnosis_for_appointment(apt_data['id'])
            
            card.bind("<Button-1>", on_card_click)
            for child in card.winfo_children():
                child.bind("<Button-1>", on_card_click)
    
    ctk.CTkButton(search_frame, text="Search",
                 command=lambda: load_appointments(search_entry.get()),
                 fg_color="#9b59b6", width=90 + module_scale*4, height=34 + module_scale).pack(side="left", padx=5)
    
    ctk.CTkButton(search_frame, text="Clear",
                 command=lambda: [search_entry.delete(0, "end"), load_appointments()],
                 fg_color="#95a5a6", width=90 + module_scale*4, height=34 + module_scale).pack(side="left", padx=5)
    
    diag_header = ctk.CTkFrame(left, fg_color="#3498db", corner_radius=10)
    diag_header.pack(fill="x", padx=10, pady=(10,5))
    ctk.CTkLabel(diag_header, text="Diagnosis Summary",
                font=F(14, "bold"), text_color="white").pack(pady=10)
    
    diag_container = ctk.CTkScrollableFrame(left, fg_color="transparent", height=220 + module_scale*4)
    diag_container.pack(fill="both", expand=True, padx=10, pady=(5,10))
    
    selected_diagnosis = [None]
    
    ## Load diagnoses for a selected appointment and display summaries
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
            ORDER BY diag.diagnosis_date DESC, diag.id DESC
        """, (apt_id,))
        
        if not diagnoses:
            ctk.CTkLabel(diag_container, text="No diagnosis recorded for this appointment.",
                        text_color="gray", font=F(12)).pack(pady=20)
            diagnosis_text.delete("1.0", "end")
            load_medications(None)
            return
        
        for diag in diagnoses:
            # Get medications for this diagnosis
            meds = db.query("SELECT * FROM medications WHERE diagnosis_id = ? ORDER BY id",
                           (diag['id'],))
            med_count = len(meds) if meds else 0
            
            card = ctk.CTkFrame(diag_container, fg_color="#f0f9ff", corner_radius=8,
                               border_width=2, border_color="#3498db")
            card.pack(fill="x", padx=5, pady=6)
            
            # Header with date and doctor
            header_frame = ctk.CTkFrame(card, fg_color="#e3f2fd", corner_radius=6)
            header_frame.pack(fill="x", padx=8, pady=(8,4))
            
            ctk.CTkLabel(header_frame, text=f"Date: {diag['diagnosis_date']} | {format_doctor_name(diag['doctor_name'])}",
                        font=F(12, "bold"), anchor="w").pack(side="left", padx=10, pady=8)
            
            # Medication count badge
            if med_count > 0:
                ctk.CTkLabel(header_frame, text=f"📋 {med_count} medication(s)",
                            font=F(11, "bold"), text_color="#e67e22").pack(side="right", padx=10, pady=8)
            
            # Diagnosis text
            ctk.CTkLabel(card, text=f"Diagnosis: {diag['diagnosis_text'][:250]}{'...' if len(diag['diagnosis_text']) > 250 else ''}",
                        font=F(11), anchor="nw", wraplength=520 + module_scale*20, justify="left").pack(fill="x", padx=10, pady=(4,8))
            
            # Medications for this diagnosis
            if meds:
                med_frame = ctk.CTkFrame(card, fg_color="#fff5eb", corner_radius=6)
                med_frame.pack(fill="x", padx=8, pady=(0,8))
                
                ctk.CTkLabel(med_frame, text="Medications prescribed:", font=F(10, "bold"),
                            text_color="#e67e22").pack(anchor="w", padx=8, pady=(6,4))
                
                for med in meds:
                    price = float(med['price']) if med['price'] else 0.0
                    qty = int(med['quantity']) if med['quantity'] else 1
                    subtotal = price * qty
                    
                    ctk.CTkLabel(med_frame, 
                                text=f"  • {med['medicine_name']} x{qty} - ₱{subtotal:,.2f}",
                                font=F(10), anchor="w").pack(anchor="w", padx=12, pady=2)
            
            ## Select a diagnosis entry and populate right-hand form
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
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=540 + module_scale*8)
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)
    
    ctk.CTkLabel(right, text="Diagnosis Entry", font=F(20, "bold"),
                text_color="#2c3e50").pack(pady=15)
    
    apt_info_label = ctk.CTkLabel(right, text="Select an appointment from the left panel",
                                  font=F(11), text_color="#7f8c8d")
    apt_info_label.pack(anchor="w", padx=15)
    
    form_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
    form_container.pack(fill="both", expand=True, padx=15, pady=10)
    
    ctk.CTkLabel(form_container, text="Diagnosis:",
                font=F(13, "bold"), text_color="#2c3e50").pack(anchor="w", pady=(10,5))
    diagnosis_text = ctk.CTkTextbox(form_container, height=120 + module_scale*8, font=F(12),
                                    fg_color="#f8f9fa", border_width=2, border_color="#dee2e6")
    diagnosis_text.pack(fill="x", pady=(0,10))
    
    med_header = ctk.CTkFrame(form_container, fg_color="#e67e22", corner_radius=8)
    med_header.pack(fill="x", pady=(10,5))
    ctk.CTkLabel(med_header, text="Medications", font=F(13, "bold"),
                text_color="white").pack(pady=8)
    
    med_input_frame = ctk.CTkFrame(form_container, fg_color="transparent")
    med_input_frame.pack(fill="x", pady=5)
    
    ctk.CTkLabel(med_input_frame, text="Select medicine from the list below:", font=F(11)).grid(row=0, column=0,
                                                                                   sticky="w", padx=5)
    selected_med_display = [None]

    # Scrollable browser for medicines (shows name and use). Clicking sets selection and autofills price.
    med_browser_frame = ctk.CTkScrollableFrame(med_input_frame, height=180 + module_scale*6, fg_color="#fdf2e9")
    med_browser_frame.grid(row=1, column=0, columnspan=5, pady=(8,0), sticky="we")

    # price and qty placed below the browser
    ctk.CTkLabel(med_input_frame, text="Price (₱):", font=F(11)).grid(row=2, column=0,
                                                                               sticky="w", padx=5)
    price_entry = ctk.CTkEntry(med_input_frame, placeholder_text="0.00", width=120 + module_scale*6, font=F(11))
    price_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ctk.CTkLabel(med_input_frame, text="Qty:", font=F(11)).grid(row=2, column=2,
                                                                        sticky="w", padx=5)
    qty_entry = ctk.CTkEntry(med_input_frame, placeholder_text="1", width=60 + module_scale*4, font=F(11))
    qty_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)
    qty_entry.insert(0, "1")

    med_list_frame = ctk.CTkScrollableFrame(form_container, height=140 + module_scale*6, fg_color="#fdf2e9")
    med_list_frame.pack(fill="x", pady=10)
    
    medications_data = []
    
    ## Load and display medications for a given diagnosis id
    def load_medications(diagnosis_id):
        for w in med_list_frame.winfo_children():
            w.destroy()
        medications_data.clear()
        
        if not diagnosis_id:
            ctk.CTkLabel(med_list_frame, text="No medications yet",
                        text_color="gray", font=F(12)).pack(pady=10)
            update_total()
            return
        
        meds = db.query("SELECT * FROM medications WHERE diagnosis_id = ? ORDER BY id",
                       (diagnosis_id,))
        
        if not meds:
            ctk.CTkLabel(med_list_frame, text="No medications prescribed",
                        text_color="gray", font=F(12)).pack(pady=10)
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
                        font=F(11), anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(med_row, text=f"₱{subtotal:,.2f}",
                        font=F(11, "bold"), anchor="e").pack(side="right", padx=10, pady=5)
            
            ## Remove a medication from the diagnosis (UI callback)
            def delete_med(mid=med['id']):
                        if messagebox.askyesno("Confirm", "Delete this medication?"):
                            dv = DiagnosisView()
                            res = dv.delete_med_logic(mid)
                            if not res.get('ok'):
                                messagebox.showerror('Error', res.get('error', 'Failed to delete medication'))
                            if selected_diagnosis[0]:
                                load_medications(selected_diagnosis[0]['id'])
            
            ctk.CTkButton(med_row, text="X", width=30 + module_scale, height=30 + module_scale, fg_color="#e74c3c",
                         command=delete_med).pack(side="right", padx=5, pady=5)
        
        update_total()
    
    total_label = ctk.CTkLabel(form_container, text="Medication Total: ₱0.00",
                               font=F(14, "bold"), text_color="#e67e22")
    total_label.pack(anchor="e", pady=5)
    
    ## Recalculate medication total and update UI label
    def update_total():
        total = sum(float(m.get('price', 0)) * int(m.get('quantity', 1)) for m in medications_data)
        total_label.configure(text=f"Medication Total: ₱{total:,.2f}")
    
    ## UI handler: add medication to selected diagnosis (validates input)
    def add_medication():
        if not selected_diagnosis[0]:
            messagebox.showerror("Error", "Please save a diagnosis first before adding medications.")
            return
        # read selected medicine (from the browser selection)
        sel = (selected_med_display[0] or "").strip()
        # map back to real medicine name if display used
        med_name = display_map.get(sel, sel)
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

        dv = DiagnosisView()
        res = dv.add_medication_logic(selected_diagnosis[0]['id'], med_name, price, qty)
        if not res.get('ok'):
            messagebox.showerror('Error', res.get('error', 'Failed to add medication'))
            return

        # clear browser selection
        selected_med_display[0] = None
        for child in med_browser_frame.winfo_children():
            try:
                child.configure(fg_color="#ffffff")
            except Exception:
                pass
        price_entry.delete(0, "end")
        qty_entry.delete(0, "end")
        qty_entry.insert(0, "1")

        load_medications(selected_diagnosis[0]['id'])
        messagebox.showinfo("Success", f"Medication '{med_name}' added successfully!")
    
    ctk.CTkButton(med_input_frame, text="Add Medication", command=add_medication,
                 fg_color="#e67e22", width=140 + module_scale*4, height=36 + module_scale, font=F(12)).grid(row=3, column=0, columnspan=4, pady=10)

    # Label showing 'Use' of selected medicine
    med_use_label = ctk.CTkLabel(med_input_frame, text="Use:", font=F(11), text_color="#7f8c8d")
    med_use_label.grid(row=0, column=4, sticky="w", padx=8)

    display_map = {}

    ## Populate medicine browser list and map display names
    def refresh_medicine_list():
        # populate combo and browser; tolerate missing 'use' column
        try:
            meds = db.query("SELECT name, price, use FROM medicines ORDER BY name")
        except Exception:
            # fallback if 'use' column not present
            meds = db.query("SELECT name, price FROM medicines ORDER BY name")
        values = []
        display_map.clear()
        for m in meds:
            try:
                use_text = m.get('use', '') if isinstance(m, dict) else (m['use'] if 'use' in m else '')
            except Exception:
                use_text = ''
            disp = f"{m['name']} — {use_text}" if use_text else m['name']
            values.append(disp)
            display_map[disp] = m['name']
        # populate combo removed; browser will show values
        # populate browser
        for w in med_browser_frame.winfo_children():
            w.destroy()
        for disp in values:
            item = ctk.CTkFrame(med_browser_frame, fg_color="#ffffff", corner_radius=6)
            item.pack(fill="x", padx=4, pady=2)
            lbl = ctk.CTkLabel(item, text=disp, font=F(11), anchor="w")
            lbl.pack(side="left", padx=8, pady=6, fill="x", expand=True)
            ## Select medicine from browser and highlight in UI
            def on_item_click(e=None, d=disp, item_ref=item):
                # visually mark selection
                for child in med_browser_frame.winfo_children():
                    try:
                        child.configure(fg_color="#ffffff")
                    except Exception:
                        pass
                try:
                    item_ref.configure(fg_color="#e8f8f5")
                except Exception:
                    pass
                selected_med_display[0] = d
                select_med(d)
            item.bind("<Button-1>", on_item_click)
            lbl.bind("<Button-1>", on_item_click)

        ## Given a display value, load medicine details into inputs
        def select_med(display_value):
            med_name = display_map.get(display_value, display_value)
            if not med_name:
                return
            med = db.query("SELECT * FROM medicines WHERE name = ?", (med_name,))
            if not med:
                return
            med = med[0]
            try:
                price_entry.delete(0, 'end')
                price_entry.insert(0, f"{float(med['price']):.2f}")
            except Exception:
                pass
            try:
                use_text = med.get('use', '') if isinstance(med, dict) else (med['use'] if 'use' in med else '')
            except Exception:
                use_text = ''
            med_use_label.configure(text=f"Use: {use_text or ''}", font=F(10))

    # initial population
    refresh_medicine_list()
    
    ## Save diagnosis text for selected appointment (UI action)
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
        
        dv = DiagnosisView()
        res = dv.save_diagnosis_logic(apt, diag_text, selected_diagnosis[0])
        if res.get('updated'):
            messagebox.showinfo("Success", "Diagnosis updated successfully!")
        elif res.get('created'):
            selected_diagnosis[0] = {
                'id': res['id'],
                'appointment_id': res['appointment_id'],
                'patient_id': res['patient_id'],
                'doctor_id': res['doctor_id'],
                'diagnosis_text': res['diagnosis_text'],
                'diagnosis_date': res['diagnosis_date']
            }
            messagebox.showinfo("Success", "Diagnosis saved successfully! You can now add medications.")
        
        load_appointments(search_entry.get())
        load_diagnosis_for_appointment(apt['id'])
    
    ## Generate and save a plain-text medical certificate for selected diag
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
                 fg_color="#2ecc71", height=44 + module_scale, font=F(13, "bold")).pack(side="left", padx=5, expand=True, fill="x")
    
    ctk.CTkButton(btn_frame, text="Print Certificate", command=print_medical_certificate,
                 fg_color="#3498db", height=44 + module_scale, font=F(13)).pack(side="left", padx=5, expand=True, fill="x")
    
    ## Clear the diagnosis form and reset medicine selections
    def clear_form():
        diagnosis_text.delete("1.0", "end")
        # clear selected medicine in browser
        try:
            selected_med_display[0] = None
            for child in med_browser_frame.winfo_children():
                try:
                    child.configure(fg_color="#ffffff")
                except Exception:
                    pass
        except Exception:
            pass
        price_entry.delete(0, "end")
        qty_entry.delete(0, "end")
        qty_entry.insert(0, "1")
        selected_diagnosis[0] = None
        apt_info_label.configure(text="Select an appointment from the left panel", font=F(11))
        for w in med_list_frame.winfo_children():
            w.destroy()
        medications_data.clear()
        update_total()
    
    ctk.CTkButton(btn_frame, text="Clear", command=clear_form,
                 fg_color="#95a5a6", height=44 + module_scale, font=F(12)).pack(side="left", padx=5, expand=True, fill="x")
    
    load_appointments()

## Backwards-compatible alias for showing diagnosis view
def diagnosis(parent):
    """Compatibility alias: older code may call diagnosis(parent)."""
    return show_diagnosis_view(parent)