"""
CLASS : 3
Medicine Module - Inventory and supplier management for the Vet Clinic.

Provides:
- Create, update, delete medicines in clinic inventory
- Track stock, unit price, dosage form (tablet, injection, syrup, etc.) and intended use
- Store supplier name and contact for each medicine
- Load sample medicines for testing/demo
- UI: show_medicine_view(parent) to manage medicines from the app

Notes:
- Expects global `db` (Database) and `app` to be assigned by main application before use.
- Uses sqlite row/dict results via db.query / db.execute.
"""

import customtkinter as ctk
from tkinter import messagebox
from abc import ABC, abstractmethod

app = None
db = None

UI_SCALE = 1.12

## Scaled font helper to apply module UI scaling
def scaled_font(size, weight=None):
    sz = max(8, int(size * UI_SCALE))
    if weight:
        return ("Arial", sz, weight)
    return ("Arial", sz)

## Abstract base representing a medicine record
class MedicineBase(ABC):
    def __init__(self, name: str, stock: int = 0, price: float = 0.0, supplier_name: str = None, supplier_contact: str = None):
        self.name = name.strip() if name else ''
        self.stock = int(stock or 0)
        self.price = float(price or 0.0)
        self.supplier_name = supplier_name
        self.supplier_contact = supplier_contact

    @abstractmethod
    ## Persist the medicine (insert or update)
    def save(self):
        raise NotImplementedError()

    @abstractmethod
    ## Delete the medicine record
    def delete(self):
        raise NotImplementedError()


