import cv2
import numpy as np
import os

# Load the pre-trained LBPHFaceRecognizer model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('D:/ConvoLogix-Project/Trained Model/Trainer.yml')

# Function to evaluate the LBPHFaceRecognizer model
def evaluate_lbph_model(recognizer, testing_data_dir):
    correct_predictions = 0
    total_predictions = 0
    class_id_map = {}  # Mapping dictionary for class folder names to class IDs
    current_class_id = 0  # Current class ID

    # Iterate through each class folder in the testing data directory
    for class_folder in os.listdir(testing_data_dir):
        class_folder_path = os.path.join(testing_data_dir, class_folder)

        # Add the class folder name to the mapping dictionary with a unique class ID
        class_id_map[class_folder] = current_class_id
        current_class_id += 1

        # Iterate through each image in the class folder
        for image_name in os.listdir(class_folder_path):
            image_path = os.path.join(class_folder_path, image_name)
            face_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            # Perform face recognition
            predicted_class_id, _ = recognizer.predict(face_image)

            # Check if prediction matches the ground truth
            if predicted_class_id == class_id_map[class_folder]:
                correct_predictions += 1
            total_predictions += 1

    # Calculate accuracy
    accuracy = float(correct_predictions / total_predictions)
    return accuracy

# Specify the path to your testing data directory
testing_data_dir = 'D:/ConvoLogix-Project/Test Accuracy'

# Evaluate the LBPHFaceRecognizer model
accuracy = evaluate_lbph_model(recognizer, testing_data_dir)

# Print the accuracy
print("Accuracy:", accuracy)
