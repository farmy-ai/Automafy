# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connectedto a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image
from datetime import date
from model import predict_one_image, setup
import cv2
import os
import uuid
import imgcompare
import numpy as np
import base64
from datetime import datetime

# import serial
# from serial import Serial
from PIL import Image
import requests

# gstreamer_pipeline returns a GStreamer pipeline for capturingfrom the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0and 2)
# display_width and display_height determine the size of the windowon the screen

_DELAY_ = 30
_CLASS_ = 'class_3/'
_IMAGE_DIR_PATH_ = 'dataset/'+_CLASS_
# arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)


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
        # os.mkdir('dataset')
        os.mkdir(_IMAGE_DIR_PATH_)
    except:
        print("Already exist")

    return True


def do_somthing():
    return


def filter(current_image, past_image):
    """ 1st TRY"""
    # # --- take the absolute difference of the images ---
    # res = cv2.absdiff(current_image, past_image)

    # # --- convert the result to integer type ---
    # res = res.astype(np.uint8)

    # # --- find percentage difference based on number of pixels that are not zero ---
    # percentage = (np.count_nonzero(res) * 100) / res.size

    """ 2nd TRY """

    current_image = Image.fromarray(current_image, 'RGB')
    past_image = Image.fromarray(past_image, 'RGB')

    # --- take the absolute difference of the images ---
    percentage = imgcompare.image_diff_percent(current_image, past_image)

    print(percentage)

    return percentage < 16


def save_image(image):

    filename = str(uuid.uuid4())

    dir = os.path.abspath(os.getcwd())

    path = os.path.join(_IMAGE_DIR_PATH_ + filename + ".png")

    cv2.imwrite(path, image)


def send_frame(img):

    print('send frame next')

    encoded_image = base64.b64encode(img)

    try:
        requests.post(
            "http://127.0.0.1:5000/send_frame", data=encoded_image, timeout=5)
    except Exception as e:
        print(e)


def show_camera():

    # select Stream to collect from
    # cap = cv2.VideoCapture(gstreamer_pipeline(
    #     flip_method=0), cv2.CAP_GSTREAMER)
    cap = cv2.VideoCapture(0)

    if cap.isOpened():

        # Init past image
        ret_val, past_image = cap.read()

        prediction_results = []

        # Start video & exit on window close
        while True:

            # check if model enabled
            res = {'alive': True}
            try:
                res = requests.get('http://127.0.0.1:5000/is_alive').json()
            except:
                pass

            if not res['alive']:
                cv2.waitKey(_DELAY_)
                continue

            # get image
            ret_val, img = cap.read()

            print('send frame next')
            # send frame to server
            send_frame(img)

            detected_crop = filter(img, past_image)

            # first scenario : crop detected
            if(detected_crop):
                # Pass image through model
                frame_prediction_result = predict_one_image(img)

                prediction_results.append(frame_prediction_result[0])

                print('detected')

            elif(not detected_crop and len(prediction_results) > 0):

                midian_prediction = []

                for i in range(len(prediction_results[0])):

                    midian = 0

                    for p in range(len(prediction_results)):
                        midian = midian + prediction_results[p][i]

                    midian = midian / len(prediction_results[0])

                    midian_prediction.append(midian)

                print('-------------------------------------')
                print('-------------------------------------')
                print('Final result')
                print(midian_prediction)
                print('-------------------------------------')
                print('-------------------------------------')

                try:
                    requests.post('http://127.0.0.1:5000/send_anomaly',
                                  json={"prediction": midian_prediction, "time": datetime.now().time()}, timeout=5)
                except:
                    pass

                """ INJECT YOUR CODE HERE """
                # move jetson motors
                do_somthing()
                """ END INJECTION """

                prediction_results.clear()

            cv2.waitKey(_DELAY_)

        # Clear objects
        cap.release()

    else:
        print("Unable to open camera")


if __name__ == "__main__":
    main()
    setup(tensorflow_model_path='assets/Tensorflow_model')

    show_camera()
