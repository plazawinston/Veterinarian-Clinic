"""
CLASS: 3
"""
import customtkinter as ctk
from tkinter import messagebox
from abc import ABC, abstractmethod
import namtrash

app = None
db = None
refs = {}


## Abstract patient record model
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
    ## Persist the patient record
    def save(self):
        raise NotImplementedError()

    @abstractmethod
    ## Delete the patient record
    def delete(self):
        raise NotImplementedError()


## Concrete patient model implementing persistence
class Patient(PatientBase):
    ## Insert or update a patient row
    def add_patient(self):
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

    ## Save delegator (fulfills abstract interface)
    def save(self):
        return self.add_patient()

    ## Delete this patient by id
    def delete(self):
        if not self.id:
            raise ValueError('No ID to delete')
        # Fetch the current patient row so we can save it to the trash and soft-delete
        try:
            row = db.query("SELECT * FROM patients WHERE id=?", (self.id,))[0]
        except Exception:
            row = None
        if row:
            try:
                namtrash.add_deleted_patient(row)
            except Exception:
                pass
        # Soft-delete: mark patient as deleted so appointments keep their FK intact
        db.execute("UPDATE patients SET is_deleted=1 WHERE id=?", (self.id,))

    @staticmethod
    ## Return list of patients, optional filtering by query and species
    def list_all(query='', species=''):
        sql = "SELECT * FROM patients WHERE is_deleted=0"
        params = []
        conditions = []
        if query:
            conditions.append("(name LIKE ? OR owner_name LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if species:
            conditions.append("species = ?")
            params.append(species)
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        sql += " ORDER BY name"
        return db.query(sql, tuple(params))


## UI view for patient management (list + detail form)
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

        # slight scale increase for this module
        self.module_scale = 5
        ## Font helper for patients module
        def F(size, weight=None):
            s = int(size + self.module_scale)
            return ("Arial", s, weight) if weight else ("Arial", s)
        self.F = F

        ctk.CTkLabel(self.parent, text="Patient Management", font=self.F(32, "bold")).pack(pady=20 + self.module_scale)

        self.container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20)

        self.left = ctk.CTkFrame(self.container, fg_color="white", corner_radius=10)
        self.left.pack(side="left", fill="both", expand=True, padx=(0,10))

        self.search_frame = ctk.CTkFrame(self.left, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search...", width=300 + self.module_scale * 8, font=self.F(12))
        self.search_entry.pack(side="left", padx=5)

        species_list = ["All"] + [row['species'] for row in db.query("SELECT DISTINCT species FROM patients ORDER BY species")]
        self.species_combo = ctk.CTkComboBox(
            self.search_frame,
            values=species_list,
            width=120 + self.module_scale * 6,
            command=lambda s: self.load_patients(self.search_entry.get(), "" if s == "All" else s),
            font=self.F(12)
        )
        self.species_combo.pack(side="left", padx=5)
        self.species_combo.set("All")

        ctk.CTkButton(self.search_frame, text="Search", width=80 + self.module_scale * 4, command=lambda: self.load_patients(self.search_entry.get(), "" if self.species_combo.get() == "All" else self.species_combo.get()), font=self.F(12)).pack(side="left", padx=5)
        
        ctk.CTkButton(self.search_frame, text="Clear", width=80 + self.module_scale * 4, command=lambda: [self.search_entry.delete(0, "end"), self.species_combo.set("All"), self.load_patients()], font=self.F(12)).pack(side="left", padx=5)
        
        ctk.CTkButton(self.search_frame, text="Refresh", width=80 + self.module_scale * 4, command=self.refresh_patients, font=self.F(12)).pack(side="left", padx=5)

        self.patient_container = ctk.CTkScrollableFrame(self.left, fg_color="transparent")
        self.patient_container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.left, text="Click a patient card to load details for editing.", font=self.F(11), text_color="#7f8c8d").pack(anchor="w", padx=12, pady=(4,8))

        self.right = ctk.CTkFrame(self.container, fg_color="white", corner_radius=10, width=420 + self.module_scale * 8)
        self.right.pack(side="right", fill="both", padx=(10,0))
        self.right.pack_propagate(False)

        ctk.CTkLabel(self.right, text="Patient Details", font=self.F(20, "bold")).pack(pady=15)

        # Validation function for integer-only fields
        def validate_integer(P):
            if P == "" or P.isdigit():
                return True
            return False

        vcmd = (self.right.register(validate_integer), '%P')

        for label in ["Name", "Species", "Breed", "Age", "Owner Name", "Owner Contact", "Notes"]:
            ctk.CTkLabel(self.right, text=f"{label}:", font=self.F(12)).pack(anchor="w", padx=10, pady=(5,0))
            if label == "Notes":
                self.fields[label] = ctk.CTkTextbox(self.right, height=80 + self.module_scale * 6, font=self.F(11))
            else:
                if label in ["Age", "Owner Contact"]:
                    self.fields[label] = ctk.CTkEntry(self.right, validate="key", validatecommand=vcmd, font=self.F(12))
                else:
                    self.fields[label] = ctk.CTkEntry(self.right, font=self.F(12))
            self.fields[label].pack(fill="x", padx=10, pady=5)

        self.selected_label = ctk.CTkLabel(self.right, text="Selected ID: None", font=self.F(11))
        self.selected_label.pack(anchor="e", padx=10, pady=(6,0))

        btn_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=self.save_patient, fg_color="#2ecc71", height=40 + self.module_scale, font=self.F(13, "bold"))
        save_btn.pack(side="left", padx=5, expand=True, fill="x")

        new_btn = ctk.CTkButton(btn_frame, text="New", command=self.clear_form, fg_color="#3498db", height=40 + self.module_scale, font=self.F(13, "bold"))
        new_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.delete_btn = ctk.CTkButton(btn_frame, text="Delete", command=self.delete_patient, fg_color="#e74c3c", height=40 + self.module_scale, font=self.F(13, "bold"))
        self.delete_btn.pack(side="left", padx=5, expand=True, fill="x")
        self.delete_btn.configure(state="disabled")

        self.load_patients()

    ## Create a clickable patient card in the list
    def make_patient_card(self, p):
        card = ctk.CTkFrame(self.patient_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
        card.pack(fill="x", padx=10, pady=6)

        header = f"{p['name']} ({p['species']})"
        ctk.CTkLabel(card, text=header, font=self.F(13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10 + self.module_scale, pady=(8,2))
        ctk.CTkLabel(card, text=f"Owner: {p['owner_name']} | {p['owner_contact']}", font=self.F(11), anchor="w").grid(row=1, column=0, sticky="w", padx=10 + self.module_scale, pady=(0,8))

        ## Click handler: load patient details into form
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

    ## Load patients matching optional query and species filter
    def load_patients(self, query="", species=""):
        for w in self.patient_container.winfo_children():
            w.destroy()
        patients = Patient.list_all(query, species)
        for p in patients:
            self.make_patient_card(p)

    ## Refresh species list and reload patients
    def refresh_patients(self):
        new_species_list = ["All"] + [row['species'] for row in db.query("SELECT DISTINCT species FROM patients ORDER BY species")]
        self.species_combo.configure(values=new_species_list)
        self.load_patients(self.search_entry.get(), "" if self.species_combo.get() == "All" else self.species_combo.get())

    ## Clear detail form and reset selection
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

    ## Read form inputs and save patient to DB
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

    ## Delete the currently selected patient (UI action)
    def delete_patient(self):
        if self.selected_id[0] and messagebox.askyesno("Confirm", "Delete this patient?"):
            pat = Patient(id=self.selected_id[0])
            pat.delete()
            messagebox.showinfo("Success", "Patient deleted")
            self.clear_form()
            self.load_patients()


## Show patients management view in the parent container
def show_patients_view(parent):
    pv = PatientView(parent)
    return pv

