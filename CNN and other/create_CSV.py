import os
import cv2
import pandas as pd
import torch

# Check if GPU is available
if torch.cuda.is_available():
    device = torch.device("cuda")
    print('####'*10)
    print("Using GPU:", torch.cuda.get_device_name(0))
else:
    device = torch.device("cpu")
    print('####'*10)
    print("GPU not available, using CPU.")


# Path to your dataset directory
dataset_dir = r'D:\ConvoLogix-Project\Training'

# Define class labels
class_labels = {'Anushka': 0, 'Prathamesh': 1, 'Shritej': 2, 'Swamini': 3, 'Unknown': 4}

# Create an empty DataFrame to store image paths and labels
df = pd.DataFrame(columns=['image_path', 'label'])
rows = []

# Iterate over class folders
for class_name, label in class_labels.items():
    class_dir = os.path.join(dataset_dir, class_name)

    # Iterate over images in class folder
    for filename in os.listdir(class_dir):
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.png'):
            # Read and process image
            image_path = os.path.join(class_dir, filename)
            image = cv2.imread(image_path)
            # Resize image if needed
            # image = cv2.resize(image, (width, height))
            # Convert image to grayscale or RGB if needed
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            rows.append({'image_path': image_path, 'label': label})

# Create DataFrame from the list of dictionaries
df = pd.DataFrame(rows)

# Specify the full path to store the CSV file
csv_file_path = r'D:\ConvoLogix-Project\CSV File\dataset.csv'

# Save DataFrame to CSV file
df.to_csv(csv_file_path, index=False)
print("CSV Created")
