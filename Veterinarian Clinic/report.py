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

    def get_monthly_summary(self, year: int = None):
        """Return completed appointments aggregated per month with totals."""
        if year is None:
            year = datetime.now().year
        return db.query(
            """
            SELECT 
                CAST(strftime('%Y', date) AS INTEGER) AS year,
                CAST(strftime('%m', date) AS INTEGER) AS month,
                COUNT(a.id) AS count,
                SUM(COALESCE(d.fee, 0)) AS total_fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.status = 'completed' AND strftime('%Y', date) = ?
            GROUP BY strftime('%Y', date), strftime('%m', date)
            ORDER BY year DESC, month DESC
            """,
            (str(year),)
        )

    def get_monthly_details(self, year: int = None, month: int = None):
        """Return all completed appointments for a given month."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        month_str = f"{int(month):02d}"
        return db.query(
            """
            SELECT a.*, d.name AS doctor_name, d.specialization, d.fee,
                   p.name AS pet_name, p.species, p.owner_name, p.owner_contact
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN patients p ON a.patient_id = p.id
            WHERE a.status = 'completed'
              AND strftime('%Y', a.date) = ?
              AND strftime('%m', a.date) = ?
            ORDER BY a.date DESC, a.time DESC
            """,
            (str(year), month_str)
        )

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
        self.now = datetime.now()
        self.selected_year = self.now.year
        self.selected_month = self.now.month
        self.build()

    def build(self):
        for w in self.parent.winfo_children():
            w.destroy()

        # slight scale increase and shared font helper
        module_scale = 4
        def F(size, weight=None):
            s = int(size + module_scale)
            return ("Arial", s, weight) if weight else ("Arial", s)

        ctk.CTkLabel(self.parent, text="Client History Reports",
                    font=F(34, "bold")).pack(pady=20 + module_scale)

        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Use grid inside container so left/right become equal (50/50)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        right = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        # --- Left: Search / Pickers / Report display ---
        search_frame = ctk.CTkFrame(left, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Search Client:", font=F(14, "bold")).pack(side="left", padx=5)
        # wider entry so buttons remain visible on one row
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Owner name or contact...", width=320 + module_scale*4, font=F(12))
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(search_frame, text="Generate Report",
                     command=lambda: self.generate_report(self.search_entry.get()),
                     fg_color="#2ecc71", width=140, font=F(12, "bold")).pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="Clear",
                     command=lambda: [self.search_entry.delete(0, "end"), self.generate_report()],
                     fg_color="#3498db", width=90, font=F(12)).pack(side="left", padx=5)

        # Monthly picker section
        picker_frame = ctk.CTkFrame(left, fg_color="#ecf0f1", corner_radius=8)
        picker_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(picker_frame, text="Monthly Report", font=F(12, "bold"),
                    text_color="#2c3e50").pack(pady=(10, 5))

        selector_frame = ctk.CTkFrame(picker_frame, fg_color="transparent")
        selector_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(selector_frame, text="Year:", font=F(11)).pack(side="left", padx=5)
        year_options = [str(y) for y in range(self.now.year - 5, self.now.year + 1)]
        self.year_combobox = ctk.CTkComboBox(selector_frame, values=year_options,
                                              variable=ctk.StringVar(value=str(self.selected_year)),
                                              state="readonly", font=F(11), width=120 + module_scale*2)
        self.year_combobox.pack(side="left", padx=5)

        ctk.CTkLabel(selector_frame, text="Month:", font=F(11)).pack(side="left", padx=5)
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        self.month_combobox = ctk.CTkComboBox(selector_frame, values=months,
                                               variable=ctk.StringVar(value=months[self.selected_month - 1]),
                                               state="readonly", font=F(11), width=140 + module_scale*2)
        self.month_combobox.pack(side="left", padx=5)

        button_frame = ctk.CTkFrame(picker_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkButton(button_frame, text="Show Monthly Report",
                     command=self.on_monthly_report_click,
                     fg_color="#1abc9c", width=160 + module_scale*4, height=34 + module_scale, font=F(11)).pack(side="left", padx=5)

        ctk.CTkButton(button_frame, text="All Completed",
                     command=self.show_completed_clients,
                     fg_color="#9b59b6", width=150 + module_scale*2, height=34 + module_scale, font=F(11)).pack(side="left", padx=5)

        # Report display (left) - slightly larger font
        self.report_display = ctk.CTkTextbox(left, font=F(12))
        self.report_display.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Right: Quick Stats and export ---
        ctk.CTkLabel(right, text="Quick Stats", font=F(20, "bold")).pack(pady=15)

        self.stats_text = ctk.CTkTextbox(right, font=F(12), height=400)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(right, text="Export Report to File", command=self.export_report,
                     fg_color="#e67e22", height=44 + module_scale, font=F(12, "bold")).pack(fill="x", padx=10, pady=(10, 20))

        # Initialize
        self.update_stats()
        self.generate_report()

    def on_monthly_report_click(self):
        """Handle monthly report button click."""
        year = int(self.year_combobox.get())
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month = months.index(self.month_combobox.get()) + 1
        self.selected_year = year
        self.selected_month = month
        self.show_monthly_report(year, month)

    def update_stats(self):
        s = self.report.stats()
        self.stats_text.delete('1.0', 'end')
        self.stats_text.insert("end", "CLINIC STATISTICS\n")
        self.stats_text.insert("end", "="*40 + "\n\n")
        
        self.stats_text.insert("end", f"Total Clients:           {s['total_clients']}\n")
        self.stats_text.insert("end", f"Total Pets:              {s['total_pets']}\n")
        self.stats_text.insert("end", f"Total Appointments:     {s['total_apts']}\n")
        self.stats_text.insert("end", f"Completed Appointments: {s['completed_apts']}\n")
        
        self.stats_text.insert("end", "\n" + "="*40 + "\n")
        self.stats_text.insert("end", "TOP CLIENTS BY VISITS\n")
        self.stats_text.insert("end", "="*40 + "\n\n")
        
        top_clients = self.report.top_clients_by_visits()
        if top_clients:
            for idx, row in enumerate(top_clients, 1):
                visits = row['visits']
                self.stats_text.insert("end", f"{idx}. {row['owner_name']:<28} {visits} visit(s)\n")
        else:
            self.stats_text.insert("end", "No completed visits recorded yet.\n")
        
        self.stats_text.configure(state="disabled")

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
                        self.report_display.insert("end", f"    - {apt['date']} at {apt['time']} | {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
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

    def show_monthly_report(self, year: int = None, month: int = None):
        """Display monthly report in the main display area."""
        self.report_display.delete("1.0", "end")
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        details = self.report.get_monthly_details(year, month)
        summary_rows = self.report.get_monthly_summary(year)

        # Header
        self.report_display.insert("end", "="*90 + "\n")
        self.report_display.insert("end", f"MONTHLY REPORT - {year}-{int(month):02d}\n")
        self.report_display.insert("end", "="*90 + "\n")
        self.report_display.insert("end", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.report_display.insert("end", "-"*90 + "\n\n")

        # Year summary
        if summary_rows:
            self.report_display.insert("end", "YEAR SUMMARY (Completed Appointments)\n")
            for row in summary_rows:
                fee_val = float(row['total_fee']) if row['total_fee'] else 0.0
                fee_str = f"P{fee_val:,.2f}"
                self.report_display.insert("end", f"  - {row['year']}-{int(row['month']):02d}: {row['count']} visit(s), Total Fees: {fee_str}\n")
            self.report_display.insert("end", "\n")
        else:
            self.report_display.insert("end", "No completed appointments recorded this year.\n\n")

        # Details for selected month
        self.report_display.insert("end", f"DETAILS FOR {year}-{int(month):02d}\n")
        self.report_display.insert("end", "-"*90 + "\n")
        if details:
            total_fee = 0.0
            for apt in details:
                fee_value = float(apt['fee']) if apt['fee'] else 0.0
                total_fee += fee_value
                fee_str = f"P{fee_value:,.2f}"
                self.report_display.insert("end", (
                    f"- {apt['date']} {apt['time']} | {apt['doctor_name']} ({apt['specialization']}) | "
                    f"Pet: {apt['pet_name']} ({apt['species']}) | Owner: {apt['owner_name']} | Fee: {fee_str}\n"
                ))
                if apt['notes']:
                    self.report_display.insert("end", f"    Notes: {apt['notes']}\n")
            self.report_display.insert("end", "\n")
            self.report_display.insert("end", f"Total Completed Visits: {len(details)}\n")
            self.report_display.insert("end", f"Total Fees: P{total_fee:,.2f}\n")
        else:
            self.report_display.insert("end", "No completed appointments for this month.\n")

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
                        self.report_display.insert("end", f"    - {apt['date']} at {apt['time']} | {apt['doctor_name']} ({apt['specialization']}) | Fee: {fee_str}\n")
                        if apt['notes']:
                            self.report_display.insert("end", f"       Notes: {apt['notes']}\n")
                else:
                    self.report_display.insert("end", "  No completed visits for this pet.\n")
                self.report_display.insert("end", "\n")

            self.report_display.insert("end", "="*90 + "\n\n")


def show_report_view(parent):
    ReportView(parent)
