from pathlib import Path
from tkinter import Tk, Canvas, PhotoImage, messagebox, Frame, Label, Scrollbar, ttk
import tkinter as tk # Use tk alias
import subprocess
import sys
import mysql.connector
from datetime import datetime

# --- Get User ID and Fullname from Arguments ---
user_id = None
fullname = "User" # Default
if len(sys.argv) > 1:
    try:
        user_id = int(sys.argv[1]) # Expect user_id as the first argument
    except ValueError:
        print("Warning: First argument should be user_id (integer).")
if len(sys.argv) > 2:
    fullname = sys.argv[2] # Fullname as the second argument


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(
    r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame1" # Verify this path
)

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset not found at {asset_file}")
    return asset_file

# Constants
WHITE = "#FFFFFF"
BLACK = "#000000"
LIGHT_GRAY = "#DDDDDD"

# --- Database Connection ---
def get_db_connection():
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

# --- Fetch and Display History Function (MODIFIED) ---
def fetch_and_display_history(frame, target_user_id):
    """Fetches print job history for the user and displays it in the scrollable frame."""
    # Clear previous history items
    for widget in frame.winfo_children():
        widget.destroy()

    if target_user_id is None:
         Label(frame, text="Could not load history (User ID missing).",
               font=("Inter Bold", 16), bg=WHITE, fg="red").pack(pady=20, padx=10)
         return

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return

        cursor = conn.cursor(dictionary=True)
        # Query print jobs for the specific user, join with files to get filename
        # Order by submission date, newest first
        sql_query = """
            SELECT pj.job_id, f.file_name, pj.created_at
            FROM print_jobs pj
            LEFT JOIN files f ON pj.file_id = f.file_id
            WHERE pj.user_id = %s
            ORDER BY pj.created_at DESC
        """
        cursor.execute(sql_query, (target_user_id,))
        history = cursor.fetchall()

        if not history:
             Label(frame, text="No print history found.",
                   font=("Inter Bold", 16), bg=WHITE, fg="grey").pack(pady=20, padx=10)
             return

        # Configure columns for layout within the frame
        frame.columnconfigure(0, weight=1) # Row Number
        frame.columnconfigure(1, weight=5) # File Name
        frame.columnconfigure(2, weight=3) # Date/Time

        row_index = 0 # Grid row counter
        item_number = 1 # Sequential number for display

        for item in history:
            # We fetch job_id but don't display it directly
            job_id = item['job_id']
            file_name = item.get('file_name', 'File not found')
            created_at = item['created_at']

            # Format date and time
            date_str = created_at.strftime("%Y-%m-%d") if created_at else "N/A"
            time_str = created_at.strftime("%I:%M %p") if created_at else "" # AM/PM format
            full_time_str = f"{date_str}\n{time_str}".strip() # Combine date and time

            # Display Sequential Number
            num_label = Label(frame, text=str(item_number), font=("Inter Bold", 16), bg=WHITE, anchor="nw")
            num_label.grid(row=row_index, column=0, padx=(30, 10), pady=10, sticky="nw")

            # Display File Name
            file_label = Label(frame, text=file_name, font=("Inter Bold", 16), bg=WHITE, anchor="nw", wraplength=350, justify="left") # Added wrap
            file_label.grid(row=row_index, column=1, padx=10, pady=10, sticky="nw")

            # Display Date/Time
            time_label = Label(frame, text=full_time_str, font=("Inter Bold", 16), bg=WHITE, anchor="ne", justify="right") # Anchor right
            time_label.grid(row=row_index, column=2, padx=(10, 30), pady=10, sticky="ne")

            # Separator Line
            sep = ttk.Separator(frame, orient="horizontal")
            sep.grid(row=row_index + 1, column=0, columnspan=3, sticky="ew", padx=5)

            row_index += 2
            item_number += 1

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to fetch history: {err}")
    finally:
        if conn and conn.is_connected():
            # cursor should be closed before connection if it exists
            if 'cursor' in locals() and cursor:
                 cursor.close()
            conn.close()


# --- Scrollbar Helper Functions ---
def on_frame_configure(canvas):
    """Reset the scroll region to encompass the inner frame"""
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_mousewheel(event, canvas):
    """Scroll the canvas on mousewheel event"""
    # Prevent scrolling up past the top
    current_y_view = canvas.yview()
    if current_y_view[0] == 0.0 and event.delta > 0:
        return
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# --- Helper to create rounded rectangles ---
def round_rectangle(canvas, x1, y1, x2, y2, r=15, **kwargs):
    points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1,
              x2, y1, x2, y1+r, x2, y1+r, x2, y2-r,
              x2, y2-r, x2, y2, x2-r, y2, x2-r, y2,
              x1+r, y2, x1+r, y2, x1, y2, x1, y2-r,
              x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- Open Printer.py when Back is clicked ---
