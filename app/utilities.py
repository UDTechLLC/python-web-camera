import os
import time
import uuid
import glob

from web.app import app
from web.app import db
from web.app.models import Setting
from cv.imagedata_recorder import ImageDataRecorder

from cv.uart_control import UartControl

DATASET_NEW_NAME = './datasets/raw/new'


def get_folder_images(folder_name, dataset_name):
    # image_list = map(Image.open, glob('.././data/images/' + folder_name + '/*.png'))
    # return image_list
    images_list = {}
    for img in glob.glob(dataset_name + '/' + folder_name + '/*.png'):
        first_step = img.rfind('_')
        key = img[(first_step+1):-4]
        if key[1:] == '0':
            # images_list.append(img[10:])
            # images_list[int(key[:1])] = img[10:]
            images_list[int(key[:1])] = img[11:]
    return images_list


def change_folder_name(name, dataset_name):
    setting_images = Setting.get_by_name('package_images')
    old_name = setting_images.value
    if os.path.isdir(dataset_name + '/' + old_name):
        os.rename(dataset_name + '/' + old_name, dataset_name + '/' + name)
    db.session.query(Setting).filter_by(name='package_images').delete()
    db.session.commit()


def random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.


def is_setting_exits(name):
    setting = Setting.get_by_name(name)
    if setting is None:
        return False
    if setting.value == '0':
        return False
    else:
        return True


def run_simple(width):
    recorder = ImageDataRecorder()
    recorder.set_width(width)
    recorder.start(0, 100)


def run_uart():
    uart = UartControl(debug=True)

    # first phase: 4 faces
    base_count = 5
    current_face = 1
    led = 100

    uart.enable_led(led)
    time.sleep(1)

    while current_face <= 1:
        time.sleep(8)
        uart.start_step(3200)
        time.sleep(8)

        current_face += 1

    while current_face <= 2:
        time.sleep(5)
        uart.start_step(1600)
        time.sleep(9)

        current_face += 1

    # while current_face <= 3:
    #
    #     time.sleep(5)
    #     uart.start_step(3200)
    #     time.sleep(8)
    #
    #     current_face += 1
    #
    # time.sleep(6)
    # uart.disable_led()
    # time.sleep(1)
    # uart.enable_led(led)
    # time.sleep(1)
    # # second phase: 2 faces
    # while current_face <= 5:
    #     time.sleep(5)
    #     # TODO: rotate 180
    #     uart.start_step(3200)
    #     time.sleep(8)
    #     current_face += 1
    uart.disable_led()


def run_algorithm(width):
    uart = UartControl(debug=True)

    setting_detect = Setting.init_setting_model('detect_package', random_string())

    # first phase: 4 faces
    base_count = 5
    current_face = 1
    app.config['IDR'].set_width(width)
    # with SpeakerManager() as speaker:
    #     speaker.say('Начинаем получение данных', 3)
    # uart.enable_led(led)
    # led = 20
    led = Setting.get_by_name('led')

    time.sleep(1)
    while current_face <= 4:
        # TODO:
        # uart.enable_led(led)
        if led:
            uart.enable_led(int(led.value))
        time.sleep(1)
        app.config['IDR'].start(current_face, base_count)

        time.sleep(4)

        if led:
            uart.disable_led()

        time.sleep(1)

        # TODO: rotate 90

        uart.start_step(1600)

        time.sleep(4)

        current_face += 1

    # how to wait: by keypress 's'
    # while not self._second_phase_activate:
    #    self._window_manager.process_events()

    # with SpeakerManager() as speaker:
    #     speaker.say('Переверните упаковку', 3)
    uart.disable_led()

    # Create option for change side - for ajax request from page
    change_option_side = Setting.init_setting_model('change_side', random_string())

    while is_setting_exits('change_side'):
        pass

    # uart.enable_led(led)
    if led:
        uart.enable_led(int(led.value))
    time.sleep(1)
    # second phase: 2 faces
    while current_face <= 6:
        # TODO:

        app.config['IDR'].start(current_face, base_count)

        time.sleep(4)

        # uart.disable_led()

        time.sleep(1)

        # TODO: rotate 180 if not last face
        if current_face != 6:
            uart.start_step(3200)
            time.sleep(8)

        current_face += 1

    uart.disable_led()

    images_count = app.config['IDR'].write_dataset(
        dataset_name=DATASET_NEW_NAME,
        class_name=setting_detect.value)
    print(images_count)

    Setting.init_setting_model('package_images', setting_detect.value)
    db.session.query(Setting).filter_by(name='detect_package').delete()
    db.session.query(Setting).filter_by(name='detect_thread').delete()
    db.session.query(Setting).filter_by(name='change_side').delete()
    db.session.commit()


def enable_led(value):
    uart = UartControl(debug=True)
    uart.enable_led(value)
    while True:
        pass


def disable_led():
    uart = UartControl(debug=True)
    uart.disable_led()
