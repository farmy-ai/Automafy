from flask import Flask, render_template, Response, request
from flask.wrappers import Response
import cv2
import base64
import numpy as np
import _thread
from io import BytesIO
from jetson_camera import main as jetson_main

app = Flask(__name__, static_folder='template', template_folder='template')

is_alive = True
statistics = []


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


@app.route('/is_alive', methods=['GET'])
def alive():
    global is_alive
    r = {"alive": is_alive}
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


@app.route('/power', methods=['POST'])
def power():

    global is_alive

    is_alive = request.json['alive']

    return Response("{ }", status=201, mimetype='application/json')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # Create two threads as follows
    try:
        _thread.start_new_thread(jetson_main, ())
    except:
        print("Error: unable to start thread")

    app.run(host="0.0.0.0", debug=True)
