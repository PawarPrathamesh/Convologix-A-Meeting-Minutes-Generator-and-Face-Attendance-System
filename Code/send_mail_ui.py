import tkinter as tk
from tkinter import messagebox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime

def send_email(sender_email, sender_password, receiver_email, subject, body, file_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach body
        msg.attach(MIMEText(body, 'plain'))

        # Attach file
        if file_path:
            attachment = open(file_path, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % file_path)
            msg.attach(part)

        # Connect to SMTP server and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        messagebox.showinfo("Success", "Email sent successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send email: {str(e)}"+receiver_email)

def send_email_window(file_name):
    def send():
        current_date = datetime.datetime.now().strftime("%D-%m-%Y")
        sender_email = "convologix11@gmail.com"  
        sender_password = "ihfmwfpbotkkkdcd"  
        receiver_email = email_entry.get()
        subject = "Meeting Summary"
        body = "Minutes of Meeting: "+current_date
        fp=f"D:/ConvoLogix-Project/Minutes of Meeting/meeting_summary_{file_name}.txt" 
        file_path = fp
        send_email(sender_email, sender_password, receiver_email, subject, body, file_path)

    window = tk.Tk()
    window.title("Send Email")
    window.geometry("300x150")

    email_label = tk.Label(window, text="Email ID:")
    email_label.pack()

    email_entry = tk.Entry(window)
    email_entry.pack()

    send_button = tk.Button(window, text="Send Email", command=send)
    send_button.pack()

    window.mainloop()
