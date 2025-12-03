"""
Login Module - Simple modal login window for the Vet Clinic app.
"""
import customtkinter as ctk

def get_credentials():
    """Return hardcoded user credentials"""
    return {
        "admin": "vet2106",
        "user": "password"
    }

def show_login():
    """Display login window and return True if login successful"""
    
    ctk.set_appearance_mode("light")
    login_window = ctk.CTkToplevel()
    login_window.title("Vet Clinic - Login")
    login_window.geometry("450x420")
    login_window.resizable(False, False)
    
    # Center window on screen
    login_window.update_idletasks()
    screen_width = login_window.winfo_screenwidth()
    screen_height = login_window.winfo_screenheight()
    x = (screen_width - 450) // 2
    y = (screen_height - 420) // 2
    login_window.geometry(f"+{x}+{y}")
    
    # Login result
    login_result = [False]
    
    # Main frame
    main_frame = ctk.CTkFrame(login_window, fg_color="white")
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Header
    header = ctk.CTkFrame(main_frame, fg_color="#2c3e50", corner_radius=0, height=100)
    header.pack(fill="x", padx=0, pady=0)
    header.pack_propagate(False)
    
    ctk.CTkLabel(header, text="Veterinary Clinic System", 
                font=("Arial", 24, "bold"),
                text_color="white").pack(pady=25)
    
    # Login form
    form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    form_frame.pack(fill="both", expand=False, padx=40, pady=20)
    
    # Username
    ctk.CTkLabel(form_frame, text="Username",
                font=("Arial", 14, "bold"),
                text_color="#2c3e50").pack(anchor="w", pady=(0, 5))
    
    username_entry = ctk.CTkEntry(form_frame,
                                  placeholder_text="Enter username",
                                  height=40,
                                  font=("Arial", 13),
                                  border_width=2,
                                  corner_radius=8)
    username_entry.pack(fill="x", pady=(0, 20))
    
    # Password
    ctk.CTkLabel(form_frame, text="Password",
                font=("Arial", 14, "bold"),
                text_color="#2c3e50").pack(anchor="w", pady=(0, 5))
    
    password_entry = ctk.CTkEntry(form_frame,
                                  placeholder_text="Enter password",
                                  height=40,
                                  font=("Arial", 13),
                                  border_width=2,
                                  corner_radius=8,
                                  show="•")
    password_entry.pack(fill="x", pady=(0, 20))
    
    # Error label
    error_label = ctk.CTkLabel(form_frame, text="",
                              font=("Arial", 12),
                              text_color="#e74c3c")
    error_label.pack(anchor="w", pady=(0, 10))
    
    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        
        if not username or not password:
            error_label.configure(text=" Please enter both username and password")
            return
        
        credentials = get_credentials()
        
        if username in credentials and credentials[username] == password:
            login_result[0] = True
            login_window.destroy()
        else:
            error_label.configure(text=" Invalid username or password")
            password_entry.delete(0, "end")
    
    def on_enter(event):
        login()
    
    password_entry.bind("<Return>", on_enter)
    
    # Buttons
    button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    button_frame.pack(fill="x", pady=(15, 0))
    
    ctk.CTkButton(button_frame, text="LOGIN",
                command=login,
                fg_color="#2ecc71",
                hover_color="#27ae60",
                font=("Arial", 16, "bold"),
                height=100,
                corner_radius=8).pack(fill="x", padx=0, pady=(0,5))
    

    
    # Make window modal and wait
    login_window.grab_set()
    login_window.wait_window()
    
    return login_result[0]

if __name__ == "__main__":
    if show_login():
        print("Login successful!")
    else:
        print("Login cancelled")
