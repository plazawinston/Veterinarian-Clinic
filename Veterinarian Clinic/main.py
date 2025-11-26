import customtkinter as ctk
from database import Database
import patients
import appointments
import dashboard
import report
import invoice
from login import show_login

ctk.set_appearance_mode("light")

class VetClinicApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.db = Database
        
        for module in [patients, appointments, dashboard, report, invoice]:
            module.app = self
            module.db = self.db
        
        self.title("Vet Clinic Management")
        self.geometry("1400x850")
        
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#2c3e50")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="Vet Clinic", font=("Arial", 24, "bold"), 
                    text_color="white").pack(pady=30)
        
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#f0f0f0")
        self.content.pack(side="right", fill="both", expand=True)
        
        for text, cmd, color in [
            ("Dashboard", lambda: dashboard.show_dashboard_view(self.content), "#3498db"),
            ("Patients", lambda: patients.show_patients_view(self.content), "#2ecc71"),
            ("Appointments", lambda: appointments.show_appointments_view(self.content), "#e67e22"),
            ("Reports", lambda: report.show_report_view(self.content), "#9b59b6"),
            ("Invoices", lambda: invoice.show_invoice_view(self.content), "#f39c12"),
        ]:
            ctk.CTkButton(sidebar, text=text, command=cmd, font=("Arial", 16),
                         fg_color=color, height=50).pack(fill="x", padx=10, pady=5)
        
        dashboard.show_dashboard_view(self.content)

if __name__ == "__main__":
    if show_login():
        app = VetClinicApp()
        app.mainloop()
    else:
        print("Login cancelled or failed")
