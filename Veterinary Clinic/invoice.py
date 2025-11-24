import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

app = None
db = None
refs = {}

def show_invoice_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Invoice Generation",
                font=("Arial", 32, "bold")).pack(pady=20)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(search_frame, text="Client:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search client...", width=200)
    search_entry.pack(side="left", padx=5)
    
    selected_appointments = {}
    
    appointments_frame = ctk.CTkFrame(left, fg_color="transparent")
    appointments_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    ctk.CTkLabel(appointments_frame, text="Select Appointments for Invoice:",
                font=("Arial", 14, "bold")).pack(anchor="w", pady=(0,10))
    
    appointments_list = ctk.CTkScrollableFrame(appointments_frame, height=400)
    appointments_list.pack(fill="both", expand=True)
    
    def load_appointments(search_query=""):
        for widget in appointments_list.winfo_children():
            widget.destroy()
        selected_appointments.clear()
        
        if not search_query:
            ctk.CTkLabel(appointments_list, text="Enter client name to load appointments",
                        text_color="gray").pack(pady=20)
            return
        
        clients = db.query("""
            SELECT DISTINCT p.owner_name, p.owner_contact
            FROM patients p
            WHERE p.owner_name LIKE ? OR p.owner_contact LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%"))
        
        if not clients:
            ctk.CTkLabel(appointments_list, text=f"No client found: {search_query}",
                        text_color="red").pack(pady=20)
            return
        
        client = clients[0]
        
        appointments = db.query("""
            SELECT a.*, p.name as pet_name, p.species, d.name as doctor_name, 
                   d.specialization, d.fee
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE p.owner_name = ? AND p.owner_contact = ?
            ORDER BY a.date DESC, a.time DESC
        """, (client['owner_name'], client['owner_contact']))
        
        if not appointments:
            ctk.CTkLabel(appointments_list, text="No appointments found for this client",
                        text_color="gray").pack(pady=20)
            return
        
        for apt in appointments:
            frame = ctk.CTkFrame(appointments_list, fg_color="#f8f9fa", corner_radius=5)
            frame.pack(fill="x", pady=5, padx=5)
            
            var = ctk.BooleanVar(value=False)
            selected_appointments[apt['id']] = {'var': var, 'data': apt}
            
            checkbox = ctk.CTkCheckBox(frame, text="", variable=var, width=30)
            checkbox.pack(side="left", padx=10, pady=10)
            
            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=5)
            
            try:
                fee_str = f"₱{float(apt['fee']):,.2f}"
            except:
                fee_str = f"₱{apt['fee']}"
            
            ctk.CTkLabel(info_frame, 
                        text=f"{apt['date']} {apt['time']} - {apt['pet_name']} ({apt['species']})",
                        font=("Arial", 12, "bold"),
                        anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame,
                        text=f"Dr. {apt['doctor_name']} - {apt['specialization']} | {fee_str} | {apt['status'].upper()}",
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
                 command=lambda: load_appointments(search_entry.get()),
                 fg_color="#2ecc71", width=100).pack(side="left", padx=5)
    
    ctk.CTkButton(search_frame, text="Clear",
                 command=lambda: [search_entry.delete(0, "end"), load_appointments()],
                 fg_color="#95a5a6", width=80).pack(side="left", padx=5)
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=500)
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)
    
    ctk.CTkLabel(right, text="Invoice Preview", font=("Arial", 20, "bold")).pack(pady=15)
    
    invoice_display = ctk.CTkTextbox(right, font=("Courier", 10))
    invoice_display.pack(fill="both", expand=True, padx=10, pady=10)
    
    def generate_invoice():
        invoice_display.delete("1.0", "end")
        
        selected = [(aid, data) for aid, data in selected_appointments.items() 
                   if data['var'].get()]
        
        if not selected:
            invoice_display.insert("end", "No appointments selected.\n\n")
            invoice_display.insert("end", "Please:\n")
            invoice_display.insert("end", "1. Search for a client\n")
            invoice_display.insert("end", "2. Select appointments to invoice\n")
            invoice_display.insert("end", "3. Click 'Generate Invoice'\n")
            return
        
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        invoice_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        first_apt = selected[0][1]['data']
        
        client_info = db.query("""
            SELECT DISTINCT owner_name, owner_contact 
            FROM patients 
            WHERE id = ?
        """, (first_apt['patient_id'],))[0]
        
        invoice_display.insert("end", "=" * 70 + "\n")
        invoice_display.insert("end", "                    VET CLINIC MANAGEMENT SYSTEM\n")
        invoice_display.insert("end", "                      OFFICIAL INVOICE RECEIPT\n")
        invoice_display.insert("end", "=" * 70 + "\n\n")
        
        invoice_display.insert("end", f"Invoice Number: {invoice_number}\n")
        invoice_display.insert("end", f"Date: {invoice_date}\n\n")
        
        invoice_display.insert("end", "-" * 70 + "\n")
        invoice_display.insert("end", "BILL TO:\n")
        invoice_display.insert("end", f"  Name:    {client_info['owner_name']}\n")
        invoice_display.insert("end", f"  Contact: {client_info['owner_contact']}\n")
        invoice_display.insert("end", "-" * 70 + "\n\n")
        
        invoice_display.insert("end", "SERVICES RENDERED:\n")
        invoice_display.insert("end", "=" * 70 + "\n\n")
        
        subtotal = 0.0
        current_pet = None
        
        sorted_items = sorted(selected, key=lambda x: (x[1]['data']['pet_name'], x[1]['data']['date']))
        
        for idx, (aid, apt_dict) in enumerate(sorted_items, 1):
            apt = apt_dict['data']
            
            if current_pet != apt['pet_name']:
                if current_pet is not None:
                    invoice_display.insert("end", "\n")
                current_pet = apt['pet_name']
                invoice_display.insert("end", f"Pet: {apt['pet_name']} ({apt['species']})\n")
                invoice_display.insert("end", "-" * 70 + "\n")
            
            try:
                fee = float(apt['fee'])
                subtotal += fee
                fee_str = f"₱{fee:,.2f}"
            except:
                fee_str = f"₱{apt['fee']}"
            
            invoice_display.insert("end", f"{idx}. Date: {apt['date']} at {apt['time']}\n")
            invoice_display.insert("end", f"   Service: {apt['specialization']}\n")
            invoice_display.insert("end", f"   Provider: Dr. {apt['doctor_name']}\n")
            invoice_display.insert("end", f"   Fee: {fee_str:>50}\n")
            if apt['notes']:
                invoice_display.insert("end", f"   Notes: {apt['notes']}\n")
            invoice_display.insert("end", "\n")
        
        invoice_display.insert("end", "=" * 70 + "\n")
        invoice_display.insert("end", f"SUBTOTAL: {f'₱{subtotal:,.2f}':>59}\n")
        invoice_display.insert("end", "-" * 70 + "\n")
        invoice_display.insert("end", f"TOTAL AMOUNT DUE: {f'₱{subtotal:,.2f}':>51}\n")
        invoice_display.insert("end", "=" * 70 + "\n\n")
        
        invoice_display.insert("end", "Thank you for choosing our veterinary services!\n")
        invoice_display.insert("end", "For inquiries, please contact our clinic.\n\n")
        invoice_display.insert("end", "=" * 70 + "\n")
        invoice_display.insert("end", "           This is a computer-generated invoice.\n")
        invoice_display.insert("end", "=" * 70 + "\n")
    
    def print_invoice():
        try:
            content = invoice_display.get("1.0", "end")
            if not content.strip() or "No appointments selected" in content:
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