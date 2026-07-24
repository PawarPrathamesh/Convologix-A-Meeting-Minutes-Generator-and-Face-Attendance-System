import cv2
import os
import numpy as np
from moviepy.editor import VideoFileClip
import imageio

def get_class_names(dataset_dir):
    class_names = {}
    for idx, class_folder in enumerate(os.listdir(dataset_dir)):
        class_names[idx] = class_folder
    return class_names

def mark_attendance():
    attendance = []
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('D:/ConvoLogix-Project/Trained Model/Trainer.yml')

    class_names = get_class_names('D:/ConvoLogix-Project/Dataset')

    for j in range(0, 10):
        img = cv2.imread(f'D:/ConvoLogix-Project/Video ScreenShots/screenshot_{j}.jpg')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier('D:/ConvoLogix-Project/Required Files/haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            for i, (x, y, w, h) in enumerate(faces):
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 2)
                face = gray[y:y+h, x:x+w]
                face_id, confidence = recognizer.predict(face)
                # Check if confidence is within a certain threshold for accurate prediction
                if confidence > 78:  # Assuming a confidence threshold of 78
                    # Append class name instead of class ID
                    attendance.append(class_names.get(face_id, "Unknown"))
                    print(f"Face {i} recognized as {class_names.get(face_id, 'Unknown')} with confidence {confidence}")
                else:
                    attendance.append("Unknown")
                    print(f"Face {i} not recognized with confidence {confidence}")
    attendance=list(set(attendance))
    print(attendance)
    return attendance

def capture_screenshots(input_video, output_folder, num_screenshots=10):
    clip = VideoFileClip(input_video)
    duration = clip.duration
    fps = clip.fps

    interval = duration/num_screenshots # Capture screenshot per minute

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for t in range(0, 10):
       # screenshot_time = t + interval / 2  # Capture the frame at the middle of the interval
        frame = clip.get_frame(t*interval)
        output_path = f"{output_folder}/screenshot_{t}.jpg"
        imageio.imwrite(output_path, frame)
        print(f"Saved screenshot at {t} seconds: {output_path}")


