import customtkinter as ctk
import json
from pathlib import Path
import tkinter as tk

CREDENTIALS_FILE = Path(__file__).with_name('credentials.json')

def load_credentials():
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"admin": "admin", "user": "password"}

def show_login():
    """Display a modern, aesthetic login window"""
    
    ctk.set_appearance_mode("light")
    
    root = tk.Tk()
    root.withdraw()
    
    login_window = ctk.CTkToplevel(root)
    login_window.title("Vet Clinic - Login")
    login_window.geometry("520x680")
    login_window.resizable(False, False)
    login_window.configure(fg_color="#667eea")
    
    login_window.update_idletasks()
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width - 520) // 2
    y = (screen_height - 680) // 2
    login_window.geometry(f"+{x}+{y}")
    
    login_result = [False]
    password_visible = [False]
    
    gradient_frame = ctk.CTkFrame(login_window, fg_color="#667eea", corner_radius=0)
    gradient_frame.pack(fill="both", expand=True)
    
    top_decor = ctk.CTkFrame(gradient_frame, fg_color="#764ba2", corner_radius=0, height=200)
    top_decor.pack(fill="x")
    top_decor.pack_propagate(False)
    
    paw_label = ctk.CTkLabel(top_decor, 
                             text="{ }",
                             font=("Arial", 48),
                             text_color="#a78bfa")
    paw_label.place(x=30, y=20)
    
    paw_label2 = ctk.CTkLabel(top_decor, 
                              text="{ }",
                              font=("Arial", 36),
                              text_color="#9879d8")
    paw_label2.place(x=420, y=80)
    
    welcome_frame = ctk.CTkFrame(top_decor, fg_color="transparent")
    welcome_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    icon_label = ctk.CTkLabel(welcome_frame,
                              text="*",
                              font=("Arial", 60),
                              text_color="white")
    icon_label.pack()
    
    title_label = ctk.CTkLabel(welcome_frame,
                               text="VetCare Clinic",
                               font=("Arial", 28, "bold"),
                               text_color="white")
    title_label.pack(pady=(5, 0))
    
    subtitle_label = ctk.CTkLabel(welcome_frame,
                                  text="Your Pet's Health, Our Priority",
                                  font=("Arial", 12),
                                  text_color="#e8e0f0")
    subtitle_label.pack(pady=(2, 0))
    
    card_frame = ctk.CTkFrame(gradient_frame, 
                              fg_color="white", 
                              corner_radius=25,
                              border_width=0)
    card_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
    
    form_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
    form_frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    login_title = ctk.CTkLabel(form_frame,
                               text="Welcome Back!",
                               font=("Arial", 24, "bold"),
                               text_color="#2d3748")
    login_title.pack(anchor="w", pady=(0, 5))
    
    login_subtitle = ctk.CTkLabel(form_frame,
                                  text="Sign in to access your account",
                                  font=("Arial", 13),
                                  text_color="#718096")
    login_subtitle.pack(anchor="w", pady=(0, 30))
    
    username_label = ctk.CTkLabel(form_frame,
                                  text="Username",
                                  font=("Arial", 13, "bold"),
                                  text_color="#4a5568")
    username_label.pack(anchor="w", pady=(0, 8))
    
    username_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    username_frame.pack(fill="x", pady=(0, 20))
    
    username_entry = ctk.CTkEntry(username_frame,
                                  placeholder_text="Enter your username",
                                  height=50,
                                  font=("Arial", 14),
                                  border_width=2,
                                  border_color="#e2e8f0",
                                  corner_radius=12,
                                  fg_color="#f7fafc",
                                  text_color="#2d3748")
    username_entry.pack(fill="x")
    
    password_label = ctk.CTkLabel(form_frame,
                                  text="Password",
                                  font=("Arial", 13, "bold"),
                                  text_color="#4a5568")
    password_label.pack(anchor="w", pady=(0, 8))
    
    password_container = ctk.CTkFrame(form_frame, fg_color="transparent")
    password_container.pack(fill="x", pady=(0, 15))
    
    password_entry = ctk.CTkEntry(password_container,
                                  placeholder_text="Enter your password",
                                  height=50,
                                  font=("Arial", 14),
                                  border_width=2,
                                  border_color="#e2e8f0",
                                  corner_radius=12,
                                  fg_color="#f7fafc",
                                  text_color="#2d3748",
                                  show="*")
    password_entry.pack(side="left", fill="x", expand=True)
    
    def toggle_password():
        if password_visible[0]:
            password_entry.configure(show="*")
            toggle_btn.configure(text="Show")
            password_visible[0] = False
        else:
            password_entry.configure(show="")
            toggle_btn.configure(text="Hide")
            password_visible[0] = True
    
    toggle_btn = ctk.CTkButton(password_container,
                               text="Show",
                               width=60,
                               height=50,
                               font=("Arial", 11),
                               fg_color="#edf2f7",
                               text_color="#4a5568",
                               hover_color="#e2e8f0",
                               corner_radius=12,
                               command=toggle_password)
    toggle_btn.pack(side="right", padx=(10, 0))
    
    error_label = ctk.CTkLabel(form_frame,
                               text="",
                               font=("Arial", 12),
                               text_color="#e53e3e")
    error_label.pack(anchor="w", pady=(0, 10))
    
    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        
        if not username or not password:
            error_label.configure(text="Please enter both username and password")
            return
        
        credentials = load_credentials()
        
        if username in credentials and credentials[username] == password:
            login_result[0] = True
            login_window.destroy()
            root.destroy()
        else:
            error_label.configure(text="Invalid username or password")
            password_entry.delete(0, "end")
            password_entry.focus()
    
    def on_enter(event):
        login()
    
    password_entry.bind("<Return>", on_enter)
    username_entry.bind("<Return>", lambda e: password_entry.focus())
    
    login_button = ctk.CTkButton(form_frame,
                                 text="Sign In",
                                 command=login,
                                 height=50,
                                 font=("Arial", 16, "bold"),
                                 fg_color="#667eea",
                                 hover_color="#5a67d8",
                                 corner_radius=12)
    login_button.pack(fill="x", pady=(15, 20))
    
    divider_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    divider_frame.pack(fill="x", pady=(0, 15))
    
    line1 = ctk.CTkFrame(divider_frame, fg_color="#e2e8f0", height=1)
    line1.pack(side="left", fill="x", expand=True)
    
    or_label = ctk.CTkLabel(divider_frame,
                            text="  Clinic System  ",
                            font=("Arial", 11),
                            text_color="#a0aec0",
                            fg_color="white")
    or_label.pack(side="left")
    
    line2 = ctk.CTkFrame(divider_frame, fg_color="#e2e8f0", height=1)
    line2.pack(side="left", fill="x", expand=True)
    
    hint_frame = ctk.CTkFrame(form_frame, fg_color="#f0fff4", corner_radius=10)
    hint_frame.pack(fill="x", pady=(10, 0))
    
    hint_label = ctk.CTkLabel(hint_frame,
                              text="Hint: Default credentials are admin/admin",
                              font=("Arial", 11),
                              text_color="#38a169")
    hint_label.pack(pady=12)
    
    footer_label = ctk.CTkLabel(form_frame,
                                text="Vet Clinic Management System v1.0",
                                font=("Arial", 10),
                                text_color="#a0aec0")
    footer_label.pack(side="bottom", pady=(20, 0))
    
    def on_close():
        login_result[0] = False
        login_window.destroy()
        root.destroy()
    
    login_window.protocol("WM_DELETE_WINDOW", on_close)
    
    login_window.grab_set()
    username_entry.focus()
    
    root.wait_window(login_window)
    
    return login_result[0]

if __name__ == "__main__":
    if show_login():
        print("Login successful!")
    else:
        print("Login cancelled")
