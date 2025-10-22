import sys
import subprocess
from pathlib import Path
from tkinter import (
    Tk, Canvas, Entry, Text, messagebox, filedialog,
    Checkbutton, IntVar, DISABLED, NORMAL, StringVar, OptionMenu, PhotoImage, Label, Button
)
import os
from datetime import datetime
import mysql.connector


# --- Database Connection Function ---
def create_db_connection():
    """Creates and returns a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="copy_corner_db"
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
        return None

def update_request_status(job_id, new_status):
    """
    Updates the status of a print job in the database.
    Example: update_request_status(5, "Declined") or update_request_status(5, "Approved")
    """
    conn = None
    try:
        conn = create_db_connection()
        if conn is None:
            return

        cursor = conn.cursor()
        sql_query = "UPDATE print_jobs SET status = %s WHERE id = %s"
        cursor.execute(sql_query, (new_status, job_id))
        conn.commit()

        messagebox.showinfo("Status Updated", f"Request #{job_id} marked as {new_status}.")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to update status: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# --- NEW: Function to load existing requests for the logged-in user ---
def load_user_requests():
    """Fetches and displays the user's most recent requests from the database."""
    if not user_id:
        return  # Don't load anything if there's no user logged in

    conn = None
    try:
        conn = create_db_connection()
        if not conn:
            return

        cursor = conn.cursor(dictionary=True)
        # Select the most recent jobs for this specific user
        sql_query = """
        SELECT pages, status, created_at FROM print_jobs 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5 
        """
        cursor.execute(sql_query, (user_id,))
        requests = cursor.fetchall()

        # Display the requests, with the oldest one at the top
        for request in reversed(requests):
            filename = f"{request['pages']} page(s)"  # Use a descriptive placeholder
            date_str = request['created_at'].strftime("%B %d, %Y")
            status = request['status']
            add_request_status(filename, date_str, status)

    except mysql.connector.Error as err:
        print(f"Could not load request history: {err}")  # Log error to console
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# --- Rounded Rectangle Function ---
def round_rectangle(canvas, x1, y1, x2, y2, r=15, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- MODIFIED: Navigation Functions to pass user info ---
def open_user_py():
    if user_id:
        subprocess.Popen([sys.executable, "user.py", str(user_id), fullname])
        window.destroy()


def open_notification_py():
    if user_id:
        subprocess.Popen([sys.executable, "Notification.py", str(user_id), fullname])
        window.destroy()


def open_prices_py():
    if user_id:
        subprocess.Popen([sys.executable, "Prices.py", "printer.py", str(user_id), fullname])
        window.destroy()


# Inside printer.py

# Assuming you have user_id and fullname variables already
def open_help_py():
    if user_id is None: # Add check
        messagebox.showerror("Error", "User ID not found.")
        return
    # Pass user_id and fullname to help.py
    subprocess.Popen([sys.executable, "help.py", str(user_id), fullname])
    window.destroy()

# Similar function for opening history.py
def open_history_py():
    if user_id is None:
        messagebox.showerror("Error", "User ID not found.")
        return
    # Pass user_id and fullname to history.py
    subprocess.Popen([sys.executable, "history.py", str(user_id), fullname])
    window.destroy()


def make_icon_clickable(widget, command):
    widget.bind("<Button-1>", lambda e: command())
    widget.bind("<Enter>", lambda e: window.config(cursor="hand2"))
    widget.bind("<Leave>", lambda e: window.config(cursor=""))


# --- Choose file ---
selected_file = None


def choose_file():
    global selected_file
    filepath = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[("PDF files", "*.pdf"), ("Word documents", "*.docx"), ("All files", "*.*")]
    )
    if filepath:
        selected_file = filepath
        filename = os.path.basename(filepath)
        canvas.itemconfig(file_label, text=f"Selected: {filename}")
    else:
        selected_file = None
        canvas.itemconfig(file_label, text="No file selected")


