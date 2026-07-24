import os
from sklearn.model_selection import train_test_split
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPool2D, Flatten, Dense
import time

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
import os
import random
import shutil
import time
import pickle
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPool2D, Flatten, Dense
from keras.layers import Dropout
# # Path to your dataset directory
# dataset_dir = 'D:/ConvoLogix-Project/Photos'
# # Define the ratio for splitting the dataset
# train_ratio = 0.8
# test_ratio = 0.2

# # Get the list of all class folders
# class_folders = os.listdir(dataset_dir)

# # Create training and testing directories if they don't exist
# train_dir = 'D:/ConvoLogix-Project/Training'
# test_dir = 'D:/ConvoLogix-Project/Testing'
# os.makedirs(train_dir, exist_ok=True)
# os.makedirs(test_dir, exist_ok=True)

# # Iterate over class folders
# for class_folder in class_folders:
#     class_path = os.path.join(dataset_dir, class_folder)
#     images = os.listdir(class_path)
#     random.shuffle(images)
#     # Calculate split points
#     train_split = int(train_ratio * len(images))
#     test_split = int(test_ratio * len(images))
    
#     # Split images into training and testing sets
#     train_images = images[:train_split]
#     test_images = images[train_split:train_split + test_split]

#     # Move images to training directory
#     train_class_dir = os.path.join(train_dir, class_folder)
#     os.makedirs(train_class_dir, exist_ok=True)
#     for image in train_images:
#         src = os.path.join(class_path, image)
#         dst = os.path.join(train_class_dir, image)
#         shutil.copyfile(src, dst)
    
#     # Move images to testing directory
#     test_class_dir = os.path.join(test_dir, class_folder)
#     os.makedirs(test_class_dir, exist_ok=True)
#     for image in test_images:
#         src = os.path.join(class_path, image)
#         dst = os.path.join(test_class_dir, image)
#         shutil.copyfile(src, dst)

# print("Dataset split into training and testing sets successfully.")

# Specifying the folder where images are present
TrainingImagePath = 'D:/Trydataset'

# Defining pre-processing transformations on raw images of training data
train_datagen = ImageDataGenerator(
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True)

# Defining pre-processing transformations on raw images of testing data
test_datagen = ImageDataGenerator()

# Generating the Training Data
training_set = train_datagen.flow_from_directory(
    TrainingImagePath,
    target_size=(64, 64),
    batch_size=32,
    class_mode='categorical')

# Generating the Testing Data
test_set = test_datagen.flow_from_directory(
    'D:/ConvoLogix-Project/Test Accuracy',
    target_size=(64, 64),
    batch_size=32,
    class_mode='categorical')

# Printing class labels for each face
test_set.class_indices

# Creating lookup table for all faces
TrainClasses = training_set.class_indices

# Storing the face and the numeric tag for future reference
ResultMap = {}
for faceValue, faceName in zip(TrainClasses.values(), TrainClasses.keys()):
    ResultMap[faceValue] = faceName

# Saving the face map for future reference
with open("ResultsMap.pkl", 'wb') as fileWriteStream:
    pickle.dump(ResultMap, fileWriteStream)

# The number of neurons for the output layer is equal to the number of faces
OutputNeurons = len(ResultMap)
#####################
# # Initializing the Convolutional Neural Network
# classifier = Sequential()

# # Adding the first layer of CNN
# classifier.add(Convolution2D(32, kernel_size=(5, 5), strides=(1, 1), input_shape=(64, 64, 3), activation='relu'))

# # MAX Pooling
# classifier.add(MaxPool2D(pool_size=(2, 2)))

# # ADDITIONAL LAYER of CONVOLUTION for better accuracy
# classifier.add(Convolution2D(64, kernel_size=(5, 5), strides=(1, 1), activation='relu'))
# classifier.add(MaxPool2D(pool_size=(2, 2)))

# # FLattening
# classifier.add(Flatten())

# # Fully Connected Neural Network
# classifier.add(Dense(64, activation='relu'))
# classifier.add(Dense(OutputNeurons, activation='softmax'))

# # Compiling the CNN
# classifier.compile(loss='categorical_crossentropy', optimizer='adam', metrics=["accuracy"])



# Initialize the Convolutional Neural Network
classifier = Sequential()

# Adding the first convolutional layer
classifier.add(Convolution2D(32, kernel_size=(3, 3), strides=(1, 1), input_shape=(64, 64, 3), activation='relu'))

# Adding a second convolutional layer
classifier.add(Convolution2D(64, kernel_size=(3, 3), strides=(1, 1), activation='relu'))

# Adding a third convolutional layer
classifier.add(Convolution2D(128, kernel_size=(3, 3), strides=(1, 1), activation='relu'))

# Adding a max pooling layer
classifier.add(MaxPool2D(pool_size=(2, 2)))

# Adding dropout for regularization
classifier.add(Dropout(0.25))

# Adding a fourth convolutional layer
classifier.add(Convolution2D(256, kernel_size=(3, 3), strides=(1, 1), activation='relu'))

# Adding a fifth convolutional layer
classifier.add(Convolution2D(512, kernel_size=(3, 3), strides=(1, 1), activation='relu'))

# Adding a max pooling layer
classifier.add(MaxPool2D(pool_size=(2, 2)))

# Adding dropout for regularization
classifier.add(Dropout(0.25))

# Flattening
classifier.add(Flatten())

# Adding the first fully connected layer
classifier.add(Dense(512, activation='relu'))

# Adding dropout for regularization
classifier.add(Dropout(0.5))

# Adding the output layer
classifier.add(Dense(OutputNeurons, activation='softmax'))

# Compiling the CNN
classifier.compile(loss='categorical_crossentropy', optimizer='adam', metrics=["accuracy"])


# Measuring the time taken by the model to train
StartTime = time.time()

# Starting the model training
classifier.fit(
    training_set,
    steps_per_epoch=training_set.samples // training_set.batch_size,
    epochs=10,
    validation_data=test_set,
    validation_steps=test_set.samples // test_set.batch_size)

EndTime = time.time()
print("Total Time Taken: ", round((EndTime - StartTime) / 60), 'Minutes')

# Evaluate the model on the testing set
evaluation = classifier.evaluate(test_set, steps=len(test_set))
print("#"*20)
# Print the evaluation results
print("Test Loss:", evaluation[0])
print("Test Accuracy 1:", evaluation[1])

print("#"*20)
print("#"*20)
# Evaluate the model on the testing set

accuracy = classifier.evaluate(
    test_set,
    steps=test_set.samples // test_set.batch_size)
print("Test Accuracy 2:", accuracy[1])





ask = input("Should I Save the model 1 or 0:-")

if ask == "1":
    # Saving the trained model

    classifier.save('D:/ConvoLogix-Project/Trained Model/face_recognition_model.h5')
    print("Trained model saved to disk.")
else:
    print("Trained model Not Saved to disk.")
