from sklearn.model_selection import train_test_split
import os

# Define the path to your dataset directory
dataset_dir = 'D:\ConvoLogix-Project\Training'

# Create lists to store image paths and corresponding labels
image_paths = []
labels = []

# Iterate over class folders
for class_name in os.listdir(dataset_dir):
    class_dir = os.path.join(dataset_dir, class_name)

    # Iterate over images in class folder
    for filename in os.listdir(class_dir):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            # Append image path and label to lists
            image_path = os.path.join(class_dir, filename)
            image_paths.append(image_path)
            labels.append(class_name)

# Split the data into training and testing sets
train_image_paths, test_image_paths, train_labels, test_labels = train_test_split(
    image_paths, labels, test_size=0.2, random_state=42)

# Printing the number of images in training and testing sets
print("Number of images in training set:", len(train_image_paths))
print("Number of images in testing set:", len(test_image_paths))
# for i in range(len(labels)):
#     print(image_paths[i]+"######"+labels[i])