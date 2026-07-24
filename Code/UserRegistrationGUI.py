import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os
import numpy as np

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
        
        # Button to train the model
        self.train_button = tk.Button(master, text="Train Model", command=self.train_model)
        self.train_button.grid(row=2, columnspan=2, pady=10)
        
        # OpenCV camera setup
        self.cap = cv2.VideoCapture(0)
        self.current_image = 0
        
        # Load the Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier('D:/ConvoLogix-Project/Required Files/haarcascade_frontalface_default.xml')
        
    def capture_images(self):
        name = self.name_entry.get().strip()
        if name== "":
            messagebox.showerror("Error", "Please enter a name.")
            return
        
        # Create a directory to save images if it doesn't exist
        output_dir = f"D:/ConvoLogix-Project/Dataset/{name}"
        os.makedirs(output_dir, exist_ok=True)
        
        while self.current_image < 500:
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture image.")
                #print("Error", "Failed to capture image.")
                return
            
            # Convert image to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces in the image
            faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (x, y, w, h) in faces:
                # Crop the detected face
                face_crop = gray_frame[y:y+h, x:x+w]
                
                # Save cropped face image
                image_path = f"{output_dir}/face_{self.current_image}.jpg"
                cv2.imwrite(image_path, face_crop)
                self.current_image += 1
                
                # Display the cropped face (optional)
                cv2.imshow("Cropped Face", face_crop)
            
            # Display the original image with rectangles around detected faces (optional)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.imshow("Original with Faces", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        #messagebox.Message("Success", "Images captured successfully.")
        cv2.destroyAllWindows()
        #print("Success", "Images captured successfully.")
    
    def train_model(self):
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        dataset_path = "D:/ConvoLogix-Project/Dataset"

        def get_image_data(dataset_path):
            faces = []
            ids = []
            class_id_map = {}  # Mapping dictionary for class folder names to class IDs
            
            # Iterate through each class folder
            for class_id, class_folder in enumerate(sorted(os.listdir(dataset_path))):
                class_folder_path = os.path.join(dataset_path, class_folder)
                class_id_map[class_folder] = class_id
                
                # Iterate through each image in the class folder
                for image_name in os.listdir(class_folder_path):
                    image_path = os.path.join(class_folder_path, image_name)
                    
                    # Read the image and convert it to grayscale
                    face_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                    
                    # Extract the class ID using the mapping dictionary
                    class_id = class_id_map[class_folder]
                    
                    # Append the face data and corresponding class ID
                    faces.append(face_image)
                    ids.append(class_id)
                    
                    # Display the training image (optional)
                    cv2.imshow("Training", face_image)
                    cv2.waitKey(1)
            
            return ids, faces

        IDs, facedata = get_image_data(dataset_path)

        # Train the recognizer
        recognizer.train(facedata, np.array(IDs))
        save_path = "D:/ConvoLogix-Project/Trained Model/Trainer.yml"
        recognizer.save(save_path)
        messagebox.showinfo("Success", "Model Trained")
        cv2.destroyAllWindows()

def main():
    root = tk.Tk()
    app = UserRegistrationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
