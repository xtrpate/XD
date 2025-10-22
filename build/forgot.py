from pathlib import Path
from tkinter import Tk, Canvas, Entry, messagebox
import mysql.connector
import subprocess
import sys
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sent_code = None
current_email = None
is_verified = False  # flag to track code verification status

# --- Placeholder Entry Class ---
class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", show_char="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]
        self.show_char = show_char
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    def put_placeholder(self):
        self.delete(0, "end")
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color
        if self.show_char:
            self.config(show="")

    def foc_in(self, *args):
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color
            if self.show_char:
                self.config(show=self.show_char)

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


# --- Database Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="printing_system"
    )


# --- Check if Email Exists ---
def email_exists(email):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        return False


# --- Send Verification Code ---
def send_verification_code(receiver_email):
    code = str(random.randint(100000, 999999))
    sender_email = "titematigas3@gmail.com"
    app_password = "yykmhsqkpeyjluxk"

    subject = "Email Verification"

    # HTML email template
    html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="background-color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="color: #222;">Email Verification</h2>
                </div>
                <div style="padding: 30px; color: #333;">
                    <p>Hello,</p>
                    <p>Your account is nearly set up. Please use this code to verify your email address.</p>
                    <div style="background-color: #f1f1f1; border-radius: 5px; text-align: center; font-size: 28px; 
                                letter-spacing: 5px; padding: 15px 0; margin: 25px 0; font-weight: bold; color: #333;">
                        {code}
                    </div>
                    <p style="font-size: 14px; text-align: center; color: #555;">
                        <b>Code will expire in 30 minutes.</b>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Attach HTML content
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return code
    except Exception as e:
        print("Error sending email:", e)
        return None


# --- BUTTON: Get Code ---
def on_get_code():
    global sent_code, current_email

    email = entry_email.get().strip()
    if not email or email == entry_email.placeholder:
        messagebox.showerror("Error", "Please enter your email address.")
        return

    if not email_exists(email):
        messagebox.showerror("Error", "Email not found in the database.")
        return

    sent_code = send_verification_code(email)
    if sent_code:
        current_email = email
        messagebox.showinfo("Verification Code Sent", f"A code has been sent to {email}.")
    else:
        messagebox.showerror("Error", "Failed to send verification code. Please try again.")


# --- BUTTON: Verify Code ---
def on_send_code():
    global sent_code, is_verified

    entered_code = entry_verification.get().strip()
    if not entered_code or entered_code == entry_verification.placeholder:
        messagebox.showerror("Error", "Please enter the verification code.")
        return

    if not sent_code:
        messagebox.showerror("Error", "Please click 'Get Code' first to receive your verification code.")
        return

    if entered_code == sent_code:
        is_verified = True
        messagebox.showinfo("Success", "Verification successful! You can now reset your password.")
    else:
        is_verified = False
        messagebox.showerror("Error", "Invalid verification code. Please try again.")


# --- BUTTON: Reset Password ---
def reset_password(email):
    global is_verified

    if not is_verified:
        messagebox.showerror("Error", "Please verify your email first.")
        return

    new_pass = entry_new_password.get()
    confirm_pass = entry_confirm_password.get()

    if new_pass == "New Password":
        new_pass = ""
    if confirm_pass == "Confirm Password":
        confirm_pass = ""

    if not new_pass or not confirm_pass:
        messagebox.showerror("Error", "All fields are required.")
        return

    if len(new_pass) < 8:
        messagebox.showerror("Error", "Password must be at least 8 characters long.")
        return
    if not any(c.isupper() for c in new_pass):
        messagebox.showerror("Error", "Password must contain at least one uppercase letter.")
        return
    if not any(c.islower() for c in new_pass):
        messagebox.showerror("Error", "Password must contain at least one lowercase letter.")
        return
    if not any(c.isdigit() for c in new_pass):
        messagebox.showerror("Error", "Password must contain at least one digit.")
        return
    if new_pass != confirm_pass:
        messagebox.showerror("Error", "Passwords do not match.")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_pass, email))
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("Success", "Password has been reset successfully!")
        window.destroy()
        subprocess.Popen([sys.executable, "login.py"])
    except Exception as e:
        messagebox.showerror("Database Error", str(e))


# --- GO BACK ---
def go_back():
    window.destroy()
    subprocess.Popen([sys.executable, "login.py"])


