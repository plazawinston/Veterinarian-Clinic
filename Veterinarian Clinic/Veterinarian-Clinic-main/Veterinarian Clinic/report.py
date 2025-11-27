import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

app = None
db = None
refs = {}

def show_report_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Client History Reports",
                font=("Arial", 32, "bold")).pack(pady=20)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(search_frame, text="Search Client:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Owner name or contact...", width=250)
    search_entry.pack(side="left", padx=5)
    
    report_display = ctk.CTkTextbox(left, font=("Arial", 11))
    report_display.pack(fill="both", expand=True, padx=10, pady=10)
    
    def generate_report(search_query=""):
        
        report_display.delete("1.0", "end")
        if not search_query:
            report_display.insert("end", "Please enter a client name or contact number to search.\n\n")
            report_display.insert("end", "The report will show only COMPLETED appointments for the client.\n")
            report_display.insert("end", "Usage:\n")
            report_display.insert("end", "  - Search by owner name or contact (partial match allowed)\n")
            report_display.insert("end", "  - Click 'Generate Report' to list completed visits per pet\n\n")
            return
        
        clients = db.query("""
            SELECT DISTINCT owner_name, owner_contact
            FROM patients
            WHERE owner_name LIKE ? OR owner_contact LIKE ?
            ORDER BY owner_name
        """, (f"%{search_query}%", f"%{search_query}%"))
        
        if not clients:
            report_display.insert("end", "No clients found matching your search.\n")
            return
        
        for client in clients:
            report_display.insert("end", "="*90 + "\n")
            report_display.insert("end", f"COMPLETED APPOINTMENTS - CLIENT\n")
            report_display.insert("end", "="*90 + "\n")
            report_display.insert("end", f"Owner Name: {client['owner_name']}\n")
            report_display.insert("end", f"Contact: {client['owner_contact']}\n")
            report_display.insert("end", f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_display.insert("end", "-"*90 + "\n\n")
            
            pets = db.query("""
                SELECT * FROM patients
                WHERE owner_name = ? AND owner_contact = ?
                ORDER BY name
            """, (client['owner_name'], client['owner_contact']))
            
            if not pets:
                report_display.insert("end", "No pets found for this client.\n\n")
                continue
            
            for idx, pet in enumerate(pets, 1):
                report_display.insert("end", f"[PET #{idx}] {pet['name']} ({pet['species']})\n")
                completed_apts = db.query("""
                    SELECT a.*, d.name as doctor_name, d.specialization, d.fee
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = ? AND a.status = 'completed'
                    ORDER BY a.date DESC, a.time DESC
                """, (pet['id'],))
                
                if completed_apts:
                    report_display.insert("end", f"  Completed Visits ({len(completed_apts)}):\n")
                    for apt in completed_apts:
                        fee_value = float(apt['fee']) if apt['fee'] else 0.0
                        fee_str = f"P{fee_value:,.2f}"
                        report_display.insert("end", f"    - {apt['date']} at {apt['time']} | Dr. {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
                        if apt['notes']:
                            report_display.insert("end", f"       Notes: {apt['notes']}\n")
                else:
                    report_display.insert("end", "  No completed visits for this pet.\n")
                
                report_display.insert("end", "\n")
            
            report_display.insert("end", "="*90 + "\n\n")
    
    def export_report():
        
        try:
            content = report_display.get("1.0", "end").strip()
            if not content:
                messagebox.showerror("Error", "No report to export. Generate a report first.")
                return
            filename = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Report exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")
    
    ctk.CTkButton(search_frame, text="Generate Report", 
                 command=lambda: generate_report(search_entry.get()),
                 fg_color="#2ecc71", width=120).pack(side="left", padx=5)
    
    ctk.CTkButton(search_frame, text="Clear",
                 command=lambda: [search_entry.delete(0, "end"), generate_report()],
                 fg_color="#3498db", width=80).pack(side="left", padx=5)

    # Button to show all clients/patients who have completed appointments
    def show_completed_clients():
        
        report_display.delete("1.0", "end")
        clients = db.query("""
            SELECT DISTINCT p.owner_name, p.owner_contact
            FROM patients p
            JOIN appointments a ON a.patient_id = p.id
            WHERE a.status = 'completed'
            ORDER BY p.owner_name
        """)
        if not clients:
            report_display.insert("end", "No clients found with completed appointments.\n")
            return

        for client in clients:
            report_display.insert("end", "="*90 + "\n")
            report_display.insert("end", f"COMPLETED APPOINTMENTS - CLIENT\n")
            report_display.insert("end", "="*90 + "\n")
            report_display.insert("end", f"Owner Name: {client['owner_name']}\n")
            report_display.insert("end", f"Contact: {client['owner_contact']}\n")
            report_display.insert("end", f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_display.insert("end", "-"*90 + "\n\n")

            pets = db.query("""
                SELECT * FROM patients
                WHERE owner_name = ? AND owner_contact = ?
                ORDER BY name
            """, (client['owner_name'], client['owner_contact']))

            if not pets:
                report_display.insert("end", "No pets found for this client.\n\n")
                continue

            for idx, pet in enumerate(pets, 1):
                report_display.insert("end", f"[PET #{idx}] {pet['name']} ({pet['species']})\n")
                completed_apts = db.query("""
                    SELECT a.*, d.name as doctor_name, d.specialization, d.fee
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = ? AND a.status = 'completed'
                    ORDER BY a.date DESC, a.time DESC
                """, (pet['id'],))

                if completed_apts:
                    report_display.insert("end", f"  Completed Visits ({len(completed_apts)}):\n")
                    for apt in completed_apts:
                        fee_value = float(apt['fee']) if apt['fee'] else 0.0
                        fee_str = f"P{fee_value:,.2f}"
                        report_display.insert("end", f"    - {apt['date']} at {apt['time']} | Dr. {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
                        if apt['notes']:
                            report_display.insert("end", f"       Notes: {apt['notes']}\n")
                else:
                    report_display.insert("end", "  No completed visits for this pet.\n")

                report_display.insert("end", "\n")

            report_display.insert("end", "="*90 + "\n\n")

    # Completed button to list clients/pets with completed appointments
    ctk.CTkButton(search_frame, text="Completed", 
                 command=show_completed_clients, fg_color="#9b59b6", width=120).pack(side="left", padx=5)
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=350)
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)
    
    ctk.CTkLabel(right, text="Quick Stats", font=("Arial", 20, "bold")).pack(pady=15)
    
    stats_text = ctk.CTkTextbox(right, font=("Arial", 12), height=400)
    stats_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    total_clients = len(db.query("SELECT DISTINCT owner_name, owner_contact FROM patients"))
    total_pets = len(db.query("SELECT * FROM patients"))
    total_apts = len(db.query("SELECT * FROM appointments"))
    completed_apts = len(db.query("SELECT * FROM appointments WHERE status='completed'"))
    
    stats_text.insert("end", "CLINIC STATISTICS\n")
    stats_text.insert("end", "="*40 + "\n\n")
    stats_text.insert("end", f"Total Clients: {total_clients}\n")
    stats_text.insert("end", f"Total Pets: {total_pets}\n")
    stats_text.insert("end", f"Total Appointments: {total_apts}\n")
    stats_text.insert("end", f"Completed: {completed_apts}\n\n")
    
    stats_text.insert("end", "="*40 + "\n")
    stats_text.insert("end", "TOP CLIENTS BY VISITS\n")
    stats_text.insert("end", "="*40 + "\n\n")
    # Top clients by completed visits (only completed appointments are counted)
    top_clients = db.query("""
        SELECT p.owner_name, p.owner_contact, COUNT(a.id) AS visits
        FROM patients p
        JOIN appointments a ON a.patient_id = p.id
        WHERE a.status = 'completed'
        GROUP BY p.owner_name, p.owner_contact
        ORDER BY visits DESC, p.owner_name
        LIMIT 10
    """)
    if top_clients:
        for idx, row in enumerate(top_clients, 1):
            stats_text.insert("end", f"{idx}. {row['owner_name']} ({row['owner_contact']}) - {row['visits']} completed visit(s)\n")
    else:
        stats_text.insert("end", "No completed visits recorded yet.\n")
    stats_text.insert("end", "\n")
    
    ctk.CTkButton(right, text="Export Report to File", command=export_report,
                 fg_color="#e67e22", height=40).pack(fill="x", padx=10, pady=(10,20))
    
    generate_report()
