from keras.models import load_model
from keras.preprocessing.image import ImageDataGenerator

# Check if GPU is available
import torch

if torch.cuda.is_available():
    device = torch.device("cuda")
    print('####'*10)
    print("Using GPU:", torch.cuda.get_device_name(0))
else:
    device = torch.device("cpu")
    print('####'*10)
    print("GPU not available, using CPU.")




# Load the pre-trained model
pretrained_model = load_model('D:/ConvoLogix-Project/Trained Model/face_recognition_model.h5')

# Specify the path to your testing data directory
testing_data_dir = 'D:/ConvoLogix-Project/Test Accuracy'

# Create an ImageDataGenerator for testing data
test_datagen = ImageDataGenerator()

# Generate testing data from the directory
test_generator = test_datagen.flow_from_directory(
        testing_data_dir,
        target_size=(64, 64),  # Set the target size of your images
        batch_size=32,
        class_mode='categorical',  # Set the class mode according to your model
        shuffle=False)  # Set shuffle to False to ensure correct order

# Evaluate the model on the testing data
evaluation = pretrained_model.evaluate(test_generator)

# Print the evaluation results
print("Test Loss:", evaluation[0])
print("Test Accuracy:", evaluation[1])