## Concrete medicine model with DB persistence
class Medicine(MedicineBase):
    ## Save medicine; update if exists or insert new
    def save(self, med_id=None):
        if not self.name:
            raise ValueError('Medicine name required')
        
        # If med_id is provided, update by ID (editing existing medicine)
        if med_id is not None:
            existing = db.query("SELECT * FROM medicines WHERE id = ?", (med_id,))
            if existing:
                # update by id
                db.execute("UPDATE medicines SET name=?, stock=?, price=?, form=?, use=?, supplier_name=?, supplier_contact=? WHERE id=?",
                           (self.name, self.stock, self.price, getattr(self, 'form', None), getattr(self, 'use', None), self.supplier_name, self.supplier_contact, med_id))
            else:
                raise ValueError('Medicine not found')
        else:
            # New medicine or update by name
            existing = db.query("SELECT * FROM medicines WHERE name = ?", (self.name,))
            if existing:
                # update by name
                db.execute("UPDATE medicines SET stock=?, price=?, form=?, use=?, supplier_name=?, supplier_contact=? WHERE name=?",
                           (self.stock, self.price, getattr(self, 'form', None), getattr(self, 'use', None), self.supplier_name, self.supplier_contact, self.name))
            else:
                # insert new
                db.execute("INSERT INTO medicines (name, stock, price, form, use, supplier_name, supplier_contact) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (self.name, self.stock, self.price, getattr(self, 'form', None), getattr(self, 'use', None), self.supplier_name, self.supplier_contact))

    ## Delete medicine by name
    def delete(self):
        db.execute("DELETE FROM medicines WHERE name = ?", (self.name,))

    @staticmethod
    @staticmethod
    ## Return all medicines ordered by name
    def list_all():
        return db.query("SELECT * FROM medicines ORDER BY name")


## Simple supplier data container
class Supplier:
    def __init__(self, name: str = None, contact: str = None):
        self.name = name
        self.contact = contact


## Build and display the medicine management UI
def show_medicine_view(parent):
    for w in parent.winfo_children():
        w.destroy()

    ctk.CTkLabel(parent, text="Medicine Inventory",
                font=scaled_font(32, "bold"),
                text_color="#2c3e50").pack(pady=20)

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20)

    left = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
    left.pack(side="left", fill="both", expand=True, padx=(0,10))

    right = ctk.CTkFrame(container, fg_color="white", corner_radius=10, width=int(420 * UI_SCALE))
    right.pack(side="right", fill="both", padx=(10,0))
    right.pack_propagate(False)

    search_frame = ctk.CTkFrame(left, fg_color="transparent")
    search_frame.pack(fill="x", padx=10, pady=10)

    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search medicines...", width=int(300 * UI_SCALE))
    search_entry.pack(side="left", padx=5)

    med_container = ctk.CTkScrollableFrame(left, fg_color="transparent")
    med_container.pack(fill="both", expand=True, padx=10, pady=10)

    selected_card = [None]
    selected_med_id = [None]

    ## Load and render medicine cards matching optional query
    def load_meds(query=""):
        for w in med_container.winfo_children():
            w.destroy()

        sql = "SELECT * FROM medicines"
        params = []
        if query:
            sql += " WHERE name LIKE ? OR supplier_name LIKE ?"
            params.extend([f"%{query}%", f"%{query}%"])
        sql += " ORDER BY name"

        meds = db.query(sql, tuple(params))
        if not meds:
            ctk.CTkLabel(med_container, text="No medicines registered.", text_color="gray", font=scaled_font(12)).pack(pady=20)
            return

        for m in meds:
            card = ctk.CTkFrame(med_container, fg_color="#f8f9fa", corner_radius=8, border_width=1, border_color="#e0e0e0")
            card.pack(fill="x", padx=10, pady=6)

            ctk.CTkLabel(card, text=f"{m['name']}", font=scaled_font(13, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(8,2))
            ctk.CTkLabel(card, text=f"Stock: {m['stock']} | ₱{float(m['price']):,.2f}", font=scaled_font(11), anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))

            ## UI handler: populate form with selected medicine details
            def on_click(e=None, mid=m['id'], card_ref=card):
                try:
                    med = db.query("SELECT * FROM medicines WHERE id = ?", (mid,))[0]
                except Exception as e:
                    print(f"Error querying medicine: {e}")
                    return
                try:
                    if selected_card[0] and selected_card[0] != card_ref:
                        selected_card[0].configure(fg_color="#f8f9fa")
                except Exception:
                    pass
                try:
                    card_ref.configure(fg_color="#e8f8f5")
                except Exception:
                    pass
                selected_card[0] = card_ref
                selected_med_id[0] = med['id']
                name_entry.delete(0, 'end'); name_entry.insert(0, med['name'])
                stock_entry.delete(0, 'end'); stock_entry.insert(0, str(med['stock']))
                price_entry.delete(0, 'end'); price_entry.insert(0, f"{float(med['price']):.2f}")
                uses_entry.delete(0, 'end'); uses_entry.insert(0, med['use'] or "")
                form_combo.set(med['form'] or "Tablet")
                supplier_entry.delete(0, 'end'); supplier_entry.insert(0, med['supplier_name'] or "")
                supplier_contact_entry.delete(0, 'end'); supplier_contact_entry.insert(0, med['supplier_contact'] or "")
                print(f"Loaded medicine: {med['name']}, Use: {med['use']}, Supplier: {med['supplier_name']}, Contact: {med['supplier_contact']}")

            card.bind('<Button-1>', on_click)
            for child in card.winfo_children():
                child.bind('<Button-1>', on_click)

    ## Refresh the medicine list using current search entry
    def refresh():
        load_meds(search_entry.get())

    ctk.CTkButton(search_frame, text="Search", width=int(80 * UI_SCALE), font=scaled_font(12), command=lambda: load_meds(search_entry.get())).pack(side="left", padx=5)
    ctk.CTkButton(search_frame, text="Clear", width=int(80 * UI_SCALE), font=scaled_font(12), command=lambda: [search_entry.delete(0, 'end'), load_meds()]).pack(side="left")
    ctk.CTkButton(search_frame, text="Refresh", width=int(80 * UI_SCALE), font=scaled_font(12), command=refresh).pack(side="left", padx=5)

    # Right form
    ctk.CTkLabel(right, text="Medicine Details", font=scaled_font(20, "bold")).pack(pady=15)

    form = ctk.CTkFrame(right, fg_color="transparent")
    form.pack(fill="both", expand=True, padx=10, pady=10)

    ctk.CTkLabel(form, text="Name:", font=scaled_font(12)).pack(anchor='w')
    name_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    name_entry.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Uses:", font=scaled_font(12)).pack(anchor='w')
    uses_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    uses_entry.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Stock:", font=scaled_font(12)).pack(anchor='w')
    stock_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    stock_entry.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Price (₱):", font=scaled_font(12)).pack(anchor='w')
    price_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    price_entry.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Form:", font=scaled_font(12)).pack(anchor='w')
    form_combo = ctk.CTkComboBox(form, values=["Tablet", "Injection", "Syrup", "Cream", "Ointment", "Drops", "Suppository", "Other"], width=int(200 * UI_SCALE))
    form_combo.set("Tablet")
    form_combo.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Supplier Name:", font=scaled_font(12)).pack(anchor='w')
    supplier_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    supplier_entry.pack(fill='x', pady=6)

    ctk.CTkLabel(form, text="Supplier Contact:", font=scaled_font(12)).pack(anchor='w')
    supplier_contact_entry = ctk.CTkEntry(form, width=int(280 * UI_SCALE))
    supplier_contact_entry.pack(fill='x', pady=6)

    ## Insert a set of sample medicines into the DB (duplicates skipped)
    def load_sample_meds():
        samples = [
            ("Amoxicillin", 50, 150.0, "Tablet", "MediSuppliers", "09171234567"),
            ("Carprofen", 30, 200.0, "Tablet", "PetPharm", "09171234568"),
            ("Enrofloxacin", 40, 250.0, "Syrup", "VetMeds", "09171234569"),
            ("Ketamine", 10, 500.0, "Injection", "MediSuppliers", "09171234567"),
            ("Dexamethasone", 25, 120.0, "Injection", "PharmaPlus", "09171234570"),
        ]
        inserted = 0
        for name, stock, price, form_val, sname, scontact in samples:
            existing = db.query("SELECT * FROM medicines WHERE name = ?", (name,))
            if not existing:
                try:
                    db.execute("INSERT INTO medicines (name, stock, price, form, use, supplier_name, supplier_contact) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (name, stock, price, form_val, None, sname, scontact))
                    inserted += 1
                except Exception:
                    pass
        messagebox.showinfo('Sample Load', f'Inserted {inserted} sample medicines (duplicates skipped).')
        load_meds()

    ## Clear the right-hand form inputs and selection
    def clear_form():
        selected_med_id[0] = None
        try:
            if selected_card[0]:
                selected_card[0].configure(fg_color="#f8f9fa")
                selected_card[0] = None
        except Exception:
            pass
        for e in [name_entry, stock_entry, price_entry, uses_entry, supplier_entry, supplier_contact_entry]:
            e.delete(0, 'end')
        form_combo.set("Tablet")

    ## Read form inputs and save medicine via the `Medicine` model
    def save_med():
        name = name_entry.get().strip()
        if not name:
            messagebox.showerror('Error', 'Medicine name required')
            return
        try:
            stock = int(stock_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror('Error', 'Invalid stock value')
            return
        try:
            price = float(price_entry.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror('Error', 'Invalid price value')
            return
        supplier = supplier_entry.get().strip() or None
        supplier_contact = supplier_contact_entry.get().strip() or None
        form_val = form_combo.get() or None
        use = uses_entry.get().strip() or None

        med = Medicine(name, stock, price, supplier, supplier_contact)
        med.form = form_val
        med.use = use
        try:
            med_id_to_save = selected_med_id[0]
            med.save(med_id_to_save)
            messagebox.showinfo('Success', f"Medicine '{name}' saved")
            clear_form()
            load_meds(search_entry.get())
        except Exception as e:
            messagebox.showerror('Error', f"Save failed: {str(e)}")

    ## Delete the currently selected medicine (by id)
    def delete_med():
        if not selected_med_id[0]:
            return
        if messagebox.askyesno('Confirm', 'Delete this medicine from inventory?'):
            med = db.query('SELECT * FROM medicines WHERE id = ?', (selected_med_id[0],))
            if med:
                db.execute('DELETE FROM medicines WHERE id = ?', (selected_med_id[0],))
            clear_form()
            load_meds()

    btn_frame = ctk.CTkFrame(form, fg_color='transparent')
    btn_frame.pack(fill='x', pady=10)

    ctk.CTkButton(btn_frame, text='Save', command=save_med, fg_color='#2ecc71', font=scaled_font(13)).pack(side='left', expand=True, fill='x', padx=4)
    ctk.CTkButton(btn_frame, text='New', command=clear_form, fg_color='#3498db', font=scaled_font(13)).pack(side='left', expand=True, fill='x', padx=4)
    ctk.CTkButton(btn_frame, text='Delete', command=delete_med, fg_color='#e74c3c', font=scaled_font(13)).pack(side='left', expand=True, fill='x', padx=4)
    ctk.CTkButton(btn_frame, text='Load Sample Medicines', command=load_sample_meds, fg_color='#9b59b6', font=scaled_font(12)).pack(side='left', expand=True, fill='x', padx=4)

    load_meds()


## Backwards-compatible alias for showing the medicine view
def medicine(parent):
    return show_medicine_view(parent)
