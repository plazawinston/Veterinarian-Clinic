import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

app = None
db = None
refs = {}
class Report:
    """Data/access layer for reports."""
    def find_clients(self, search_query=""):
        if not search_query:
            return []
        return db.query("""
            SELECT DISTINCT owner_name, owner_contact
            FROM patients
            WHERE owner_name LIKE ? OR owner_contact LIKE ?
            ORDER BY owner_name
        """, (f"%{search_query}%", f"%{search_query}%"))

    def get_pets_for_client(self, owner_name, owner_contact):
        return db.query("""
            SELECT * FROM patients
            WHERE owner_name = ? AND owner_contact = ?
            ORDER BY name
        """, (owner_name, owner_contact))

    def get_completed_appointments_for_patient(self, patient_id):
        return db.query("""
            SELECT a.*, d.name as doctor_name, d.specialization, d.fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = ? AND a.status = 'completed'
            ORDER BY a.date DESC, a.time DESC
        """, (patient_id,))

    def find_clients_with_completed(self):
        return db.query("""
            SELECT DISTINCT p.owner_name, p.owner_contact
            FROM patients p
            JOIN appointments a ON a.patient_id = p.id
            WHERE a.status = 'completed'
            ORDER BY p.owner_name
        """)

    def stats(self):
        return {
            'total_clients': len(db.query("SELECT DISTINCT owner_name, owner_contact FROM patients")),
            'total_pets': len(db.query("SELECT * FROM patients")),
            'total_apts': len(db.query("SELECT * FROM appointments")),
            'completed_apts': len(db.query("SELECT * FROM appointments WHERE status='completed'"))
        }

    def top_clients_by_visits(self):
        return db.query("""
            SELECT p.owner_name, p.owner_contact, COUNT(a.id) AS visits
            FROM patients p
            JOIN appointments a ON a.patient_id = p.id
            WHERE a.status = 'completed'
            GROUP BY p.owner_name, p.owner_contact
            ORDER BY visits DESC, p.owner_name
            LIMIT 10
        """)


