import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

app = None
db = None
refs = {}


class Invoice:
    def generate_text(self, invoice_display=None):
        # Build invoice_data compatible with build_invoice_text
        invoice_data = {
            'generated_at': self.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'service_total': sum([float(it.get('service_total', 0.0)) for it in self.items]) if self.items else 0.0,
            # the rest will be filled by build_invoice_text when used per-appointment
        }
        text = build_invoice_text(invoice_data)
        if invoice_display is not None:
            invoice_display.delete('1.0', 'end')
            invoice_display.insert('end', text)
            refs['last_invoice'] = text
        return text

    def save(self):
        # Optional: persist invoice to DB if an `invoices` table is present.
        try:
            db.execute("INSERT INTO invoices (invoice_number, generated_at) VALUES (?, ?)",
                       (self.invoice_number or '', self.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except Exception:
            # If invoices table doesn't exist, skip saving silently.
            pass


class InvoiceView:
    def __init__(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        ctk.CTkLabel(parent, text="Invoice Generation",
                    font=("Arial", 32, "bold")).pack(pady=20)

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20)

        # left (search / appointments) - make slightly wider so search controls/buttons are visible
        left = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=520)
        left.pack(side="left", fill="y", expand=False, padx=(0,10))
        # allow children to size the left frame vertically
        left.pack_propagate(True)

        search_frame = ctk.CTkFrame(left, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Client:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        # increased entry width so buttons will sit on the same row
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search client...", width=260)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.selected_appointments = {}

        appointments_frame = ctk.CTkFrame(left, fg_color="transparent")
        appointments_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(appointments_frame, text="Select Appointments for Invoice:",
                    font=("Arial", 14, "bold")).pack(anchor="w", pady=(0,10))

        self.appointments_list = ctk.CTkScrollableFrame(appointments_frame, height=520)
        self.appointments_list.pack(fill="both", expand=True)

        def load_appointments(search_query=""):
            for widget in self.appointments_list.winfo_children():
                widget.destroy()
            self.selected_appointments.clear()

            if not search_query:
                ctk.CTkLabel(self.appointments_list, text="Enter client name to load appointments",
                            text_color="gray").pack(pady=20)
                return

            clients = db.query("""
                SELECT DISTINCT p.owner_name, p.owner_contact
                FROM patients p
                WHERE p.owner_name LIKE ? OR p.owner_contact LIKE ?
            """, (f"%{search_query}%", f"%{search_query}%"))

            if not clients:
                ctk.CTkLabel(self.appointments_list, text=f"No client found: {search_query}",
                            text_color="red").pack(pady=20)
                return

            client = clients[0]

            appointments = db.query("""
                SELECT a.*, p.name as pet_name, p.species, d.name as doctor_name, 
                       d.specialization, d.fee
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE p.owner_name = ? AND p.owner_contact = ? AND a.status = 'completed'
                ORDER BY a.date DESC, a.time DESC
            """, (client['owner_name'], client['owner_contact']))

            if not appointments:
                ctk.CTkLabel(self.appointments_list, text="No completed appointments found for this client",
                            text_color="gray").pack(pady=20)
                return

            for apt in appointments:
                frame = ctk.CTkFrame(self.appointments_list, fg_color="#f8f9fa", corner_radius=5)
                frame.pack(fill="x", pady=5, padx=5)

                var = ctk.BooleanVar(value=False)

                diagnoses = db.query("SELECT id FROM diagnoses WHERE appointment_id = ?", (apt['id'],))
                has_diagnosis = len(diagnoses) > 0

                med_total = 0.0
                diagnosis_ids = []
                if has_diagnosis:
                    for diag in diagnoses:
                        diagnosis_ids.append(diag['id'])
                        meds = db.query("""
                            SELECT SUM(price * quantity) as total 
                            FROM medications 
                            WHERE diagnosis_id = ?
                        """, (diag['id'],))
                        if meds and meds[0]['total']:
                            med_total += float(meds[0]['total'])

                apt_dict = dict(apt)
                apt_dict['has_diagnosis'] = has_diagnosis
                apt_dict['diagnosis_ids'] = diagnosis_ids
                apt_dict['medication_total'] = med_total

                self.selected_appointments[apt['id']] = {'var': var, 'data': apt_dict}

                checkbox = ctk.CTkCheckBox(frame, text="", variable=var, width=30)
                checkbox.pack(side="left", padx=10, pady=10)

                info_frame = ctk.CTkFrame(frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, pady=5)

                fee_value = float(apt['fee']) if apt['fee'] else 0.0
                fee_str = f"P{fee_value:,.2f}"

                ctk.CTkLabel(info_frame, 
                            text=f"{apt['date']} {apt['time']} - {apt['pet_name']} ({apt['species']})",
                            font=("Arial", 12, "bold"),
                            anchor="w").pack(anchor="w")

                doctor_text = f"Dr. {apt['doctor_name']} - {apt['specialization']} | Fee: {fee_str}"
                if med_total > 0:
                    doctor_text += f" | Meds: P{med_total:,.2f}"

                ctk.CTkLabel(info_frame,
                            text=doctor_text,
                            font=("Arial", 10),
                            text_color="#666",
                            anchor="w").pack(anchor="w")

                if apt['notes']:
                    ctk.CTkLabel(info_frame,
                                text=f"Notes: {apt['notes']}",
                                font=("Arial", 9),
                                text_color="#888",
                                anchor="w").pack(anchor="w")

        ctk.CTkButton(search_frame, text="Search",
                     command=lambda: load_appointments(self.search_entry.get()),
                     fg_color="#2ecc71", width=100).pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="Clear",
                     command=lambda: [self.search_entry.delete(0, "end"), load_appointments()],
                     fg_color="#95a5a6", width=80).pack(side="left", padx=5)

        # right (invoice preview) - allocate more width so preview is clearly larger
        right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=820)
        right.pack(side="right", fill="both", padx=(10,0), expand=True)
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="Invoice Preview", font=("Arial", 22, "bold")).pack(pady=18)

        # larger, more readable preview textbox
        self.invoice_display = ctk.CTkTextbox(right, font=("Courier", 12))
        self.invoice_display.pack(fill="both", expand=True, padx=12, pady=12)

        refs['last_invoice'] = ""

        def generate_invoice():
            self.invoice_display.delete("1.0", "end")
            refs['last_invoice'] = ""

            selected = [(aid, data) for aid, data in self.selected_appointments.items() 
                       if data['var'].get()]

            if not selected:
                self.invoice_display.insert("end", "No appointments selected.\n\n")
                self.invoice_display.insert("end", "Please:\n")
                self.invoice_display.insert("end", "1. Search for a client\n")
                self.invoice_display.insert("end", "2. Select appointments to invoice\n")
                self.invoice_display.insert("end", "3. Click 'Generate Invoice'\n")
                return

            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            invoice_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            first_apt = selected[0][1]['data']

            client_info = db.query("""
                SELECT DISTINCT owner_name, owner_contact 
                FROM patients 
                WHERE id = ?
            """, (first_apt['patient_id'],))[0]

            lines = []
            lines.append("=" * 70)
            lines.append("                    VET CLINIC MANAGEMENT SYSTEM")
            lines.append("                      OFFICIAL INVOICE RECEIPT")
            lines.append("=" * 70)
            lines.append(f"Invoice Number: {invoice_number}")
            lines.append(f"Date Generated: {invoice_date}")
            lines.append("-" * 70)
            lines.append("BILL TO:")
            lines.append(f"  Owner Name:    {client_info['owner_name']}")
            lines.append(f"  Owner Contact: {client_info['owner_contact']}")
            lines.append("-" * 70)
            lines.append("SERVICES & MEDICATIONS:")
            lines.append("=" * 70)

            doctor_fees_total = 0.0
            medications_total = 0.0
            current_pet = None

            sorted_items = sorted(selected, key=lambda x: (x[1]['data']['pet_name'], x[1]['data']['date'], x[1]['data']['time']))

            for idx, (aid, apt_dict) in enumerate(sorted_items, 1):
                apt = apt_dict['data']

                if current_pet != apt['pet_name']:
                    if current_pet is not None:
                        lines.append("")
                    current_pet = apt['pet_name']
                    lines.append(f"Pet: {apt['pet_name']} ({apt['species']})  [Patient ID: {apt['patient_id']}]")
                    lines.append("-" * 70)

                fee_value = float(apt['fee']) if apt['fee'] is not None else 0.0
                doctor_fees_total += fee_value
                fee_str = f"P{fee_value:,.2f}"

                lines.append(f"{idx}. Appointment: {apt['date']} at {apt['time']}")
                lines.append(f"   Provider: Dr. {apt['doctor_name']} ({apt['specialization']})")
                lines.append(f"   Doctor's Fee: {fee_str}")

                if apt.get('has_diagnosis') and apt.get('diagnosis_ids'):
                    for diag_id in apt['diagnosis_ids']:
                        diagnosis = db.query("SELECT * FROM diagnoses WHERE id = ?", (diag_id,))
                        if diagnosis:
                            diag = diagnosis[0]
                            diag_text = diag['diagnosis_text']
                            if len(diag_text) > 80:
                                diag_text = diag_text[:80] + "..."
                            lines.append(f"   Diagnosis: {diag_text}")

                        meds = db.query("SELECT * FROM medications WHERE diagnosis_id = ?", (diag_id,))
                        if meds:
                            lines.append("   Medications:")
                            for med in meds:
                                med_price = float(med['price']) if med['price'] else 0.0
                                med_qty = int(med['quantity']) if med['quantity'] else 1
                                med_subtotal = med_price * med_qty
                                medications_total += med_subtotal
                                lines.append(f"     - {med['medicine_name']} x{med_qty} @ P{med_price:,.2f} = P{med_subtotal:,.2f}")

                if apt['notes']:
                    lines.append(f"   Notes: {apt['notes']}")
                lines.append("")

            grand_total = doctor_fees_total + medications_total

            lines.append("=" * 70)
            lines.append("                         INVOICE SUMMARY")
            lines.append("=" * 70)
            lines.append(f"  Doctor's Fees Subtotal:      P{doctor_fees_total:,.2f}")
            lines.append(f"  Medications Subtotal:        P{medications_total:,.2f}")
            lines.append("-" * 70)
            lines.append(f"  GRAND TOTAL:                 P{grand_total:,.2f}")
            lines.append("=" * 70)
            lines.append("")
            lines.append("Thank you for choosing our veterinary services!")
            lines.append("This is a computer-generated invoice.")
            lines.append("=" * 70)

            invoice_text = "\n".join(lines)
            self.invoice_display.insert("end", invoice_text)
            refs['last_invoice'] = invoice_text

        def print_invoice():
            try:
                content = refs.get('last_invoice', "").strip()
                if not content:
                    content = self.invoice_display.get("1.0", "end").strip()
                if not content:
                    messagebox.showerror("Error", "No invoice to print. Generate an invoice first.")
                    return

                invoice_number = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"invoice_{invoice_number}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Invoice saved to {filename}\n\nYou can print this file.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save invoice: {str(e)}")

        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        ctk.CTkButton(btn_frame, text="Generate Invoice", command=generate_invoice,
                     fg_color="#2ecc71", height=40).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(btn_frame, text="Save & Print", command=print_invoice,
                     fg_color="#e67e22", height=40).pack(side="left", padx=5, expand=True, fill="x")

        load_appointments()
        generate_invoice()