# --- Toggle additional notes ---
def toggle_notes():
    if notes_var.get() == 1:
        notes_text.config(state=NORMAL)
    else:
        notes_text.delete("1.0", "end")
        notes_text.config(state=DISABLED)


def clear_form():
    global selected_file
    selected_file = None
    canvas.itemconfig(file_label, text="No file selected")
    pages_entry.delete(0, "end")
    copies_entry.delete(0, "end")
    paper_size_var.set("A4")
    color_choice.set("")
    notes_var.set(0)
    notes_text.delete("1.0", "end")
    notes_text.config(state=DISABLED)


# --- MODIFIED: Submit Request Function to include user_id ---
def submit_request():
    # 1. Validate user input
    if not user_id:
        messagebox.showerror("Error", "No user is logged in. Cannot submit request.")
        return
    if not selected_file:
        messagebox.showwarning("Missing File", "Please select a file to print.")
        return
    pages = pages_entry.get().strip()
    if not pages.isdigit() or int(pages) <= 0:
        messagebox.showwarning("Invalid Input", "Please enter a valid number of pages.")
        return
    copies = copies_entry.get().strip()
    if not copies.isdigit() or int(copies) <= 0:
        messagebox.showwarning("Invalid Input", "Please enter a valid number of copies.")
        return
    color_option = color_choice.get()
    if not color_option:
        messagebox.showwarning("Missing Option", "Please select a color option.")
        return

    # 2. Gather all data from the form
    filename = os.path.basename(selected_file)
    paper_size = paper_size_var.get()
    color_value = "Color" if color_option == 'color' else "Black & White"
    notes = notes_text.get("1.0", "end").strip() if notes_var.get() == 1 else ""

    # 3. Insert data into the database
    conn = None
    try:
        conn = create_db_connection()
        if conn is None:
            return

        cursor = conn.cursor()

        file_name = os.path.basename(selected_file)
        file_ext = os.path.splitext(file_name)[1].lower().replace(".", "")
        file_path = selected_file  # full local path

        insert_file_query = """
                INSERT INTO files (user_id, file_name, file_path, file_type)
                VALUES (%s, %s, %s, %s)
                """
        cursor.execute(insert_file_query, (user_id, file_name, file_path, file_ext))
        file_id = cursor.lastrowid

        # MODIFIED: Added user_id to the query
        sql_query = """
               INSERT INTO print_jobs 
               (user_id, file_id, pages, paper_size, color_option, copies, notes, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               """
        job_data = (
            user_id,
            file_id,  # linked file
            int(pages),
            paper_size,
            color_value,
            int(copies),
            notes,
            "Pending"
        )

        cursor.execute(sql_query, job_data)
        conn.commit()

        messagebox.showinfo("Success", f"Print request for '{filename}' submitted successfully!")

        date_now = datetime.now().strftime("%B %d, %Y")
        add_request_status(filename, date_now, "Pending")
        clear_form()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"An error occurred: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# --- Dynamic Request Status System ---
request_y = 470


def add_request_status(filename, date, status):
    """Display a new row in the Request Status section."""
    global request_y
    canvas.create_text(265, request_y + 12, anchor="nw", text=filename, fill="#000000", font=("Inter", 11))
    canvas.create_text(580, request_y + 12, anchor="nw", text=date, fill="#000000", font=("Inter", 11))
    canvas.create_text(740, request_y + 12, anchor="nw", text=status, fill="#000000", font=("Inter", 11, "bold"))
    request_y += 45


# --- Setup paths ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# --- MODIFIED: Get user_id and fullname from login.py ---
user_id = None
fullname = "User"
# Expects command: python printer.py <user_id> <fullname>
if len(sys.argv) > 2:
    try:
        user_id = int(sys.argv[1])
        fullname = sys.argv[2]
    except ValueError:
        print("Error: User ID passed from login was not a valid number.")
        user_id = None  # Invalidate user_id if it's not a number
        fullname = "User (Error)"