class ReportView:
    def __init__(self, parent, report=None):
        self.parent = parent
        self.report = report or Report()
        self.build()

    def build(self):
        for w in self.parent.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.parent, text="Client History Reports",
                    font=("Arial", 32, "bold")).pack(pady=20)

        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20)

        left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        search_frame = ctk.CTkFrame(left, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Search Client:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Owner name or contact...", width=250)
        self.search_entry.pack(side="left", padx=5)

        self.report_display = ctk.CTkTextbox(left, font=("Arial", 11))
        self.report_display.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(search_frame, text="Generate Report", 
                     command=lambda: self.generate_report(self.search_entry.get()),
                     fg_color="#2ecc71", width=120).pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="Clear",
                     command=lambda: [self.search_entry.delete(0, "end"), self.generate_report()],
                     fg_color="#3498db", width=80).pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="Completed", 
                     command=self.show_completed_clients, fg_color="#9b59b6", width=120).pack(side="left", padx=5)

        right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=350)
        right.pack(side="right", fill="both", padx=(10,0))
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="Quick Stats", font=("Arial", 20, "bold")).pack(pady=15)

        self.stats_text = ctk.CTkTextbox(right, font=("Arial", 12), height=400)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(right, text="Export Report to File", command=self.export_report,
                     fg_color="#e67e22", height=40).pack(fill="x", padx=10, pady=(10,20))

        # Initialize stats and report
        self.update_stats()
        self.generate_report()

    def update_stats(self):
        s = self.report.stats()
        self.stats_text.delete('1.0', 'end')
        self.stats_text.insert("end", "CLINIC STATISTICS\n")
        self.stats_text.insert("end", "="*40 + "\n\n")
        self.stats_text.insert("end", f"Total Clients: {s['total_clients']}\n")
        self.stats_text.insert("end", f"Total Pets: {s['total_pets']}\n")
        self.stats_text.insert("end", f"Total Appointments: {s['total_apts']}\n")
        self.stats_text.insert("end", f"Completed: {s['completed_apts']}\n\n")
        self.stats_text.insert("end", "="*40 + "\n")
        self.stats_text.insert("end", "TOP CLIENTS BY VISITS\n")
        self.stats_text.insert("end", "="*40 + "\n\n")
        top_clients = self.report.top_clients_by_visits()
        if top_clients:
            for idx, row in enumerate(top_clients, 1):
                self.stats_text.insert("end", f"{idx}. {row['owner_name']} ({row['owner_contact']}) - {row['visits']} completed visit(s)\n")
        else:
            self.stats_text.insert("end", "No completed visits recorded yet.\n")
        self.stats_text.insert("end", "\n")

    def generate_report(self, search_query=""):
        self.report_display.delete("1.0", "end")
        if not search_query:
            self.report_display.insert("end", "Please enter a client name or contact number to search.\n\n")
            self.report_display.insert("end", "The report will show only COMPLETED appointments for the client.\n")
            self.report_display.insert("end", "Usage:\n")
            self.report_display.insert("end", "  - Search by owner name or contact (partial match allowed)\n")
            self.report_display.insert("end", "  - Click 'Generate Report' to list completed visits per pet\n\n")
            return

        clients = self.report.find_clients(search_query)
        if not clients:
            self.report_display.insert("end", "No clients found matching your search.\n")
            return

        for client in clients:
            self.report_display.insert("end", "="*90 + "\n")
            self.report_display.insert("end", f"COMPLETED APPOINTMENTS - CLIENT\n")
            self.report_display.insert("end", "="*90 + "\n")
            self.report_display.insert("end", f"Owner Name: {client['owner_name']}\n")
            self.report_display.insert("end", f"Contact: {client['owner_contact']}\n")
            self.report_display.insert("end", f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.report_display.insert("end", "-"*90 + "\n\n")

            pets = self.report.get_pets_for_client(client['owner_name'], client['owner_contact'])
            if not pets:
                self.report_display.insert("end", "No pets found for this client.\n\n")
                continue

            for idx, pet in enumerate(pets, 1):
                self.report_display.insert("end", f"[PET #{idx}] {pet['name']} ({pet['species']})\n")
                completed_apts = self.report.get_completed_appointments_for_patient(pet['id'])
                if completed_apts:
                    self.report_display.insert("end", f"  Completed Visits ({len(completed_apts)}):\n")
                    for apt in completed_apts:
                        fee_value = float(apt['fee']) if apt['fee'] else 0.0
                        fee_str = f"P{fee_value:,.2f}"
                        self.report_display.insert("end", f"    - {apt['date']} at {apt['time']} | Dr. {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
                        if apt['notes']:
                            self.report_display.insert("end", f"       Notes: {apt['notes']}\n")
                else:
                    self.report_display.insert("end", "  No completed visits for this pet.\n")
                self.report_display.insert("end", "\n")

            self.report_display.insert("end", "="*90 + "\n\n")

    def export_report(self):
        try:
            content = self.report_display.get("1.0", "end").strip()
            if not content:
                messagebox.showerror("Error", "No report to export. Generate a report first.")
                return
            filename = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Report exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")

    def show_completed_clients(self):
        self.report_display.delete("1.0", "end")
        clients = self.report.find_clients_with_completed()
        if not clients:
            self.report_display.insert("end", "No clients found with completed appointments.\n")
            return

        for client in clients:
            self.report_display.insert("end", "="*90 + "\n")
            self.report_display.insert("end", f"COMPLETED APPOINTMENTS - CLIENT\n")
            self.report_display.insert("end", "="*90 + "\n")
            self.report_display.insert("end", f"Owner Name: {client['owner_name']}\n")
            self.report_display.insert("end", f"Contact: {client['owner_contact']}\n")
            self.report_display.insert("end", f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.report_display.insert("end", "-"*90 + "\n\n")

            pets = self.report.get_pets_for_client(client['owner_name'], client['owner_contact'])
            if not pets:
                self.report_display.insert("end", "No pets found for this client.\n\n")
                continue

            for idx, pet in enumerate(pets, 1):
                self.report_display.insert("end", f"[PET #{idx}] {pet['name']} ({pet['species']})\n")
                completed_apts = self.report.get_completed_appointments_for_patient(pet['id'])
                if completed_apts:
                    self.report_display.insert("end", f"  Completed Visits ({len(completed_apts)}):\n")
                    for apt in completed_apts:
                        fee_value = float(apt['fee']) if apt['fee'] else 0.0
                        fee_str = f"P{fee_value:,.2f}"
                        self.report_display.insert("end", f"    - {apt['date']} at {apt['time']} | Dr. {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
                        if apt['notes']:
                            self.report_display.insert("end", f"       Notes: {apt['notes']}\n")
                else:
                    self.report_display.insert("end", "  No completed visits for this pet.\n")
                self.report_display.insert("end", "\n")

            self.report_display.insert("end", "="*90 + "\n\n")


def show_report_view(parent):
    ReportView(parent)
