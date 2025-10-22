# Notifications – icons above buttons + visible borders

from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Label, Frame, Scrollbar, messagebox, ttk
import tkinter as tk # Use tk alias
import math
import sys
import subprocess
import mysql.connector
from datetime import datetime # To format timestamps

# --- Get User ID and Fullname from Arguments ---
user_id = None
fullname = "User" # Default
if len(sys.argv) > 1:
    try:
        user_id = int(sys.argv[1]) # Expect user_id as the first argument
    except ValueError:
        print("Warning: First argument should be user_id (integer).")
        # Handle error or exit if user_id is crucial
if len(sys.argv) > 2:
    fullname = sys.argv[2] # Fullname as the second argument

# --- Database Connection ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="copy_corner_db"
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Connection failed: {err}")
        return None

# --- Fetch Notifications (MODIFIED) ---
def fetch_notifications(current_user_id):
    """Fetches ALL notifications (Read and Unread) for the user or sent to all."""
    if current_user_id is None:
        return [] # Cannot fetch without user ID

    notifications = []
    conn = get_db_connection()
    if not conn: return notifications

    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch notifications specifically for the user OR where user_id is NULL (broadcast)
        # Fetch ALL statuses, ordered newest first
        query = """
            SELECT notif_id, subject, message, created_at, status
            FROM notifications
            WHERE (user_id = %s OR user_id IS NULL)
            ORDER BY created_at DESC
        """
        cursor.execute(query, (current_user_id,))
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching notifications:\n{err}")
        return []

