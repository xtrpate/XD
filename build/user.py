from pathlib import Path
from tkinter import Tk, Canvas, messagebox, PhotoImage, Label, Entry
import subprocess
import sys
import mysql.connector

# --- Get user_id and Fullname from Arguments ---
user_id = None
fullname = "User"
if len(sys.argv) > 2:
    try:
        user_id = int(sys.argv[1])
        fullname = sys.argv[2]
    except ValueError:
        user_id = None
        fullname = "User"
elif len(sys.argv) > 1:
    fullname = sys.argv[1]

# --- Paths ---
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
        user="root",
        password="",
        database="copy_corner_db"
    )


# --- Fetch User Data ---
def get_user_data(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT fullname, username, email, password, contact
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        return None


# --- Update User Data ---
def update_user_data(user_id, new_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET fullname=%s, username=%s, email=%s, password=%s, contact=%s
            WHERE user_id=%s
        """, (
            new_data["fullname"],
            new_data["username"],
            new_data["email"],
            new_data["password"],
            new_data["contact"],
            user_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        messagebox.showinfo("Success", "Profile updated successfully!")
    except Exception as e:
        messagebox.showerror("Database Error", str(e))


# --- Log Out ---
def logout():
    messagebox.showinfo("Logged Out", "Logout successful!")
    subprocess.Popen([sys.executable, "login.py"])
    window.destroy()


# --- Navigation ---
def open_printer():
    subprocess.Popen([sys.executable, "printer.py", str(user_id), fullname])
    window.destroy()


def open_notification_py():
    subprocess.Popen([sys.executable, "Notification.py", str(user_id), fullname])
    window.destroy()


def open_prices_py():
    subprocess.Popen([sys.executable, "Prices.py", str(user_id), fullname])
    window.destroy()


def open_help_py():
    subprocess.Popen([sys.executable, "Help.py", str(user_id), fullname])
    window.destroy()


# --- Clickable Icons ---
def make_icon_clickable(widget, command):
    widget.bind("<Button-1>", lambda e: command())
    widget.bind("<Enter>", lambda e: window.config(cursor="hand2"))
    widget.bind("<Leave>", lambda e: window.config(cursor=""))


# --- Rounded Rectangle ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- Rounded Button Helper ---
def create_rounded_button(canvas, x, y, w, h, text, command=None, fill="#000000", text_color="#FFFFFF"):
    rect = create_rounded_rect(canvas, x, y, x + w, y + h, radius=15, fill=fill, outline="")
    txt = canvas.create_text(x + w / 2, y + h / 2, text=text, fill=text_color, font=("Inter Bold", 14), anchor="center")

    def on_click(event):
        if command:
            command()

    for tag in (rect, txt):
        canvas.tag_bind(tag, "<Button-1>", on_click)
        canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor=""))
    return rect, txt


# --- Main Window ---
window = Tk()
window_width = 859
window_height = 534
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.configure(bg="#FFFFFF")
window.title("Profile")

canvas = Canvas(window, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# --- Borders and Header ---
create_rounded_rect(canvas, 21, 16, 850, 520, radius=0, fill="#FFFFFF", outline="#000000", width=2)
create_rounded_rect(canvas, 21, 15, 850, 103, radius=0, fill="#000000", outline="")
canvas.create_text(120, 60, anchor="center", text="Profile", fill="#FFFFFF", font=("Inter Bold", 34))
canvas.create_rectangle(233.0, 17.0, 234.0, 522.0, fill="#000000", outline="", width=3)


# --- Left Menu ---
def create_rounded_menu_button(canvas, x, y, w, h, text, command=None):
    rect = create_rounded_rect(canvas, x, y, x + w, y + h, radius=12, fill="#FFFFFF", outline="#000000", width=1)
    txt = canvas.create_text(x + 40, y + 10, text=text, anchor="nw", fill="#000000", font=("Inter Bold", 16))

    def on_click(event): command() if command else None

    for tag in (rect, txt):
        canvas.tag_bind(tag, "<Button-1>", on_click)
        canvas.tag_bind(tag, "<Enter>", lambda e: canvas.itemconfig(rect, fill="#E8E8E8"))
        canvas.tag_bind(tag, "<Leave>", lambda e: canvas.itemconfig(rect, fill="#FFFFFF"))
    return rect, txt


create_rounded_menu_button(canvas, 46, 129, 171, 38, "Print Request", open_printer)
create_rounded_menu_button(canvas, 46, 178, 171, 38, "Notifications", open_notification_py)
create_rounded_menu_button(canvas, 46, 227, 171, 38, "Pricelist", open_prices_py)
create_rounded_menu_button(canvas, 46, 276, 171, 38, "Help", open_help_py)
create_rounded_button(canvas, 50, 450, 160, 45, "Log Out", logout)

# --- Profile Picture ---
create_rounded_rect(canvas, 609, 51, 810, 214, radius=20, fill="#FFFFFF", outline="#000000", width=2)
canvas.create_text(682.0, 123.0, anchor="nw", text="Picture", fill="#000000", font=("Inter Bold", 16))

# --- Form Fields ---
user = get_user_data(user_id)
entries = {}
field_positions = {
    "fullname": (271, 146, 500, 174),
    "username": (271, 212, 500, 240),
    "password": (271, 278, 500, 306),
    "email": (269, 341, 500, 369),
    "contact": (269, 407, 500, 435)
}
labels = {
    "fullname": "Full Name",
    "username": "Username",
    "password": "Password",
    "email": "Email",
    "contact": "Contact"
}

for key, label in labels.items():
    lx, ly, x1, y1, x2, y2 = (
        271,
        {"fullname": 121, "username": 187, "password": 250, "email": 316, "contact": 382}[key],
        *field_positions[key]
    )
    canvas.create_text(lx, ly, anchor="nw", text=label, fill="#000000", font=("Inter Bold", 15))
    create_rounded_rect(canvas, x1, y1, x2, y2, radius=10, fill="#FFFAFA", outline="#000000")
    entry = Entry(window, bd=0, bg="#FFFAFA", font=("Inter", 13))
    entry.place(x=x1 + 8, y=y1 + 3, width=x2 - x1 - 16, height=22)
    entry.insert(0, user[key] if user else "")
    entry.config(state="readonly")
    entries[key] = entry


# --- Edit / Save / Cancel Logic ---
def enter_edit_mode():
    for entry in entries.values():
        entry.config(state="normal")
    canvas.itemconfigure(edit_btn_rect, state="hidden")
    canvas.itemconfigure(edit_btn_text, state="hidden")
    canvas.itemconfigure(save_btn_rect, state="normal")
    canvas.itemconfigure(save_btn_text, state="normal")
    canvas.itemconfigure(cancel_btn_rect, state="normal")
    canvas.itemconfigure(cancel_btn_text, state="normal")


def save_changes():
    updated_data = {k: v.get().strip() for k, v in entries.items()}

    # --- Validation checks ---
    for field, value in updated_data.items():
        if not value:
            messagebox.showerror("Error", f"{field.capitalize()} cannot be empty.")
            return

    password = updated_data["password"]
    email = updated_data["email"]

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
    if not email.lower().endswith("@gmail.com"):
        messagebox.showerror("Error", "Email must end with @gmail.com")
        return

    # --- Save if valid ---
    update_user_data(user_id, updated_data)
    global user
    user = get_user_data(user_id)
    for entry in entries.values():
        entry.config(state="readonly")

    # Hide Save + Cancel, Show Edit
    canvas.itemconfigure(save_btn_rect, state="hidden")
    canvas.itemconfigure(save_btn_text, state="hidden")
    canvas.itemconfigure(cancel_btn_rect, state="hidden")
    canvas.itemconfigure(cancel_btn_text, state="hidden")
    canvas.itemconfigure(edit_btn_rect, state="normal")
    canvas.itemconfigure(edit_btn_text, state="normal")


def cancel_edit():
    for key, entry in entries.items():
        entry.delete(0, "end")
        entry.insert(0, user[key] if user else "")
        entry.config(state="readonly")
    canvas.itemconfigure(save_btn_rect, state="hidden")
    canvas.itemconfigure(save_btn_text, state="hidden")
    canvas.itemconfigure(cancel_btn_rect, state="hidden")
    canvas.itemconfigure(cancel_btn_text, state="hidden")
    canvas.itemconfigure(edit_btn_rect, state="normal")
    canvas.itemconfigure(edit_btn_text, state="normal")


# --- Buttons ---
edit_btn_rect = create_rounded_rect(canvas, 271, 468, 351, 496, radius=15, fill="#000000", outline="")
edit_btn_text = canvas.create_text(311, 482, text="Edit", fill="#FFFFFF", font=("Inter Bold", 14))
canvas.tag_bind(edit_btn_rect, "<Button-1>", lambda e: enter_edit_mode())
canvas.tag_bind(edit_btn_text, "<Button-1>", lambda e: enter_edit_mode())

cancel_btn_rect = create_rounded_rect(canvas, 271, 468, 371, 496, radius=15, fill="#FFFFFF", outline="#000000")
cancel_btn_text = canvas.create_text(321, 482, text="Cancel", fill="#000000", font=("Inter Bold", 14))
canvas.tag_bind(cancel_btn_rect, "<Button-1>", lambda e: cancel_edit())
canvas.tag_bind(cancel_btn_text, "<Button-1>", lambda e: cancel_edit())
canvas.itemconfigure(cancel_btn_rect, state="hidden")
canvas.itemconfigure(cancel_btn_text, state="hidden")

save_btn_rect = create_rounded_rect(canvas, 385, 468, 465, 496, radius=15, fill="#000000", outline="")
save_btn_text = canvas.create_text(425, 482, text="Save", fill="#FFFFFF", font=("Inter Bold", 14))
canvas.tag_bind(save_btn_rect, "<Button-1>", lambda e: save_changes())
canvas.tag_bind(save_btn_text, "<Button-1>", lambda e: save_changes())
canvas.itemconfigure(save_btn_rect, state="hidden")
canvas.itemconfigure(save_btn_text, state="hidden")

# --- Icons ---
icon_edit = PhotoImage(file=relative_to_assets("image_13.png"))
icon_bell = PhotoImage(file=relative_to_assets("image_14.png"))
icon_sheet = PhotoImage(file=relative_to_assets("image_15.png"))
icon_help = PhotoImage(file=relative_to_assets("image_16.png"))

lbl_edit = Label(window, image=icon_edit, bg="#FFFFFF", bd=0)
lbl_bell = Label(window, image=icon_bell, bg="#FFFFFF", bd=0)
lbl_sheet = Label(window, image=icon_sheet, bg="#FFFFFF", bd=0)
lbl_help = Label(window, image=icon_help, bg="#FFFFFF", bd=0)

lbl_edit.place(x=63.0, y=148.0, anchor="center")
lbl_bell.place(x=63.0, y=198.0, anchor="center")
lbl_sheet.place(x=63.0, y=248.0, anchor="center")
lbl_help.place(x=63.0, y=298.0, anchor="center")

make_icon_clickable(lbl_edit, open_printer)
make_icon_clickable(lbl_bell, open_notification_py)
make_icon_clickable(lbl_sheet, open_prices_py)
make_icon_clickable(lbl_help, open_help_py)

window.resizable(False, False)
window.mainloop()
