import tkinter as tk
import cv2
import os

class UserRegistrationGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("User Registration")
        
        # Labels and entry fields for user information
        tk.Label(master, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(master)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Button to start capturing images
        self.capture_button = tk.Button(master, text="Capture Images", command=self.capture_images)
        self.capture_button.grid(row=1, columnspan=2, pady=10)
        
        # OpenCV camera setup
        self.cap = cv2.VideoCapture(0)
        self.current_image = 0
        
    def capture_images(self):
        name = self.name_entry.get().strip()
        if name == "":
            tk.messagebox.showerror("Error", "Please enter a name.")
            return
        
        # Create a directory to save images if it doesn't exist
        output_dir = f"D:/ConvoLogix-Project/Dataset/{name}"
        os.makedirs(output_dir, exist_ok=True)
        
        while self.current_image < 100:
            ret, frame = self.cap.read()
            if not ret:
                tk.Message("Error", "Failed to capture image.")
                return
            
            # Convert image to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect face and crop it
            # (Code for face detection and cropping goes here)
            
            # Save cropped face image
            image_path = f"{output_dir}/face_{self.current_image}.jpg"
            cv2.imwrite(image_path, gray_frame)
            self.current_image += 1
            
            # Display the image in a window (optional)
            cv2.imshow("Captured Face", gray_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        tk.Message("Success", "Images captured successfully.")
        

def main():
    root = tk.Tk()
    app = UserRegistrationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