def show_invoice_view(parent):
    InvoiceView(parent)

def _get_medications_for_appointment(appointment_id):
    """
    Return list of medication dicts and medication total for an appointment's diagnosis.
    Each dict: {'medicine_name','quantity','price','subtotal'}
    """
    sql = """
        SELECT m.medicine_name, m.quantity, m.price
        FROM medications m
        JOIN diagnoses d ON m.diagnosis_id = d.id
        WHERE d.appointment_id = ?
        ORDER BY m.id ASC
    """
    rows = db.query(sql, (appointment_id,)) or []
    meds = []
    med_total = 0.0
    for r in rows:
        # support sqlite3.Row, dict-like, or tuple
        try:
            name = r['medicine_name']
            qty = int(r['quantity'])
            price = float(r['price'])
        except Exception:
            # tuple-like fallback
            name = r[0]
            qty = int(r[1])
            price = float(r[2])
        subtotal = qty * price
        meds.append({'medicine_name': name, 'quantity': qty, 'price': price, 'subtotal': subtotal})
        med_total += subtotal
    return meds, med_total


def build_invoice_text(invoice_data):
    """
    Build invoice text including diagnosis and prescribed medications.
    invoice_data should include keys like: appointment_id, patient_name, owner_name,
    diagnosis_text, service_total, date, time, doctor_name, etc.
    """
    med_total = 0.0
    lines = []
    lines.append("======================================================================")
    lines.append("                    VET CLINIC MANAGEMENT SYSTEM")
    lines.append("                              INVOICE")
    lines.append("======================================================================")
    lines.append(f"Invoice Date: {invoice_data.get('generated_at', '')}")
    lines.append("----------------------------------------------------------------------")
    lines.append("PATIENT / OWNER:")
    lines.append(f"  Pet Name: {invoice_data.get('patient_name','')}")
    lines.append(f"  Owner:    {invoice_data.get('owner_name','')}")
    lines.append("")
    lines.append("ATTENDING VETERINARIAN:")
    lines.append(f"  {invoice_data.get('doctor_name','')}")
    lines.append("----------------------------------------------------------------------")
    lines.append("APPOINTMENT:")
    lines.append(f"  Date: {invoice_data.get('date','')}    Time: {invoice_data.get('time','')}")
    lines.append("----------------------------------------------------------------------")
    if invoice_data.get('diagnosis_text'):
        lines.append("DIAGNOSIS:")
        lines.append(f"  {invoice_data.get('diagnosis_text')}")
        lines.append("----------------------------------------------------------------------")

    appointment_id = invoice_data.get('appointment_id')
    if appointment_id:
        meds, med_total = _get_medications_for_appointment(appointment_id)
        if meds:
            lines.append("PRESCRIBED MEDICATIONS:")
            for i, m in enumerate(meds, 1):
                lines.append(f"  {i}. {m['medicine_name']}")
                lines.append(f"     Quantity: {m['quantity']} | Unit Price: P{m['price']:.2f} | Subtotal: P{m['subtotal']:.2f}")
            lines.append("")
            lines.append(f"  MEDICATION TOTAL: P{med_total:.2f}")
            lines.append("----------------------------------------------------------------------")

    service_total = float(invoice_data.get('service_total', 0.0))
    grand_total = service_total + med_total
    lines.append(f"SERVICE TOTAL: P{service_total:.2f}")
    lines.append(f"MEDICATIONS TOTAL: P{med_total:.2f}")
    lines.append(f"GRAND TOTAL: P{grand_total:.2f}")
    lines.append("======================================================================")
    return "\n".join(lines)


