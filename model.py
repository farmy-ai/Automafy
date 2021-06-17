from statistics import mean
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input
from tensorflow.keras.preprocessing import image
import os
import time
import numpy as np
import tensorflow as tf


def setup(tensorflow_model_path):

    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

    INFERENCE_STEPS = 5  # 10000
    WARMUP_STEPS = 2  # 2000

    #gpus = tf.config.experimental.list_physical_devices('GPU')
    #tf.config.experimental.set_memory_growth(gpus[0], True)

    use_tftrt = False
    global model
    model = None
    if(use_tftrt == False):
        model = tf.saved_model.load(tensorflow_model_path)
    else:
        model = tf.saved_model.load(os.path.join(
            tensorflow_model_path, 'converted'))

    img_path = 'assets/images/image.jpeg'
    img = image.load_img(img_path, target_size=(224, 224))

    step_times = []
    for step in range(1, INFERENCE_STEPS + 1):
        start_t = time.time()
        result = predict_one_image(img)
        step_time = time.time() - start_t
        # print(step_time)
        print(step_time)
        if step >= WARMUP_STEPS:
            step_times.append(step_time)

    avg_step_time = mean(step_times)

    print("\nAverage step time: %.1f sec" % (avg_step_time * 1e3))

    for i in range(1, 4):
        img = image.load_img(img_path, target_size=(224, 224))

        start_t = time.time()
        result = predict_one_image(img)
        step_time = time.time() - start_t

        print(result)

        # print(result)
        #index_max = result.argmax(axis=-1)
        # print(index_max)

    print('end warmup')


def predict_one_image(image_example):

    img_array = image.img_to_array(image_example)
    img_batch = np.expand_dims(img_array, axis=0)
    img_preprocessed = preprocess_input(img_batch)
    img_preprocessed = tf.convert_to_tensor(img_preprocessed)

    global model

    infer = model.signatures['serving_default']
    output_tensorname = list(infer.structured_outputs.keys())[0]

    result = infer(img_preprocessed)[output_tensorname]

    return result.numpy()
