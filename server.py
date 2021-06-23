from flask import Flask, render_template, Response, request
from flask.wrappers import Response
import cv2
import base64
import numpy as np
import _thread
import uuid
import shutil
import os
import zipfile
import time
from io import BytesIO
from jetson_camera import main as jetson_main

app = Flask(__name__, static_folder='template', template_folder='template')

is_alive = True
is_terminate = False
statistics = []

# CLIENT SIDE ENDPOINTS


def gen_frames():

    while True:

        try:
            global frame

            decoded = base64.decodebytes(frame)
            np_decoded = np.frombuffer(decoded, dtype=np.uint8)
            np_decoded = np_decoded.reshape(480, 640, 3)

            ret, buffer = cv2.imencode('.jpg', np_decoded)

            np_decoded = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + np_decoded + b'\r\n')  # concat frame one by one and show result
        except Exception as e:
            print(e)
            break


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/stats', methods=['GET'])
def stats():
    global statistics
    r = {"statistics": statistics}
    return r, 200


@app.route('/power', methods=['POST'])
def power():

    global is_alive

    is_alive = request.json['alive']

    return Response("{ }", status=201, mimetype='application/json')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# MODEL UPLOAD ENDPOINTS


def unzip_file(zip_src, dst_dir):
    """
    Unzip the zip file
         :param zip_src: full path of zip file
         :param dst_dir: the destination folder to extract to
    :return:
    """
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, "r")
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        return "Please upload zip file"

@app.route("/upload", methods=["POST"])
def upload():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    obj = request.files.get("file")
    print(obj)  # <FileStorage: "test.zip" ("application/x-zip-compressed")>
    print(obj.filename)  # test.zip

    # Check if the suffix name of the uploaded file is zip
    ret_list = obj.filename.rsplit(".", maxsplit=1)
    if len(ret_list) != 2:
        return "Please upload zip file"
    if ret_list[1] != "zip":
        return "Please upload zip file"

    # Kill current jetson thread
    global is_terminate
    is_terminate = True
    # safe time to make sure the thread is dead 😵
    time.sleep(1)

    # Method three: Save the compressed file locally, then decompress it, and then delete the compressed file
    file_path = os.path.join(BASE_DIR, "assets", obj.filename) # The path where the uploaded file is saved
    obj.save(file_path)
    target_path = os.path.join(BASE_DIR, "assets") # The path where the unzipped files are saved
    ret = unzip_file(file_path, target_path)
    os.remove(file_path) # delete file
    if ret:
        return ret
    else:
        
        is_terminate = False
        t = _thread.start_new_thread(jetson_main, ())

        return 'DONE'
    

# JETSON SIDE ENDPOINTS

@app.route('/is_alive', methods=['GET'])
def alive():
    global is_alive
    global is_terminate
    r = {"alive": is_alive, 'terminate': is_terminate}
    return r, 200


@app.route('/send_frame', methods=['POST'])
def send_frame():

    global frame
    frame = request.data

    return Response("{ }", status=201, mimetype='application/json')


@app.route('/send_anomaly', methods=['POST'])
def send_anomaly():

    global statistics
    statistics.append(request.json)

    return Response("{ }", status=201, mimetype='application/json')


if __name__ == '__main__':
    # Create two threads as follows
    try:
        t = _thread.start_new_thread(jetson_main, ())

    except:
        print("Error: unable to start thread")

    app.run(host="0.0.0.0", debug=True)
