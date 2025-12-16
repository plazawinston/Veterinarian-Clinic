"""
Simple "trash" module to hold recently deleted patient records.
"""
# NOTE: This module provides a lightweight "recycle bin" for deleted patients.
# It stores recently deleted patient rows so they can be restored or permanently removed.
import customtkinter as ctk
from tkinter import messagebox

app = None
db = None
refs = {}


## Save a deleted patient into the recent_deleted table
def add_deleted_patient(pat_row):
    """Save a patient row/dict into recent_deleted table.
    Accepts sqlite3.Row or dict-like with the patient fields.
    """
    if db is None:
        raise RuntimeError('Database not initialized for namtrash')
    try:
        # normalize access
        get = lambda r, k: (r[k] if isinstance(r, dict) or hasattr(r, '__getitem__') else getattr(r, k))
    except Exception:
        get = lambda r, k: r.get(k)

    pid = pat_row['id'] if hasattr(pat_row, '__getitem__') else getattr(pat_row, 'id', None)
    name = pat_row['name']
    species = pat_row.get('species') if isinstance(pat_row, dict) else pat_row['species']
    breed = pat_row.get('breed') if isinstance(pat_row, dict) else pat_row['breed']
    age = pat_row.get('age') if isinstance(pat_row, dict) else pat_row['age']
    owner_name = pat_row.get('owner_name') if isinstance(pat_row, dict) else pat_row['owner_name']
    owner_contact = pat_row.get('owner_contact') if isinstance(pat_row, dict) else pat_row['owner_contact']
    notes = pat_row.get('notes') if isinstance(pat_row, dict) else pat_row['notes']

    db.execute(
        """
        INSERT INTO recent_deleted (patient_id, name, species, breed, age, owner_name, owner_contact, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (pid, name, species, breed, age, owner_name, owner_contact, notes)
    )


## Return list of recently deleted records (most recent first)
def list_deleted():
    if db is None:
        raise RuntimeError('Database not initialized for namtrash')
    return db.query("SELECT * FROM recent_deleted ORDER BY deleted_at DESC")


## Restore a deleted patient back to the patients table
def restore_deleted(record_id):
    """Restore a deleted patient back into `patients` table and remove from `recent_deleted`.
    Returns new patient id.
    """
    if db is None:
        raise RuntimeError('Database not initialized for namtrash')
    row = db.query("SELECT * FROM recent_deleted WHERE id=?", (record_id,))
    if not row:
        raise ValueError('Record not found')
    r = row[0]
    pid = r['patient_id']
    # If original patient row exists, un-delete it. Otherwise insert with explicit id to preserve id.
    existing = db.query("SELECT * FROM patients WHERE id=?", (pid,))
    if existing:
        db.execute("UPDATE patients SET is_deleted=0 WHERE id=?", (pid,))
        new_id = pid
    else:
        try:
            db.execute(
                "INSERT INTO patients (id, name, species, breed, age, owner_name, owner_contact, notes, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
                (pid, r['name'], r['species'], r['breed'], r['age'], r['owner_name'], r['owner_contact'], r['notes'])
            )
            new_id = pid
        except Exception:
            # fallback: insert without id
            db.execute(
                "INSERT INTO patients (name, species, breed, age, owner_name, owner_contact, notes, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (r['name'], r['species'], r['breed'], r['age'], r['owner_name'], r['owner_contact'], r['notes'])
            )
            restored = db.query(
                "SELECT id FROM patients WHERE name=? AND owner_name=? ORDER BY id DESC LIMIT 1",
                (r['name'], r['owner_name'])
            )
            new_id = restored[0]['id'] if restored else None
    db.execute("DELETE FROM recent_deleted WHERE id=?", (record_id,))
    return new_id


## Permanently remove a record from the recent_deleted table
def permanently_delete(record_id):
    if db is None:
        raise RuntimeError('Database not initialized for namtrash')
    db.execute("DELETE FROM recent_deleted WHERE id=?", (record_id,))


## Build and display the UI view for recently deleted patients
def show_namtrash_view(parent):
    for w in parent.winfo_children():
        w.destroy()

    frame = ctk.CTkFrame(parent, fg_color="white")
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(frame, text="Recently Deleted Patients", font=("Arial", 20, "bold")).pack(pady=8)

    list_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    rows = list_deleted()
    if not rows:
        ctk.CTkLabel(list_frame, text="No recently deleted records.").pack(pady=8)
        return

    def make_row_widget(r):
        card = ctk.CTkFrame(list_frame, fg_color="#f8f9fa", corner_radius=6)
        card.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(card, text=f"{r['name']} ({r['species']})", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ctk.CTkLabel(card, text=f"Owner: {r['owner_name']} | Deleted: {r['deleted_at']}", font=("Arial", 11)).grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=10)

        def on_restore(rec_id=r['id']):
            if messagebox.askyesno("Restore", "Restore this patient?"):
                try:
                    restore_deleted(rec_id)
                    messagebox.showinfo("Restored", "Patient restored successfully")
                    show_namtrash_view(parent)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

        def on_delete(rec_id=r['id']):
            if messagebox.askyesno("Permanent Delete", "Permanently delete this record?"):
                permanently_delete(rec_id)
                messagebox.showinfo("Deleted", "Record permanently deleted")
                show_namtrash_view(parent)

        ctk.CTkButton(btn_frame, text="Restore", command=on_restore, fg_color="#2ecc71").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Delete", command=on_delete, fg_color="#e74c3c").pack(side="left", padx=4)

    for r in rows:
        make_row_widget(r)

    return frame
