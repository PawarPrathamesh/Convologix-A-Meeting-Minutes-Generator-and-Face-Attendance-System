from moviepy.editor import VideoFileClip
import os
import imageio

def capture_screenshots(input_video, output_folder="D:/ConvoLogix-Project/Video ScreenShots", num_screenshots=10):
    """
    Capture screenshots from a given video file and save them as images in the specified folder.

    Parameters:
    - input_video (str): Path to the input video file.
    - output_folder (str): Path to the folder where screenshots will be saved. Default is "D:/ConvoLogix-Project/Video ScreenShots".
    - num_screenshots (int): Number of screenshots to capture. Default is 10.
    """
    # Load the video clip
    clip = VideoFileClip(input_video)

    # Calculate the duration and frame rate of the video
    duration = clip.duration
    clip.close()
    print(duration)
    fps = clip.fps

    # Calculate the interval between screenshots
    interval = duration / num_screenshots
    print(interval)
    
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Capture screenshots at regular intervals
    for e in range(0, 10):
        # Get the frame at the current time
        frame = clip.get_frame(interval*e)
        

        # Save the frame as an image file
        output_path = os.path.join(output_folder, f"screenshot_{e}.jpg")
        imageio.imwrite(output_path, frame)

        # Print the path of the saved screenshot
        print(f"Saved screenshot at {e} seconds: {output_path}")

# Example usage:
# capture_screenshots("input_video.mp4", output_folder="D:/ConvoLogix-Project/Video ScreenShots", num_screenshots=10)
