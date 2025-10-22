from pathlib import Path
from tkinter import Tk, Canvas, Entry, messagebox
import subprocess
import sys
import mysql.connector

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(
    r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame0"
)

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

# --- DB Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",      # adjust if your MySQL user is different
        password="",      # put your MySQL password if set
        database="copy_corner_db"
    )

# --- Rounded rectangle function ---
def round_rectangle(canvas, x1, y1, x2, y2, r=20, **kwargs):
    points = [
        x1+r, y1,
        x2-r, y1,
        x2, y1,
        x2, y1+r,
        x2, y2-r,
        x2, y2,
        x2-r, y2,
        x1+r, y2,
        x1, y2,
        x1, y2-r,
        x1, y1+r,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# --- Toggle password visibility ---
def toggle_password(entry, icon_item):
    if entry.cget("show") == "":
        entry.config(show="*")
        canvas.itemconfig(icon_item, text="🙈")
    else:
        entry.config(show="")
        canvas.itemconfig(icon_item, text="👁")

# --- Register user (password validation + DB insert) ---
def register_user():
    fullname = fullname_entry.get().strip()
    username = username_entry.get().strip()
    contact = contact_entry.get().strip()
    email = email_entry.get().strip()
    password = password_entry.get()
    confirm = confirm_entry.get()

    # --- Validation checks ---
    if len(password) < 8:
        messagebox.showerror("Error", "Password must be at least 8 characters long.")
        return
    if not any(c.isupper() for c in password):
        messagebox.showerror("Error", "Password must contain at least one uppercase letter.")
        return
    if not any(c.islower() for c in password):
        messagebox.showerror("Error", "Password must contain at least one lowercase letter.")
        return
    if not any(c.isdigit() for c in password):
        messagebox.showerror("Error", "Password must contain at least one digit.")
        return
    if password != confirm:
        messagebox.showerror("Error", "Passwords do not match.")
        return
    if not email.lower().endswith("@gmail.com"):
        messagebox.showerror("Error", "Email must end with @gmail.com")
        return

    # --- Insert into DB ---
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # check duplicates
        cursor.execute("SELECT 1 FROM users WHERE fullname=%s OR username=%s OR email=%s",
                       (fullname, username, email))
        if cursor.fetchone():
            messagebox.showerror("Error", "User with this fullname, username, or email already exists!")
            cursor.close()
            conn.close()
            return

        # insert new user (now includes contact)
        cursor.execute(
            "INSERT INTO users (fullname, username, contact, email, password) VALUES (%s, %s, %s, %s, %s)",
            (fullname, username, contact, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("Success", "Account created successfully!")

        fullname_entry.delete(0, 'end')
        username_entry.delete(0, 'end')
        contact_entry.delete(0, 'end')
        email_entry.delete(0, 'end')
        password_entry.delete(0, 'end')
        confirm_entry.delete(0, 'end')

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# --- Open login.py ---
def open_login():
    try:
        subprocess.Popen([sys.executable, "login.py"])
        window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Could not open login.py\n{e}")

# --- Main Window ---
window = Tk()
# --- Center the Window ---
window_width = 859
window_height = 604
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

window.configure(bg="#FFFFFF")
window.title("Create Account")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=604,
    width=851,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)
canvas.place(x=0, y=0)

# --- Rounded shapes ---
round_rectangle(canvas, 10.0, 15.0, 839.0, 589.0, r=0, fill="#FFFFFF", outline="#000000", width=3)
round_rectangle(canvas, 10.0, 15.0, 839.0, 100.0, r=0, fill="#000000", outline="")
round_rectangle(canvas, 242.0, 32.0, 601.0, 575.0, r=25, fill="#FFFFFF", outline="#000000", width=2)

# --- Texts ---
canvas.create_text(283.0, 61.0, anchor="nw", text="CREATE ACCOUNT", fill="#000000", font=("Inter Bold", 32 * -1))
canvas.create_text(346.0, 100.0, anchor="nw", text="Fill in your details to register", fill="#000000", font=("Inter", 13 * -1))

# --- Input field boxes (Contact moved up) ---
round_rectangle(canvas, 367.0, 141.0, 545.0, 183.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # fullname
round_rectangle(canvas, 367.0, 199.0, 545.0, 241.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # username
round_rectangle(canvas, 367.0, 256.0, 545.0, 298.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # contact
round_rectangle(canvas, 367.0, 313.0, 545.0, 355.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # email
round_rectangle(canvas, 367.0, 370.0, 545.0, 412.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # password
round_rectangle(canvas, 367.0, 427.0, 545.0, 469.0, r=15, fill="#FFFFFF", outline="#000000", width=1)  # confirm
signup_box = round_rectangle(canvas, 367.0, 484.0, 545.0, 526.0, r=20, fill="#000000", outline="")

# --- Labels ---
canvas.create_text(299.0, 154.0, anchor="nw", text="Full Name", fill="#000000", font=("Inter", 13 * -1))
canvas.create_text(297.0, 212.0, anchor="nw", text="Username", fill="#000000", font=("Inter", 13 * -1))
canvas.create_text(295.0, 269.0, anchor="nw", text="Contact No.", fill="#000000", font=("Inter", 13 * -1))
canvas.create_text(322.0, 326.0, anchor="nw", text="Email", fill="#000000", font=("Inter", 13 * -1))
canvas.create_text(295.0, 384.0, anchor="nw", text="Password", fill="#000000", font=("Inter", 13 * -1))
canvas.create_text(254.0, 442.0, anchor="nw", text="Confirm Password", fill="#000000", font=("Inter", 13 * -1))

# --- Sign Up text ---
signup_text = canvas.create_text(426.0, 498.0, anchor="nw", text="Sign Up", fill="#FFFFFF", font=("Inter", 16 * -1))

# --- Already account / login ---
canvas.create_text(345.0, 536.0, anchor="nw", text="Already have account?", fill="#000000", font=("Inter", 14 * -1))
login_text = canvas.create_text(500.0, 534.0, anchor="nw", text="Login", fill="blue", font=("Inter Black", 16 * -1))

# --- Entry fields (Contact moved up) ---
fullname_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
username_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
contact_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
email_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
password_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12), show="*")
confirm_entry = Entry(window, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12), show="*")

canvas.create_window(456, 162, window=fullname_entry, width=160, height=25)
canvas.create_window(456, 220, window=username_entry, width=160, height=25)
canvas.create_window(456, 277, window=contact_entry, width=160, height=25)
canvas.create_window(456, 334, window=email_entry, width=160, height=25)
canvas.create_window(456, 391, window=password_entry, width=140, height=25)
canvas.create_window(456, 448, window=confirm_entry, width=140, height=25)

# --- Eye icons ---
eye_icon_pw = canvas.create_text(525, 382, anchor="nw", text="👁", fill="black", font=("Arial", 12))
canvas.tag_bind(eye_icon_pw, "<Button-1>", lambda e: toggle_password(password_entry, eye_icon_pw))
canvas.tag_bind(eye_icon_pw, "<Enter>", lambda e: window.config(cursor="hand2"))
canvas.tag_bind(eye_icon_pw, "<Leave>", lambda e: window.config(cursor=""))

eye_icon_confirm = canvas.create_text(525, 439, anchor="nw", text="👁", fill="black", font=("Arial", 12))
canvas.tag_bind(eye_icon_confirm, "<Button-1>", lambda e: toggle_password(confirm_entry, eye_icon_confirm))
canvas.tag_bind(eye_icon_confirm, "<Enter>", lambda e: window.config(cursor="hand2"))
canvas.tag_bind(eye_icon_confirm, "<Leave>", lambda e: window.config(cursor=""))

# --- Make Sign Up box + text clickable ---
def on_signup_click(e): register_user()
def on_hover_signup(e): window.config(cursor="hand2")
def on_leave_signup(e): window.config(cursor="")

canvas.tag_bind(signup_box, "<Button-1>", on_signup_click)
canvas.tag_bind(signup_text, "<Button-1>", on_signup_click)
canvas.tag_bind(signup_box, "<Enter>", on_hover_signup)
canvas.tag_bind(signup_text, "<Enter>", on_hover_signup)
canvas.tag_bind(signup_box, "<Leave>", on_leave_signup)
canvas.tag_bind(signup_text, "<Leave>", on_leave_signup)

# --- Make Login clickable ---
canvas.tag_bind(login_text, "<Button-1>", lambda e: open_login())
canvas.tag_bind(login_text, "<Enter>", lambda e: window.config(cursor="hand2"))
canvas.tag_bind(login_text, "<Leave>", lambda e: window.config(cursor=""))

# --- End ---
window.resizable(False, False)
window.mainloop()
