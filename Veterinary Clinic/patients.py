import customtkinter as ctk
from tkinter import messagebox

# set by main.py
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
    
    # left: patient list
    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))
    
    # search
    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)
    
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...", width=300)
    search_entry.pack(side="left", padx=5)
    
    patient_list = ctk.CTkTextbox(left, height=500)
    patient_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def load_patients(query=""):
        patient_list.delete("1.0", "end")
        if query:
            patients = db.query(
                "SELECT * FROM patients WHERE name LIKE ? OR owner_name LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
        else:
            patients = db.query("SELECT * FROM patients ORDER BY name")
        
        for p in patients:
            patient_list.insert("end", f"ID: {p['id']} | {p['name']} ({p['species']})\n")
            patient_list.insert("end", f"Owner: {p['owner_name']} | {p['owner_contact']}\n")
            patient_list.insert("end", "-"*70 + "\n")
    
    ctk.CTkButton(search_frame, text="Search", width=80,
                 command=lambda: load_patients(search_entry.get())).pack(side="left", padx=5)
    ctk.CTkButton(search_frame, text="Clear", width=80,
                 command=lambda: [search_entry.delete(0, "end"), load_patients()]).pack(side="left")
    
    # right: form
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
        for field in fields.values():
            if isinstance(field, ctk.CTkEntry):
                field.delete(0, "end")
            else:
                field.delete("1.0", "end")
    
    def save_patient():
        try:
            data = {k: (v.get() if isinstance(v, ctk.CTkEntry) else v.get("1.0", "end").strip()) 
                   for k, v in fields.items()}
            
            if not data["Name"] or not data["Owner Name"]:
                messagebox.showerror("Error", "Name and Owner Name required")
                return
            
            if selected_id[0]:
                db.execute("""
                    UPDATE patients SET name=?, species=?, breed=?, age=?, 
                    owner_name=?, owner_contact=?, notes=? WHERE id=?
                """, (data["Name"], data["Species"], data["Breed"], 
                      int(data["Age"] or 0), data["Owner Name"], 
                      data["Owner Contact"], data["Notes"], selected_id[0]))
                messagebox.showinfo("Success", "Patient updated")
            else:
                db.execute("""
                    INSERT INTO patients (name, species, breed, age, owner_name, owner_contact, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data["Name"], data["Species"], data["Breed"],
                      int(data["Age"] or 0), data["Owner Name"], 
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
    
    def on_select(event):
        try:
            idx = patient_list.index(f"@{event.x},{event.y}")
            line = patient_list.get(idx.split('.')[0] + ".0", idx.split('.')[0] + ".end")
            if "ID:" in line:
                pid = int(line.split("ID:")[1].split("|")[0].strip())
                patient = db.query("SELECT * FROM patients WHERE id=?", (pid,))[0]
                selected_id[0] = pid
                
                fields["Name"].delete(0, "end")
                fields["Name"].insert(0, patient['name'])
                fields["Species"].delete(0, "end")
                fields["Species"].insert(0, patient['species'])
                fields["Breed"].delete(0, "end")
                fields["Breed"].insert(0, patient['breed'])
                fields["Age"].delete(0, "end")
                fields["Age"].insert(0, str(patient['age']))
                fields["Owner Name"].delete(0, "end")
                fields["Owner Name"].insert(0, patient['owner_name'])
                fields["Owner Contact"].delete(0, "end")
                fields["Owner Contact"].insert(0, patient['owner_contact'])
                fields["Notes"].delete("1.0", "end")
                fields["Notes"].insert("1.0", patient['notes'] or "")
        except:
            pass
    
    patient_list.bind("<Button-1>", on_select)
    
    btn_frame = ctk.CTkFrame(right, fg_color="transparent")
    btn_frame.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkButton(btn_frame, text="Save", command=save_patient, 
                 fg_color="#2ecc71").pack(side="left", padx=5, expand=True, fill="x")
    ctk.CTkButton(btn_frame, text="New", command=clear_form,
                 fg_color="#3498db").pack(side="left", padx=5, expand=True, fill="x")
    ctk.CTkButton(btn_frame, text="Delete", command=delete_patient,
                 fg_color="#e74c3c").pack(side="left", padx=5, expand=True, fill="x")
    
    load_patients()