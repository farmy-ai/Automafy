# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connectedto a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image
import cv2
import os
import uuid
import imgcompare
import numpy as np
import serial
from serial import Serial
from PIL import Image


# gstreamer_pipeline returns a GStreamer pipeline for capturingfrom the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0and 2)
# display_width and display_height determine the size of the windowon the screen

_DELAY_ = 30
_CLASS_ = 'class_3/'
_IMAGE_DIR_PATH_ = 'dataset/'+_CLASS_
#arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=640,
    framerate=50,
    flip_method=1,
    
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d,format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
        capture_width,
        capture_height,
        framerate,
        flip_method,
        display_width,
        display_height,
        )
     )

def main():
    # Create folders
    try:
        #os.mkdir('dataset')
        os.mkdir(_IMAGE_DIR_PATH_)
    except:
        print("Already exist")

    return True


def filter(current_image, past_image):
    """ TRY 1 """
    # # --- take the absolute difference of the images ---
    # res = cv2.absdiff(current_image, past_image)

    # # --- convert the result to integer type ---
    # res = res.astype(np.uint8)

    # # --- find percentage difference based on number of pixels that are not zero ---
    # percentage = (np.count_nonzero(res) * 100) / res.size

    """ TRY 2 """

    current_image = Image.fromarray(current_image, 'RGB')
    past_image = Image.fromarray(past_image, 'RGB')

    # --- take the absolute difference of the images ---
    percentage = imgcompare.image_diff_percent(current_image, past_image)

    print(percentage)

    return percentage < 16

def test():
    
    print("hi")
    #time.sleep(0.1)
    arduino.write(b'1')
        

def save_image(image):

    filename = str(uuid.uuid4())

    dir = os.path.abspath(os.getcwd())
    print(dir)

    path = os.path.join(_IMAGE_DIR_PATH_ + filename + ".png")
    print(path)

    cv2.imwrite(path, image)


def show_camera():

    # select Stream to collect from
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0),cv2.CAP_GSTREAMER)

    if cap.isOpened():

        # Init past image
        ret_val, past_image = cap.read()

        # Create window
        cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)

        # Start video & exit on window close
        while cv2.getWindowProperty("CSI Camera", 0) >= 0:

            # get image
            ret_val, img = cap.read()

            # show image to window
            cv2.imshow("CSI Camera", img)

            # if image pass filter
            if(filter(img, past_image)):
                #test()
                #save_image(img)
                #print("hello")

            # This also acts as delay
            keyCode = cv2.waitKey(_DELAY_) & 0xFF

            # Stop the program on the ESC key
            if keyCode == 27:
                break

        # Clear objects
        cap.release()
        cv2.destroyAllWindows()

    else:
        print("Unable to open camera")


if __name__ == "__main__":
    main()
    show_camera()
