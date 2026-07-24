import cv2
import numpy as np
import os

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

# Calculate accuracy
def evaluate_model(recognizer, testing_data_dir):
    correct_predictions = 0
    total_predictions = 0
    
    # Iterate through each class folder in the testing data directory
    for class_folder in os.listdir(testing_data_dir):
        class_folder_path = os.path.join(testing_data_dir, class_folder)
        
        # Get the name of the individual from the folder name
        individual_name = class_folder
        
        # Iterate through each image in the class folder
        for image_name in os.listdir(class_folder_path):
            image_path = os.path.join(class_folder_path, image_name)
            face_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            # Perform face recognition
            predicted_class_id, _ = recognizer.predict(face_image)
            
            # Check if prediction matches the ground truth
            if predicted_class_id == IDs[total_predictions]:
                correct_predictions += 1
            total_predictions += 1
    
    # Calculate accuracy
    accuracy = correct_predictions / total_predictions
    return accuracy

# Evaluate the model
accuracy = evaluate_model(recognizer, dataset_path)

# Print the accuracy
print("Accuracy:", accuracy)

# Prompt user whether to save the model or not
save_model = input("Do you want to save the trained model? (0/1): ").lower()

# If user wants to save the model, prompt for path and save it
if save_model == "1":
    save_path = "D:/ConvoLogix-Project/Trained Model/Trainer.yml"
    recognizer.save(save_path)
    print("Trained model saved successfully at", save_path)
else:
    print("Trained model not saved.")

cv2.destroyAllWindows()
print("Training Completed.")