# --- Mark Notification as Read ---
def mark_notification_as_read(notif_id):
    """Updates the status of a specific notification to 'Read'."""
    conn = get_db_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        query = "UPDATE notifications SET status = 'Read' WHERE notif_id = %s"
        cursor.execute(query, (notif_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Marked notification {notif_id} as read.")
    except mysql.connector.Error as err:
         print(f"Error marking notification {notif_id} as read: {err}")

# --- Clear Read Notifications (NEW FUNCTION) ---
def clear_read_notifications():
    """Marks all currently 'Unread' notifications for the user as 'Read'."""
    if user_id is None:
        messagebox.showerror("Error", "User ID not found.")
        return

    conn = get_db_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        # Update status to 'Read' for all 'Unread' messages for this user or broadcast messages
        query = """
            UPDATE notifications
            SET status = 'Read'
            WHERE (user_id = %s OR user_id IS NULL) AND status = 'Unread'
        """
        cursor.execute(query, (user_id,))
        affected_rows = cursor.rowcount # Get how many were updated
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Marked {affected_rows} notifications as read.")
        # Refresh the list to show the visual change
        refresh_notifications()
        if affected_rows > 0:
             messagebox.showinfo("Notifications Cleared", f"{affected_rows} notifications marked as read.")
        else:
             messagebox.showinfo("Notifications Cleared", "No new notifications to clear.")

    except mysql.connector.Error as err:
         messagebox.showerror("Database Error", f"Error clearing notifications: {err}")

# --- Show Full Message Window (MODIFIED) ---
def show_message_window(notification_details):
    """Creates a Toplevel window to display the full notification message."""
    notif_id = notification_details['notif_id']
    subject = notification_details.get('subject', 'No Subject')
    message = notification_details.get('message', 'No Message Body')
    current_status = notification_details.get('status', 'Unread') # Get status

    # --- Mark as read only if it was Unread ---
    if current_status == 'Unread':
        mark_notification_as_read(notif_id)
        # We will refresh the list *after* the window closes anyway

    # --- Create the Toplevel window ---
    message_win = tk.Toplevel(window)
    message_win.title(f"Subject: {subject}")
    message_win.geometry("450x300") # Adjust size as needed
    message_win.configure(bg=WHITE)
    message_win.transient(window) # Keep it on top of the main window
    message_win.grab_set() # Prevent interaction with main window while open

    # Center the message window relative to the main window
    win_x = window.winfo_x()
    win_y = window.winfo_y()
    win_w = window.winfo_width()
    win_h = window.winfo_height()
    msg_w = 450
    msg_h = 300
    msg_x = win_x + (win_w // 2) - (msg_w // 2)
    msg_y = win_y + (win_h // 2) - (msg_h // 2)
    message_win.geometry(f"{msg_w}x{msg_h}+{msg_x}+{msg_y}")

    # --- Add Content ---
    # Subject Label
    subject_label_popup = Label(
        message_win,
        text=subject,
        font=("Inter Bold", 14),
        bg=WHITE,
        wraplength=430, # Wrap subject if long
        justify="left"
    )
    subject_label_popup.pack(pady=(10, 5), padx=10, anchor="w")

    # Separator
    ttk.Separator(message_win, orient="horizontal").pack(fill="x", padx=10)

    # Message Area (using a Text widget for scrollability and wrapping)
    message_frame = Frame(message_win, bg=WHITE)
    message_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))

    message_text_widget = Text(
        message_frame,
        wrap=tk.WORD,
        font=("Inter", 11),
        bg=WHITE,
        bd=0,
        highlightthickness=0,
        padx=5,
        pady=5
    )
    message_text_widget.insert(tk.END, message)
    message_text_widget.config(state=tk.DISABLED) # Make it read-only

    # Add Scrollbar to Text widget
    msg_scrollbar = ttk.Scrollbar(message_frame, orient="vertical", command=message_text_widget.yview)
    message_text_widget.configure(yscrollcommand=msg_scrollbar.set)

    msg_scrollbar.pack(side="right", fill="y")
    message_text_widget.pack(side="left", fill="both", expand=True)


    # --- Back/Close Button ---
    back_button = Button(
        message_win,
        text="Close",
        font=("Inter Bold", 11),
        command=message_win.destroy, # Closes this Toplevel
        width=8
    )
    back_button.pack(pady=(5, 10))

    # Wait for the window to be closed before returning
    message_win.wait_window()

    # --- Refresh main list after closing ---
    # Needed now because marking read happens inside, and we want to see the visual change
    refresh_notifications()

# --- Display Notifications Function (MODIFIED) ---
def display_notifications(frame, notifications_data):
    """Populates the frame with notification items. Shows Read items differently."""
    # Clear previous notifications
    for widget in frame.winfo_children():
        widget.destroy()

    if not notifications_data:
        no_notif_label = Label(
            frame,
            text="No notifications.", # Changed message slightly
            font=("Inter", 14),
            bg=WHITE,
            fg="grey"
        )
        no_notif_label.pack(pady=20, padx=10)
        return

    for notification in notifications_data:
        notif_id = notification['notif_id']
        status = notification.get('status', 'Unread') # Get status

        # Determine colors based on status
        text_color = BLACK if status == 'Unread' else "grey"
        time_color = "grey" # Keep time gray
        frame_bg = WHITE # Keep frame background white

        # Frame for each notification item
        item_frame = Frame(frame, bg=frame_bg, bd=1, relief="solid", padx=5, pady=5)
        item_frame.pack(fill="x", padx=10, pady=(5, 0))

        # Subject Label (Bold)
        subject_text = notification.get('subject', 'No Subject')
        subject_label = Label(
            item_frame,
            text=subject_text,
            font=("Inter Bold", 13),
            bg=frame_bg, # Match frame background
            fg=text_color, # Set color based on status
            anchor="w",
            justify="left"
        )
        subject_label.pack(fill="x")

        # Timestamp Label (Smaller, Gray)
        timestamp = notification.get('created_at', datetime.now())
        try:
            time_str = timestamp.strftime("%b %d, %Y - %I:%M %p")
        except AttributeError:
             time_str = "Invalid Date"

        time_label = Label(
            item_frame,
            text=time_str,
            font=("Inter", 9),
            bg=frame_bg, # Match frame background
            fg=time_color, # Keep time gray
            anchor="w",
            justify="left"
        )
        time_label.pack(fill="x")

        # --- Bind Click to Show Message Window ---
        # Pass the whole notification dictionary to the popup function
        item_frame.bind("<Button-1>", lambda e, notif=notification: show_message_window(notif))
        subject_label.bind("<Button-1>", lambda e, notif=notification: show_message_window(notif))
        time_label.bind("<Button-1>", lambda e, notif=notification: show_message_window(notif))
        # Add hover cursor
        for w in [item_frame, subject_label, time_label]:
            w.bind("<Enter>", lambda e: window.config(cursor="hand2"))
            w.bind("<Leave>", lambda e: window.config(cursor=""))


# --- Scrollbar Helper Functions ---
# (Keep on_frame_configure and on_mousewheel as they are)
def on_frame_configure(canvas):
    """Reset the scroll region to encompass the inner frame"""
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_mousewheel(event, canvas):
    """Scroll the canvas on mousewheel event"""
    if canvas.yview() == (0.0, 1.0) and event.delta > 0: # Prevent scroll up if fully visible and at top
        if canvas.canvasy(0) == 0 : return # Double check y position
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# --- Rounded Rectangle Function ---
# (Keep round_rectangle as it is)
def round_rectangle(canvas, x1, y1, x2, y2, r=15, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame1") # Verify this path

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset not found at {asset_file}") # More informative warning
    return asset_file

# Constants
WHITE = "#FFFFFF"
BLACK = "#000000"
FONT_BTN = ("Inter Bold", -16)
FONT_BTN_SM = ("Inter Bold", -15)


# --- Navigation Functions ---
# (Keep navigation functions as they are)
def open_user_py():
    if user_id is None: messagebox.showerror("Error", "User ID not found."); return
    subprocess.Popen([sys.executable, "user.py", str(user_id), fullname]); window.destroy()
def open_printer_py():
    if user_id is None: messagebox.showerror("Error", "User ID not found."); return
    subprocess.Popen([sys.executable, "printer.py", str(user_id), fullname]); window.destroy()
def open_prices_py():
    if user_id is None: messagebox.showerror("Error", "User ID not found."); return
    subprocess.Popen([sys.executable, "Prices.py", "Notification.py", str(user_id), fullname]); window.destroy()
def open_help_py():
    if user_id is None: messagebox.showerror("Error", "User ID not found."); return
    subprocess.Popen([sys.executable, "Help.py", str(user_id), fullname]); window.destroy()
def make_icon_clickable(widget, command):
    widget.bind("<Button-1>", lambda e: command())
    widget.bind("<Enter>", lambda e: window.config(cursor="hand2"))
    widget.bind("<Leave>", lambda e: window.config(cursor=""))

# -------- window --------
window = Tk()
# --- Center the Window ---
window_width = 829 # Adjusted to match canvas
window_height = 504 # Adjusted to match canvas
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.configure(bg=WHITE)
window.title("Notification")

c = Canvas(window, bg=WHITE, height=504, width=829, bd=0, highlightthickness=0, relief="ridge")
c.place(x=0, y=0)

# background + header
c.create_rectangle(0, 0, 829, 504, fill=WHITE, outline="")
c.create_rectangle(0, 0, 829, 85, fill=BLACK, outline="")
# title
c.create_text(228, 17, anchor="nw", text="Notifications", fill=WHITE, font=("Inter Bold", -36))
# left divider
c.create_rectangle(209, -1, 210, 504, fill=BLACK, outline="")

# --- Reusable Rounded Menu Button ---
# (Keep create_rounded_menu_button as it is)
def create_rounded_menu_button(canvas, x, y, w, h, text, command=None):
    rect = round_rectangle(canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
    txt = canvas.create_text(x + 40, y + (h/2), text=text, anchor="w", fill="#000000", font=("Inter Bold", 15))
    def on_click(event):
        if command: command()
    def on_hover(event):
        canvas.itemconfig(rect, fill="#E8E8E8"); canvas.config(cursor="hand2")
    def on_leave(event):
        canvas.itemconfig(rect, fill="#FFFFFF"); canvas.config(cursor="")
    canvas.tag_bind(rect, "<Button-1>", on_click); canvas.tag_bind(txt, "<Button-1>", on_click)
    canvas.tag_bind(rect, "<Enter>", on_hover); canvas.tag_bind(txt, "<Enter>", on_hover)
    canvas.tag_bind(rect, "<Leave>", on_leave); canvas.tag_bind(txt, "<Leave>", on_leave)
    return rect, txt

# --- Left Menu Buttons ---
Y_START = 129; BTN_H = 38; BTN_W = 161; PADDING = 11; BTN_X = 26
create_rounded_menu_button(c, BTN_X, Y_START, BTN_W, BTN_H, "Profile", open_user_py)
create_rounded_menu_button(c, BTN_X, Y_START + BTN_H + PADDING, BTN_W, BTN_H, "Print Request", open_printer_py)
create_rounded_menu_button(c, BTN_X, Y_START + 2*(BTN_H + PADDING), BTN_W, BTN_H, "Pricelist", open_prices_py)
create_rounded_menu_button(c, BTN_X, Y_START + 3*(BTN_H + PADDING), BTN_W, BTN_H, "Help", open_help_py)

# ------------- Left icons as Labels -------------
ICON_X = 43 # X-center for icons
# (Keep icon loading and placement code as it is)
# Use global variables to store images, preventing garbage collection
window.icon_edit = None; window.icon_bell = None; window.icon_sheet = None; window.icon_help = None
try:
    window.icon_edit   = PhotoImage(file=relative_to_assets("account.png"))
    window.icon_bell   = PhotoImage(file=relative_to_assets("image_14.png"))
    window.icon_sheet  = PhotoImage(file=relative_to_assets("image_15.png"))
    window.icon_help   = PhotoImage(file=relative_to_assets("image_16.png"))
except tk.TclError as e: print(f"Error loading icon: {e}")
if window.icon_edit:
    lbl_edit  = Label(window, image=window.icon_edit,  bg=WHITE, bd=0); lbl_edit.place(x=ICON_X, y=Y_START + BTN_H/2, anchor="center"); make_icon_clickable(lbl_edit, open_user_py)
if window.icon_bell:
    lbl_bell  = Label(window, image=window.icon_bell,  bg=WHITE, bd=0); lbl_bell.place(x=ICON_X, y=Y_START + BTN_H + PADDING + BTN_H/2, anchor="center"); make_icon_clickable(lbl_bell, open_printer_py)
if window.icon_sheet:
    lbl_sheet = Label(window, image=window.icon_sheet, bg=WHITE, bd=0); lbl_sheet.place(x=ICON_X, y=Y_START + 2*(BTN_H + PADDING) + BTN_H/2, anchor="center"); make_icon_clickable(lbl_sheet, open_prices_py)
if window.icon_help:
    lbl_help  = Label(window, image=window.icon_help,  bg=WHITE, bd=0); lbl_help.place(x=ICON_X, y=Y_START + 3*(BTN_H + PADDING) + BTN_H/2, anchor="center"); make_icon_clickable(lbl_help, open_help_py)


# --- Notification Scrollable Area ---
NOTIF_X, NOTIF_Y = 224, 97
NOTIF_W, NOTIF_H = 589, 391
# (Keep scrollable area setup code as it is)
notif_container = Frame(window, bg=WHITE, bd=1, relief="solid"); notif_container.place(x=NOTIF_X, y=NOTIF_Y, width=NOTIF_W, height=NOTIF_H)
notif_canvas = Canvas(notif_container, bg=WHITE, bd=0, highlightthickness=0)
notif_scrollbar = ttk.Scrollbar(notif_container, orient="vertical", command=notif_canvas.yview); notif_canvas.configure(yscrollcommand=notif_scrollbar.set)
notif_scrollbar.pack(side="right", fill="y"); notif_canvas.pack(side="left", fill="both", expand=True)
notif_content_frame = Frame(notif_canvas, bg=WHITE)
notif_content_frame_window = notif_canvas.create_window((0, 0), window=notif_content_frame, anchor="nw")
notif_content_frame.bind("<Configure>", lambda event, canvas=notif_canvas: on_frame_configure(canvas))
notif_canvas.bind("<Configure>", lambda e: notif_canvas.itemconfig(notif_content_frame_window, width=e.width))
# Bind mousewheel scrolling
window.bind_all("<MouseWheel>", lambda event: on_mousewheel(event, notif_canvas)) # Bind globally


# --- Add Clear Read Button (NEW) ---
clear_button = Button(
    window,
    text="Clear Read",
    font=("Inter Bold", 10),
    command=clear_read_notifications,
    relief="raised", # Or "flat" etc.
    bd=1,
    bg="#F0F0F0", # Light gray background
    activebackground="#D9D9D9" # Slightly darker when clicked
)
# Place it below the notification area, aligned right
clear_button.place(x=NOTIF_X + NOTIF_W - 80, y=NOTIF_Y + NOTIF_H + 5, width=70, height=25)


# --- Fetch and Display Initial Notifications ---
def refresh_notifications():
    notifications = fetch_notifications(user_id)
    display_notifications(notif_content_frame, notifications)

if user_id is not None:
    refresh_notifications()
else:
     Label(notif_content_frame, text="Could not load notifications (User ID missing).",
           font=("Inter", 12), bg=WHITE, fg="red").pack(pady=20)


window.resizable(False, False)
window.mainloop()