# --- Round Rectangle Helper ---
def round_rectangle(canvas, x1, y1, x2, y2, r=15, **kwargs):
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- Create Rounded Entry ---
def create_rounded_entry(x_pos, y_pos, placeholder="", show_char="", with_eye=False):
    round_rectangle(canvas, x_pos + 12, y_pos + 7, x_pos + 232, y_pos + 37, r=10, fill="#999999", outline="")
    round_rectangle(canvas, x_pos + 10, y_pos + 5, x_pos + 230, y_pos + 35, r=10, fill="white", outline="#000000", width=1)

    entry = PlaceholderEntry(
        window,
        placeholder=placeholder,
        bd=0,
        bg="white",
        fg="#000000",
        show_char=show_char,
        highlightthickness=0,
        font=("Inter", 12)
    )
    canvas.create_window(x_pos + 110, y_pos + 20, width=190.0, height=24, window=entry, anchor="center")

    icon_item = None
    if with_eye:
        icon_item = canvas.create_text(
            x_pos + 205, y_pos + 12,
            anchor="nw",
            text="👁",
            fill="black",
            font=("Arial", 12)
        )
        canvas.tag_bind(icon_item, "<Button-1>", lambda e: toggle_password(entry, icon_item))
        canvas.tag_bind(icon_item, "<Enter>", lambda e: window.config(cursor="hand2"))
        canvas.tag_bind(icon_item, "<Leave>", lambda e: window.config(cursor=""))

    return entry, icon_item


# --- Toggle Password Visibility ---
def toggle_password(entry, icon_item):
    if entry.cget("show") == "":
        entry.config(show="*")
        canvas.itemconfig(icon_item, text="🙈")
    else:
        entry.config(show="")
        canvas.itemconfig(icon_item, text="👁")


# --- Create Rounded Button ---
def create_rounded_button(x, y, text, command, width=150, height=35, bg="#000000", fg="white"):
    btn_id = round_rectangle(canvas, x, y, x + width, y + height, r=15, fill=bg, outline="")
    text_id = canvas.create_text(x + width/2, y + height/2, text=text, fill=fg, font=("Inter Bold", 12), anchor="center")

    def on_click(event):
        command()

    def on_hover(event):
        canvas.itemconfig(btn_id, fill="#333333")

    def on_leave(event):
        canvas.itemconfig(btn_id, fill=bg)

    for item in (btn_id, text_id):
        canvas.tag_bind(item, "<Button-1>", on_click)
        canvas.tag_bind(item, "<Enter>", on_hover)
        canvas.tag_bind(item, "<Leave>", on_leave)

    return btn_id, text_id


# --- UI ---
window = Tk()
# --- Center the Window ---
window_width = 859
window_height = 534

# Get screen width and height
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Calculate x and y coordinates
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))

# Set the new geometry
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

window.geometry("859x534")
window.title("Forgot Password")
window.configure(bg="#FFFFFF")

canvas = Canvas(window, bg="#FFFFFF", height=539, width=872, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

canvas.create_rectangle(21.0, 17.0, 850.0, 521.0, fill="#FFFFFF", outline="#000000", width=2)
canvas.create_rectangle(21.0, 17.0, 850.0, 102.0, fill="#000000", outline="")
canvas.create_rectangle(240.0, 43.0, 746.0, 508.0, fill="#FFFFFF", outline="#000000", width=1.3)

canvas.create_text(361.0, 84.0, anchor="nw", text="Forgot Password", fill="#000000", font=("Inter Bold", -32))
canvas.create_text(298.0, 165.0, anchor="nw", text="Email", fill="#000000", font=("Inter", -16))
canvas.create_text(298.0, 218.0, anchor="nw", text="Verification", fill="#000000", font=("Inter", -16))
canvas.create_text(298.0, 269.0, anchor="nw", text="Password", fill="#000000", font=("Inter", -16))
canvas.create_text(253.0, 322.0, anchor="nw", text="Confirm Password", fill="#000000", font=("Inter", -16))

# --- Rounded Buttons ---
create_rounded_button(650, 160, "Get Code", on_get_code, width=80, height=30)
create_rounded_button(650, 215, "Send", on_send_code, width=80, height=30)
create_rounded_button(270, 450, "Back", go_back, width=80, height=30)
create_rounded_button(445, 380, "Reset Password", lambda: reset_password(current_email), width=180, height=40)

# --- Entries ---
entry_email, _ = create_rounded_entry(400, 155)
entry_verification, _ = create_rounded_entry(400, 208)
entry_new_password, _ = create_rounded_entry(400, 259, placeholder="New Password", show_char="*", with_eye=True)
entry_confirm_password, _ = create_rounded_entry(400, 312, placeholder="Confirm Password", show_char="*", with_eye=True)

window.resizable(False, False)
window.mainloop()
