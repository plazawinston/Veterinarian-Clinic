import customtkinter as ctk
from tkinter import messagebox

app = None
db = None
refs = {}

def show_patients_view(parent):
    for w in parent.winfo_children():
        w.destroy()
    
    ctk.CTkLabel(parent, text="Patient Management", 
                font=("Arial", 32, "bold")).pack(pady=20)
    
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)
    
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...", width=300)
    search_entry.pack(side="left", padx=5)
    
    # Scrollable frame to hold patient cards
    patient_container = ctk.CTkScrollableFrame(left, fg_color="transparent")
    patient_container.pack(fill="both", expand=True, padx=10, pady=10)

    # Instruction label
    ctk.CTkLabel(left, text="Click a patient card to load details for editing.",
                 font=("Arial", 11), text_color="#7f8c8d").pack(anchor="w", padx=12, pady=(4,8))
    
    # keep reference to currently selected card widget
    selected_card = [None]

    def make_patient_card(p):
        card = ctk.CTkFrame(patient_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
        card.pack(fill="x", padx=10, pady=6)

        header = f"{p['name']} ({p['species']})"
        ctk.CTkLabel(card, text=header, font=("Arial", 13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
        ctk.CTkLabel(card, text=f"Owner: {p['owner_name']} | {p['owner_contact']}", font=("Arial", 11), anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))

        # bind click to select this patient
        def on_card_click(e=None, pid=p['id'], card_ref=card):
            try:
                patient = db.query("SELECT * FROM patients WHERE id=?", (pid,))[0]
            except Exception:
                return
            # remove highlight from previous
            try:
                if selected_card[0] and selected_card[0] != card_ref:
                    selected_card[0].configure(fg_color="#f8f9fa")
            except Exception:
                pass
            # highlight this
            try:
                card_ref.configure(fg_color="#e8f8f5")
            except Exception:
                pass
            selected_card[0] = card_ref
            # set selected id and populate form
            selected_id[0] = pid
            fields["Name"].delete(0, "end"); fields["Name"].insert(0, patient['name'] or "")
            fields["Species"].delete(0, "end"); fields["Species"].insert(0, patient['species'] or "")
            fields["Breed"].delete(0, "end"); fields["Breed"].insert(0, patient['breed'] or "")
            fields["Age"].delete(0, "end"); fields["Age"].insert(0, str(patient['age'] or 0))
            fields["Owner Name"].delete(0, "end"); fields["Owner Name"].insert(0, patient['owner_name'] or "")
            fields["Owner Contact"].delete(0, "end"); fields["Owner Contact"].insert(0, patient['owner_contact'] or "")
            fields["Notes"].delete("1.0", "end"); fields["Notes"].insert("1.0", patient['notes'] or "")
            selected_label.configure(text=f"Selected ID: {pid}")
            delete_btn.configure(state="normal")

        # bind click on card and its children
        card.bind("<Button-1>", on_card_click)
        for child in card.winfo_children():
            child.bind("<Button-1>", on_card_click)

        return card

    def load_patients(query=""):
        # clear container
        for w in patient_container.winfo_children():
            w.destroy()
        if query:
            patients = db.query(
                "SELECT * FROM patients WHERE name LIKE ? OR owner_name LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
        else:
            patients = db.query("SELECT * FROM patients ORDER BY name")

        for p in patients:
            make_patient_card(p)
    
    ctk.CTkButton(search_frame, text="Search", width=80,
                 command=lambda: load_patients(search_entry.get())).pack(side="left", padx=5)
    ctk.CTkButton(search_frame, text="Clear", width=80,
                 command=lambda: [search_entry.delete(0, "end"), load_patients()]).pack(side="left")
    
    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=400)
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)
    
    ctk.CTkLabel(right, text="Patient Details", font=("Arial", 20, "bold")).pack(pady=15)
    
    fields = {}
    for label in ["Name", "Species", "Breed", "Age", "Owner Name", "Owner Contact", "Notes"]:
        ctk.CTkLabel(right, text=f"{label}:").pack(anchor="w", padx=10, pady=(5,0))
        if label == "Notes":
            fields[label] = ctk.CTkTextbox(right, height=80)
        else:
            fields[label] = ctk.CTkEntry(right)
        fields[label].pack(fill="x", padx=10, pady=5)
    
    selected_id = [None]
    
    def clear_form():
        selected_id[0] = None
        # remove any highlighted selection card
        try:
            if selected_card[0]:
                selected_card[0].configure(fg_color="#f8f9fa")
                selected_card[0] = None
        except Exception:
            pass
        for field in fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, "end")
            else:
                field.delete("1.0", "end")
        # update selected label
        selected_label.configure(text="Selected ID: None")
        delete_btn.configure(state="disabled")
    
    def save_patient():
        try:
            data = {k: (v.get() if isinstance(v, ctk.CTkEntry) else v.get("1.0", "end").strip()) 
                   for k, v in fields.items()}
            
            if not data["Name"] or not data["Owner Name"]:
                messagebox.showerror("Error", "Name and Owner Name required")
                return
            
            age_value = int(data["Age"]) if data["Age"] and data["Age"].isdigit() else 0
            
            if selected_id[0]:
                db.execute("""
                    UPDATE patients SET name=?, species=?, breed=?, age=?, 
                    owner_name=?, owner_contact=?, notes=? WHERE id=?
                """, (data["Name"], data["Species"], data["Breed"], 
                      age_value, data["Owner Name"], 
                      data["Owner Contact"], data["Notes"], selected_id[0]))
                messagebox.showinfo("Success", "Patient updated")
            else:
                db.execute("""
                    INSERT INTO patients (name, species, breed, age, owner_name, owner_contact, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data["Name"], data["Species"], data["Breed"],
                      age_value, data["Owner Name"], 
                      data["Owner Contact"], data["Notes"]))
                messagebox.showinfo("Success", "Patient added")
            
            clear_form()
            load_patients()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def delete_patient():
        if selected_id[0] and messagebox.askyesno("Confirm", "Delete this patient?"):
            db.execute("DELETE FROM patients WHERE id=?", (selected_id[0],))
            messagebox.showinfo("Success", "Patient deleted")
            clear_form()
            load_patients()
    
    # card click handlers populate the form; old textbox handlers removed
    
    btn_frame = ctk.CTkFrame(right, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=10)
    save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_patient, 
                 fg_color="#2ecc71")
    save_btn.pack(side="left", padx=5, expand=True, fill="x")

    new_btn = ctk.CTkButton(btn_frame, text="New", command=clear_form,
                 fg_color="#3498db")
    new_btn.pack(side="left", padx=5, expand=True, fill="x")

    delete_btn = ctk.CTkButton(btn_frame, text="Delete", command=delete_patient,
                 fg_color="#e74c3c")
    delete_btn.pack(side="left", padx=5, expand=True, fill="x")
    delete_btn.configure(state="disabled")

    # Selected ID display
    selected_label = ctk.CTkLabel(right, text="Selected ID: None", font=("Arial", 11))
    selected_label.pack(anchor="e", padx=10, pady=(6,0))
    
    load_patients()

    # selection highlighting handled per-card
