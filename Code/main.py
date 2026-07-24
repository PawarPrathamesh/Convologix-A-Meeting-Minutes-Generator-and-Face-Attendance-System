import tkinter as tk
from tkinter import filedialog, messagebox
import os
import ConvoLogix as cl
import DetectFaces as Df
import SaveSummary as ss
import send_mail_ui as smui
from UserRegistrationGUI import UserRegistrationGUI 

def browse_file():
    global selected_file_path, flag, file_name
    file_path = filedialog.askopenfilename(title="Select a file")
    if file_path:
        selected_file_path = file_path
        file_name = os.path.basename(selected_file_path)
        if selected_file_path.endswith(".mp4"):
            flag = 1
            messagebox.showinfo("Success", "File selected successfully!")
        else:
            messagebox.showerror("Error","Please Select a MP4 File")
    else:
        flag = 0
        messagebox.showerror("Error","Please Select a File")
        

def generate_summary_and_email_ui():
    global selected_file_path
    if flag == 0:
        messagebox.showerror("Error", "Please select a file first!")
        return

    # Generate summary
    summary = cl.Convologix11("", selected_file_path)
    Df.capture_screenshots(selected_file_path, r"D:/ConvoLogix-Project/Video ScreenShots")
    attendance = Df.mark_attendance()

    # Show summary generated message
    messagebox.showinfo("Success", "Summary generated successfully!")

    ss.append_summary_to_file(summary,attendance,file_name)
    # Open email sending UI
    smui.send_email_window(file_name)

def register_new_user():
    # Create and display the registration GUI
    #registration_window = tk.Toplevel(root)
    # registration_window.title("User Registration")
    # registration_gui = UR(registration_window)
    registration_window = tk.Toplevel()
    registration_window.title("User Registration")
    registration_gui = UserRegistrationGUI(registration_window)
    #UR.main

root = tk.Tk()
root.title("File Browser")
window_width = 400
window_height = 200
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

browse_button = tk.Button(root, text="Browse Files", command=browse_file)
browse_button.pack(pady=10)

generate_summary_button = tk.Button(root, text="Generate Summary ", command=generate_summary_and_email_ui)
generate_summary_button.pack(pady=10)

register_user_button = tk.Button(root, text="Register New User", command=register_new_user)
register_user_button.pack(pady=10)

root.mainloop()
