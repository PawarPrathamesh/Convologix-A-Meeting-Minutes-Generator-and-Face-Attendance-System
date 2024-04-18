import os
import datetime

# Function to append summary and list of present staff to a file named based on current date
def append_summary_to_file(summary, present_staff,file_name):

    current_date = datetime.datetime.now().strftime("%d-%m-%y")
    filename = os.path.join("D:/ConvoLogix-Project/Minutes of Meeting", f"meeting_summary_{file_name}.txt")
    with open(filename, "a") as file:
        file.write("Summary:\n")
        file.write(summary + "\n\n")
        file.write("Present Staff:\n")
        for staff in present_staff:
            file.write(staff + "\n")
        file.write("\n")
