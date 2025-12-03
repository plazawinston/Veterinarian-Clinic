"""
Patients Module - Manage patient records for the veterinary clinic.

Provides:
- Patient model for create/update/delete operations
- Searchable listing of patients
- Patient management UI via show_patients_view(parent)

Notes:
- Expects global `db` (Database) and `app` to be assigned by the main application.
- Uses db.query / db.execute and returns sqlite3.Row / dict-like rows.
"""

import customtkinter as ctk
from tkinter import messagebox
from abc import ABC, abstractmethod

app = None
db = None
refs = {}


class PatientBase(ABC):
    def __init__(self, id=None, name='', species='', breed='', age=0, owner_name='', owner_contact='', notes=''):
        self.id = id
        self.name = name
        self.species = species
        self.breed = breed
        self.age = int(age or 0)
        self.owner_name = owner_name
        self.owner_contact = owner_contact
        self.notes = notes

    @abstractmethod
    def save(self):
        raise NotImplementedError()

    @abstractmethod
    def delete(self):
        raise NotImplementedError()


class Patient(PatientBase):
    def save(self):
        if not self.name or not self.owner_name:
            raise ValueError('Name and Owner Name required')

        if self.id:
            db.execute(
                """
                UPDATE patients SET name=?, species=?, breed=?, age=?, owner_name=?, owner_contact=?, notes=? WHERE id=?
                """,
                (self.name, self.species, self.breed, self.age, self.owner_name, self.owner_contact, self.notes, self.id)
            )
        else:
            db.execute(
                """
                INSERT INTO patients (name, species, breed, age, owner_name, owner_contact, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.name, self.species, self.breed, self.age, self.owner_name, self.owner_contact, self.notes)
            )

    def delete(self):
        if not self.id:
            raise ValueError('No ID to delete')
        db.execute("DELETE FROM patients WHERE id=?", (self.id,))

    @staticmethod
    def list_all(query='', species=''):
        sql = "SELECT * FROM patients"
        params = []
        conditions = []
        if query:
            conditions.append("(name LIKE ? OR owner_name LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if species:
            conditions.append("species = ?")
            params.append(species)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY name"
        return db.query(sql, tuple(params))


class PatientView:
    def __init__(self, parent):
        self.parent = parent
        self.selected_card = [None]
        self.selected_id = [None]
        self.fields = {}
        self.build()

    def build(self):
        for w in self.parent.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.parent, text="Patient Management", font=("Arial", 32, "bold")).pack(pady=20)

        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20)

        self.left = ctk.CTkFrame(self.container, fg_color="white", corner_radius=10)
        self.left.pack(side="left", fill="both", expand=True, padx=(0,10))

        self.search_frame = ctk.CTkFrame(self.left, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search...", width=300)
        self.search_entry.pack(side="left", padx=5)

        species_list = ["All"] + [row['species'] for row in db.query("SELECT DISTINCT species FROM patients ORDER BY species")]
        self.species_combo = ctk.CTkComboBox(self.search_frame, values=species_list, width=120, command=lambda s: self.load_patients(self.search_entry.get(), "" if s == "All" else s))
        self.species_combo.pack(side="left", padx=5)
        self.species_combo.set("All")

        ctk.CTkButton(self.search_frame, text="Search", width=80, command=lambda: self.load_patients(self.search_entry.get(), "" if self.species_combo.get() == "All" else self.species_combo.get())).pack(side="left", padx=5)
        
        ctk.CTkButton(self.search_frame, text="Clear", width=80, command=lambda: [self.search_entry.delete(0, "end"), self.species_combo.set("All"), self.load_patients()]).pack(side="left", padx=5)
        
        ctk.CTkButton(self.search_frame, text="Refresh", width=80, command=self.refresh_patients).pack(side="left", padx=5)

        self.patient_container = ctk.CTkScrollableFrame(self.left, fg_color="transparent")
        self.patient_container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.left, text="Click a patient card to load details for editing.", font=("Arial", 11), text_color="#7f8c8d").pack(anchor="w", padx=12, pady=(4,8))

        self.right = ctk.CTkFrame(self.container, fg_color="white", corner_radius=10, width=400)
        self.right.pack(side="right", fill="both", padx=(10,0))
        self.right.pack_propagate(False)

        ctk.CTkLabel(self.right, text="Patient Details", font=("Arial", 20, "bold")).pack(pady=15)

        # Validation function for integer-only fields
        def validate_integer(P):
            if P == "" or P.isdigit():
                return True
            return False

        vcmd = (self.right.register(validate_integer), '%P')

        for label in ["Name", "Species", "Breed", "Age", "Owner Name", "Owner Contact", "Notes"]:
            ctk.CTkLabel(self.right, text=f"{label}:").pack(anchor="w", padx=10, pady=(5,0))
            if label == "Notes":
                self.fields[label] = ctk.CTkTextbox(self.right, height=80)
            else:
                if label in ["Age", "Owner Contact"]:
                    self.fields[label] = ctk.CTkEntry(self.right, validate="key", validatecommand=vcmd)
                else:
                    self.fields[label] = ctk.CTkEntry(self.right)
            self.fields[label].pack(fill="x", padx=10, pady=5)

        self.selected_label = ctk.CTkLabel(self.right, text="Selected ID: None", font=("Arial", 11))
        self.selected_label.pack(anchor="e", padx=10, pady=(6,0))

        btn_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=self.save_patient, fg_color="#2ecc71")
        save_btn.pack(side="left", padx=5, expand=True, fill="x")

        new_btn = ctk.CTkButton(btn_frame, text="New", command=self.clear_form, fg_color="#3498db")
        new_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.delete_btn = ctk.CTkButton(btn_frame, text="Delete", command=self.delete_patient, fg_color="#e74c3c")
        self.delete_btn.pack(side="left", padx=5, expand=True, fill="x")
        self.delete_btn.configure(state="disabled")

        self.load_patients()

    def make_patient_card(self, p):
        card = ctk.CTkFrame(self.patient_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
        card.pack(fill="x", padx=10, pady=6)

        header = f"{p['name']} ({p['species']})"
        ctk.CTkLabel(card, text=header, font=("Arial", 13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
        ctk.CTkLabel(card, text=f"Owner: {p['owner_name']} | {p['owner_contact']}", font=("Arial", 11), anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))

        def on_card_click(e=None, pid=p['id'], card_ref=card):
            try:
                patient = db.query("SELECT * FROM patients WHERE id=?", (pid,))[0]
            except Exception:
                return
            try:
                if self.selected_card[0] and self.selected_card[0] != card_ref:
                    self.selected_card[0].configure(fg_color="#f8f9fa")
            except Exception:
                pass
            try:
                card_ref.configure(fg_color="#e8f8f5")
            except Exception:
                pass
            self.selected_card[0] = card_ref
            self.selected_id[0] = pid
            self.fields["Name"].delete(0, "end"); self.fields["Name"].insert(0, patient['name'] or "")
            self.fields["Species"].delete(0, "end"); self.fields["Species"].insert(0, patient['species'] or "")
            self.fields["Breed"].delete(0, "end"); self.fields["Breed"].insert(0, patient['breed'] or "")
            self.fields["Age"].delete(0, "end"); self.fields["Age"].insert(0, str(patient['age'] or 0))
            self.fields["Owner Name"].delete(0, "end"); self.fields["Owner Name"].insert(0, patient['owner_name'] or "")
            self.fields["Owner Contact"].delete(0, "end"); self.fields["Owner Contact"].insert(0, patient['owner_contact'] or "")
            self.fields["Notes"].delete("1.0", "end"); self.fields["Notes"].insert("1.0", patient['notes'] or "")
            self.selected_label.configure(text=f"Selected ID: {pid}")
            self.delete_btn.configure(state="normal")

        card.bind("<Button-1>", on_card_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_card_click)

        return card

    def load_patients(self, query="", species=""):
        for w in self.patient_container.winfo_children():
            w.destroy()
        patients = Patient.list_all(query, species)
        for p in patients:
            self.make_patient_card(p)

    def refresh_patients(self):
        new_species_list = ["All"] + [row['species'] for row in db.query("SELECT DISTINCT species FROM patients ORDER BY species")]
        self.species_combo.configure(values=new_species_list)
        self.load_patients(self.search_entry.get(), "" if self.species_combo.get() == "All" else self.species_combo.get())

    def clear_form(self):
        self.selected_id[0] = None
        try:
            if self.selected_card[0]:
                self.selected_card[0].configure(fg_color="#f8f9fa")
                self.selected_card[0] = None
        except Exception:
            pass
        for field in self.fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, "end")
            else:
                field.delete("1.0", "end")
        self.selected_label.configure(text="Selected ID: None")
        self.delete_btn.configure(state="disabled")

    def save_patient(self):
        try:
            data = {k: (v.get() if isinstance(v, ctk.CTkEntry) else v.get("1.0", "end").strip()) for k, v in self.fields.items()}
            if not data["Name"] or not data["Owner Name"]:
                messagebox.showerror("Error", "Name and Owner Name required")
                return
            age_value = int(data["Age"]) if data["Age"] and data["Age"].isdigit() else 0
            pat = Patient(self.selected_id[0], data["Name"], data["Species"], data["Breed"], age_value, data["Owner Name"], data["Owner Contact"], data["Notes"])
            pat.save()
            messagebox.showinfo("Success", "Patient saved")
            self.clear_form()
            self.load_patients()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_patient(self):
        if self.selected_id[0] and messagebox.askyesno("Confirm", "Delete this patient?"):
            pat = Patient(id=self.selected_id[0])
            pat.delete()
            messagebox.showinfo("Success", "Patient deleted")
            self.clear_form()
            self.load_patients()


def show_patients_view(parent):
    pv = PatientView(parent)
    return pv