elif len(sys.argv) > 1:
    fullname = sys.argv[1]  # Fallback for testing

# --- Tkinter Window Setup ---
window = Tk()
window_width = 859
window_height = 534

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

window.configure(bg="#FFFFFF")
window.title("Printing Request")

canvas = Canvas(window, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# --- UI Elements (Your Original Code) ---
round_rectangle(canvas, 21, 16, 850, 520, r=0, fill="#FFFFFF", outline="#000000", width=1.5)
round_rectangle(canvas, 21, 15, 850, 100, r=0, fill="#000000", outline="#000000")
canvas.create_text(80, 45, anchor="nw", text=f"Welcome! {fullname}", fill="#FFFFFF", font=("Inter Bold", 30))
canvas.create_rectangle(239, 100, 240, 520, fill="#000000", outline="", width=3)


def create_rounded_menu_button(canvas, x, y, w, h, text, command=None):
    rect = round_rectangle(canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
    txt = canvas.create_text(x + 35, y + 10, text=text, anchor="nw", fill="#000000", font=("Inter Bold", 15))

    def on_click(event):
        if command: command()

    def on_hover(event):
        canvas.itemconfig(rect, fill="#E8E8E8");
        window.config(cursor="hand2")

    def on_leave(event):
        canvas.itemconfig(rect, fill="#FFFFFF");
        window.config(cursor="")

    for tag in (rect, txt):
        canvas.tag_bind(tag, "<Button-1>", on_click)
        canvas.tag_bind(tag, "<Enter>", on_hover)
        canvas.tag_bind(tag, "<Leave>", on_leave)


create_rounded_menu_button(canvas, 56, 129, 151, 38, "Profile", open_user_py)
create_rounded_menu_button(canvas, 56, 178, 151, 38, "Notifications", open_notification_py)
create_rounded_menu_button(canvas, 56, 227, 151, 38, "Pricelist", open_prices_py)
create_rounded_menu_button(canvas, 56, 276, 151, 38, "Help", open_help_py)

round_rectangle(canvas, 249, 112, 832, 222, r=15, fill="#FFFFFF", outline="#000000", width=1)
canvas.create_text(432, 143, anchor="nw", text="Drag and drop file here or", fill="#000000", font=("Inter Bold", 15))
choose_btn = round_rectangle(canvas, 472, 178, 578, 213, r=10, fill="#000000", outline="#000000")
choose_text = canvas.create_text(487, 185, anchor="nw", text="Choose File", fill="#FFFFFF", font=("Inter Bold", 12))
file_label = canvas.create_text(610, 185, anchor="nw", text="No file selected", fill="#000000", font=("Inter", 11))

canvas.create_text(249, 232, anchor="nw", text="Number of Pages", fill="#000000", font=("Inter Bold", 13))
round_rectangle(canvas, 249, 254, 351, 282, r=10, fill="#FFFFFF", outline="#000000")
pages_entry = Entry(window, bd=0, bg="#FFFFFF", relief="flat", highlightthickness=0)
pages_entry.place(x=255, y=260, width=90, height=20)

canvas.create_text(249, 288, anchor="nw", text="Paper Size", fill="#000000", font=("Inter Bold", 13))
round_rectangle(canvas, 249, 310, 351, 338, r=10, fill="#FFFFFF", outline="#000000")
paper_size_var = StringVar(window)
paper_size_var.set("A4")
paper_sizes = ["Short", "A4", "Long"]
size_dropdown = OptionMenu(window, paper_size_var, *paper_sizes)
size_dropdown.config(width=9, font=("Inter", 10), bg="#FFFFFF", highlightthickness=0, relief="flat", borderwidth=0,
                     indicatoron=0)
size_dropdown.place(x=252, y=312, width=97, height=24)

canvas.create_text(249, 344, anchor="nw", text="Copies", fill="#000000", font=("Inter Bold", 13))
round_rectangle(canvas, 249, 366, 351, 394, r=10, fill="#FFFFFF", outline="#000000")
copies_entry = Entry(window, bd=0, bg="#FFFFFF", relief="flat", highlightthickness=0)
copies_entry.place(x=255, y=372, width=90, height=20)

canvas.create_text(462, 232, anchor="nw", text="Color Option", fill="#000000", font=("Inter Bold", 13))
color_choice = StringVar(value="")
bw_check = Checkbutton(window, text="Black & White", variable=color_choice, onvalue="bw", offvalue="", bg="#FFFFFF",
                       command=lambda: color_choice.set("bw"))
color_check = Checkbutton(window, text="Color", variable=color_choice, onvalue="color", offvalue="", bg="#FFFFFF",
                          command=lambda: color_choice.set("color"))
bw_check.place(x=436, y=257)
color_check.place(x=558, y=257)

canvas.create_text(525, 285, anchor="nw", text="Additional Notes", fill="#000000", font=("Inter Bold", 13))
notes_var = IntVar()
notes_toggle = Checkbutton(window, variable=notes_var, bg="#FFFFFF", command=toggle_notes)
notes_toggle.place(x=497, y=280)
round_rectangle(canvas, 372, 309, 819, 455, r=10, fill="#FFFFFF", outline="#000000", width=1)
notes_text = Text(window, bd=0, relief="flat", wrap="word", highlightthickness=0)
notes_text.place(x=375, y=312, width=440, height=140)
notes_text.config(state=DISABLED)

submit_rect = round_rectangle(canvas, 249, 404, 351, 432, r=15, fill="#000000", outline="#000000")
submit_text = canvas.create_text(273, 410, anchor="nw", text="Submit", fill="#FFFFFF", font=("Inter Bold", 12))

history_rect = round_rectangle(canvas, 683, 240, 812, 294, r=10, fill="#000000", outline="#000000")
history_text = canvas.create_text(690, 258, anchor="nw", text="Request History", fill="#FFFFFF",
                                  font=("Inter Bold", 12))


def on_history_hover(event): canvas.itemconfig(history_rect, fill="#333333"); window.config(cursor="hand2")


def on_history_leave(event): canvas.itemconfig(history_rect, fill="#000000"); window.config(cursor="")


def on_history_click(event): open_history_py()


def on_hover_submit(event): canvas.itemconfig(submit_rect, fill="#333333"); window.config(cursor="hand2")


def on_leave_submit(event): canvas.itemconfig(submit_rect, fill="#000000"); window.config(cursor="")


def on_click_submit(event): submit_request()


def on_hover_choose(event): canvas.itemconfig(choose_btn, fill="#333333"); window.config(cursor="hand2")


def on_leave_choose(event): canvas.itemconfig(choose_btn, fill="#000000"); window.config(cursor="")


def on_click_choose(event): choose_file()


for tag in (submit_rect, submit_text):
    canvas.tag_bind(tag, "<Enter>", on_hover_submit)
    canvas.tag_bind(tag, "<Leave>", on_leave_submit)
    canvas.tag_bind(tag, "<Button-1>", on_click_submit)
for tag in (choose_btn, choose_text):
    canvas.tag_bind(tag, "<Enter>", on_hover_choose)
    canvas.tag_bind(tag, "<Leave>", on_leave_choose)
    canvas.tag_bind(tag, "<Button-1>", on_click_choose)
for tag in (history_rect, history_text):
    canvas.tag_bind(tag, "<Enter>", on_history_hover)
    canvas.tag_bind(tag, "<Leave>", on_history_leave)
    canvas.tag_bind(tag, "<Button-1>", on_history_click)

canvas.create_text(254, 442, anchor="nw", text="Request Status", fill="#000000", font=("Inter Bold", 13))
round_rectangle(canvas, 249, 465, 832, 510, r=10, fill="#FFFFFF", outline="#000000", width=1)

# --- NEW: Load user's request history when the application starts ---
load_user_requests()

window.resizable(False, False)
window.mainloop()