def show_invoice_preview_for_appointment(appointment_id):
    """
    Example helper: gather data, build text, and open a simple preview window.
    Call this from your existing preview command instead of the old preview.
    """
    # fetch appointment, patient, diagnosis and doctor info (adjust columns to your schema)
    apt = db.query("SELECT a.id, a.date, a.time, p.name as patient_name, o.name as owner_name, d.diagnosis_text, doc.name as doctor_name FROM appointments a "
                   "LEFT JOIN patients p ON a.patient_id = p.id "
                   "LEFT JOIN owners o ON p.owner_id = o.id "
                   "LEFT JOIN diagnoses d ON d.appointment_id = a.id "
                   "LEFT JOIN doctors doc ON a.doctor_id = doc.id "
                   "WHERE a.id = ?", (appointment_id,))
    if not apt:
        messagebox.showerror("Invoice", "Appointment not found.")
        return
    row = apt[0]
    invoice_data = {
        'appointment_id': appointment_id,
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'patient_name': row.get('patient_name') if isinstance(row, dict) or 'patient_name' in row else row[3],
        'owner_name': row.get('owner_name') if isinstance(row, dict) or 'owner_name' in row else row[4],
        'diagnosis_text': row.get('diagnosis_text') if isinstance(row, dict) or 'diagnosis_text' in row else row[5],
        'doctor_name': row.get('doctor_name') if isinstance(row, dict) or 'doctor_name' in row else row[6],
        'date': row.get('date') if isinstance(row, dict) or 'date' in row else row[1],
        'time': row.get('time') if isinstance(row, dict) or 'time' in row else row[2],
        'service_total': row.get('service_total', 0.0) if isinstance(row, dict) else 0.0
    }

    text = build_invoice_text(invoice_data)

    # show in a simple CTk window - replace/fit into your existing preview UI
    preview = ctk.CTkToplevel()
    preview.title("Invoice Preview")
    txt = ctk.CTkTextbox(preview, width=800, height=600)
    txt.pack(fill="both", expand=True, padx=10, pady=10)
    txt.insert("0.0", text)
    txt.configure(state="disabled")