def open_printer_py():
    if user_id is None:
        messagebox.showerror("Error", "User ID not found. Cannot go back.")
        window.destroy()
        return
    window.destroy()
    subprocess.Popen([sys.executable, "printer.py", str(user_id), fullname])

# --- Window Setup ---
window = Tk()
window.title("History")

window_width = 900
window_height = 504
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.configure(bg="#FFFFFF")

canvas = Canvas(window, bg="#FFFFFF", height=504, width=900, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# --- Header ---
canvas.create_rectangle(0.0, 0.0, 900.0, 85.0, fill="#000000", outline="")
canvas.create_text(300.0, 20.0, anchor="nw", text="Request History", fill="#FFFFFF", font=("Inter Bold", 36)) # Centered Title

# --- Table Headers Area (Static Background and Text) ---
canvas.create_rectangle(0.0, 85.0, 900.0, 132.0, fill=WHITE, outline="") # White background for headers
canvas.create_text(31.0, 93.0, anchor="nw", text="#", fill="#000000", font=("Inter Bold", 20)) # Number header
canvas.create_text(200.0, 93.0, anchor="nw", text="File Name", fill="#000000", font=("Inter Bold", 20)) # Adjusted X
canvas.create_text(700.0, 93.0, anchor="nw", text="Date Submitted", fill="#000000", font=("Inter Bold", 20)) # Adjusted X
canvas.create_rectangle(0.0, 130.0, 900.0, 133.0, fill="#000000", outline="") # Header underline

# --- Scrollable History Area ---
HISTORY_X, HISTORY_Y = 0, 133 # Start below header line
HISTORY_W, HISTORY_H = 900, 300 # Adjust height as needed (leave space for button)

# 1. Main container (no border needed if it fills space)
history_container = Frame(window, bg=WHITE)
history_container.place(x=HISTORY_X, y=HISTORY_Y, width=HISTORY_W, height=HISTORY_H)

# 2. Canvas for scrolling
history_canvas = Canvas(history_container, bg=WHITE, bd=0, highlightthickness=0)

# 3. Scrollbar
history_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=history_canvas.yview)
history_canvas.configure(yscrollcommand=history_scrollbar.set)

# 4. Pack scrollbar and canvas
history_scrollbar.pack(side="right", fill="y")
history_canvas.pack(side="left", fill="both", expand=True)

# 5. Inner content frame
history_content_frame = Frame(history_canvas, bg=WHITE)
history_content_frame_window = history_canvas.create_window((0, 0), window=history_content_frame, anchor="nw")

# 6. Bind events
history_content_frame.bind(
    "<Configure>",
    lambda event, canvas=history_canvas: on_frame_configure(canvas)
)
history_canvas.bind( # Make content frame fill canvas width
    "<Configure>",
    lambda e: history_canvas.itemconfig(history_content_frame_window, width=e.width)
)
# Bind mousewheel scrolling globally directed to this canvas
window.bind_all(
    "<MouseWheel>",
    lambda event: on_mousewheel(event, history_canvas)
)


# --- Rounded Back Button ---
# Positioned below the scrollable area
back_rect = round_rectangle(canvas, 31, 450, 140, 493, r=15, fill="#000000", outline="#000000") # Adjusted Y
back_text = canvas.create_text(60, 457, anchor="nw", text="Back", fill="#FFFFFF", font=("Inter Bold", 20)) # Adjusted Y

# Hover + Click effects
def on_hover(event):
    canvas.itemconfig(back_rect, fill="#333333"); window.config(cursor="hand2")
def on_leave(event):
    canvas.itemconfig(back_rect, fill="#000000"); window.config(cursor="")
def on_click(event):
    open_printer_py()

for tag in (back_rect, back_text):
    canvas.tag_bind(tag, "<Enter>", on_hover)
    canvas.tag_bind(tag, "<Leave>", on_leave)
    canvas.tag_bind(tag, "<Button-1>", on_click)

# --- Initial Data Load ---
fetch_and_display_history(history_content_frame, user_id) # Call the function


window.resizable(False, False)
window.mainloop()