from threading import Thread, enumerate
from flask import render_template, Response, jsonify, request, redirect, url_for, send_from_directory
import os
import time

from web.app import app
from cv.imagedata_recorder import ImageDataRecorder
from web.app import models, db, utilities
from web.app.models import Package, Setting, TableBuilder
from data.dataset_generator_web import DatasetGeneratorWeb
from train.dispatcher import prepare_train
from train.build_and_train import Trainer


@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['MEDIA_FOLDER'], filename, as_attachment=True)


@app.before_request
def before_request():
    # detecting package page opened, run algorithm with uart
    if utilities.is_setting_exits('detect_thread') and request.endpoint != 'detect_package_page':
        if (request.endpoint != 'detect_package_ajax') and \
                (request.endpoint != 'static') and \
                (request.endpoint != 'change_side_ajax') and \
                (request.endpoint != 'video_feed') and \
                (request.endpoint != 'platform_feed'):
            return redirect(url_for('detect_package_page'))
    # creation meta-data for package
    if utilities.is_setting_exits('package_images') and request.endpoint != 'show_package_form':
        if (request.endpoint != 'download_file') and (request.endpoint != 'static') and (
                request.endpoint != 'detect_package_ajax'):
            return redirect(url_for('show_package_form'))


@app.route("/")
def index():
    # setting = Setting.get_by_name('detect_package')
    # print(setting)
    # setting = Setting.get_by_name('package_images')
    # print(setting)
    packages = models.Package.query.all()
    return render_template('index.html',
                           packages=packages,
                           training_model=utilities.is_setting_exits('train_model')
                           )


@app.route("/start-video")
def start_video_content():
    if app.config['IDR'] is None:
        app.config['IDR'] = ImageDataRecorder()
    led_setting = Setting.get_by_name('led')
    if led_setting:
        led = int(led_setting.value)
        thread = Thread(target=utilities.enable_led, args=[led])
        thread.start()
    else:
        led = 10
    return render_template('start_video.html', led=led)


@app.route("/enable-led", methods=['POST'])
def enable_led_ajax():
    if request.method == "POST":
        data = request.get_json()
        led = data['led']
    else:
        led = 10
    thread = Thread(target=utilities.enable_led, args=[led])
    thread.start()
    led_setting = Setting.get_by_name('led')
    if led_setting:
        led_setting.change_value(str(led))
    else:
        led_setting = Setting.init_setting_model('led', str(led))
    return jsonify('enable led = ' + str(led))


@app.route("/disable-led", methods=['POST'])
def disable_led_ajax():
    utilities.disable_led()
    db.session.query(Setting).filter_by(name='led').delete()
    db.session.commit()
    return jsonify('disable')


@app.route("/train-model")
def train_model_method():
    setting = Setting.get_by_name('train_model')
    if setting is None:
        Setting.init_setting_model('train_model', 'train')
    else:
        setting.change_value('train')

    app.config['DGW'] = DatasetGeneratorWeb()
    app.config['TRAINER'] = Trainer()
    thread = Thread(target=generate_datasets, args=[])
    thread.start()
    # D_SETS_WEB.status = ...

    return render_template('train_page.html', dsw=app.config['DGW'])


def generate_datasets():
    # app.config['DGW'].rescale_dataset(source_dataset=os.path.join('./datasets', 'raw', 'new'),
    #                                   output_dataset=os.path.join('./datasets', 'rescaled', 'new'),
    #                                   scale=0.4)

    app.config['DGW'].augment_dataset(source_dataset=os.path.join('./datasets', 'rescaled', 'new'),
                                      dataset_count=30,
                                      augmented_per_class=300)

    # TODO: train dispatcher logic
    prepare_train(
        network_name='vgg',
        weights_path='/home/apteka/code/tensorflow/transfer-learning-food/data/vgg_19.ckpt',
        datasets='/home/apteka/code/apteka/prototype/package_entry/datasets/augmented/new',
        save_checkpoints_dir='/home/apteka/code/apteka/prototype/package_entry/checkpoints/test1',
        img_size=224,
        batch_size=32,
        epochs=10
    )


@app.route("/train-status", methods=['GET'])
def train_status_ajax():
    dgw = app.config['DGW']
    trainer = app.config['TRAINER']

    result = {}
    if dgw is not None and dgw.status is not 'END':
        result = {
            'operation': dgw.current_operation,
            'status': dgw.status,
            'step': dgw.step,
            'amount': dgw.amount
        }
    elif trainer is not None:
        result = {
            'operation': trainer.current_operation,
            'status': trainer.status,
            'step': trainer.step,
            'amount': trainer.amount
        }

    return jsonify(result)


@app.route("/export-model")
def export_model_method():
    return redirect(url_for('index'))


@app.route("/loading-page")
def loading_page():
    setting = Setting.get_by_name('train_model')
    if utilities.is_setting_exits('train_model'):
        if setting is not None:
            setting.change_value('0')
    else:
        setting.change_value('train')

    result_list = Package.query.filter_by(train_status=0).all()
    for package in result_list:
        package.train_status = 1

    db.session.commit()
    return render_template('loading_page.html')


@app.route("/detect-package", methods=['GET'])
def detect_package_page():
    detect = Setting.get_by_name('detect_thread')
    # if not setting with detect_thread - thread with algorithm not started
    if detect is None:
        width = request.args.get('width')
        if width is None:
            width = 100
        thread = Thread(target=utilities.run_algorithm, args=[width])
        thread.start()
        detect = Setting.init_setting_model('detect_thread', thread.ident)
    # thread with algorithm save in settings
    else:
        thread_stopped = True
        # check thread with algorithm - alive or not?
        for thread in enumerate():
            if thread.ident == int(detect.value):
                thread_stopped = False
        if thread_stopped:
            db.session.query(Setting).filter_by(name='detect_thread').delete()
            db.session.commit()
            return redirect(url_for('start_video_content'))

    return render_template('detect_package.html')


@app.route("/detect-package-ajax", methods=['GET'])
def detect_package_ajax():
    setting = Setting.get_by_name('detect_thread')
    side = Setting.get_by_name('change_side')
    if side:
        return jsonify('change side')
    if setting:
        return jsonify(setting.value)
    else:
        return jsonify('empty')


@app.route("/change-side-ajax", methods=['GET'])
def change_side_ajax():
    db.session.query(Setting).filter_by(name='change_side').delete()
    db.session.commit()
    return jsonify('success')


@app.route('/package-create', methods=['GET', 'POST'])
def show_package_form():
    if request.method == 'POST':
        package = Package(request.form)
        db.session.add(package)
        db.session.commit()
        print(package.unique_name)
        utilities.change_folder_name(package.unique_name, utilities.DATASET_NEW_NAME)
        return redirect(url_for('index'))
    # show the package form
    package = Package.__init__

    folder_name = Setting.get_by_name('package_images')
    if folder_name is not None:
        images_list = utilities.get_folder_images(folder_name.value, utilities.DATASET_NEW_NAME)
    else:
        images_list = None
    return render_template('package_form.html',
                           package=package,
                           images_list=images_list,
                           )


@app.route('/edit-package/<int:id>', methods=['GET', 'POST'])
def edit_package(id):
    # show the post with the given id, the id is an integer
    package = Package.query.get(id)
    if request.method == 'GET':
        folder_name = package.unique_name
        if folder_name is not None:
            images_list = utilities.get_folder_images(folder_name, utilities.DATASET_NEW_NAME)
        else:
            images_list = None
        return render_template('package_form.html',
                               package=package,
                               images_list=images_list
                               )

    elif request.method == 'POST':
        package.save_changes(request.form)
        return redirect(url_for('index'))


@app.route('/delete-package/<int:id>', methods=['DELETE'])
def delete_package(id):
    Package.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify(['success'])


def gen_video_frame(camera):
    while True:
        frame = camera.get_video_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    while app.config['IDR'] is None:
        time.sleep(0.1)

    return Response(gen_video_frame(app.config['IDR']),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_platform_frame(camera):
    while True:
        frame = camera.get_platform_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/platform_feed')
def platform_feed():
    while app.config['IDR'] is None:
        time.sleep(0.1)

    return Response(gen_platform_frame(app.config['IDR']),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/table_package_ajax", methods=['GET'])
def table_package_ajax_content():
    result = TableBuilder.collect_data_serverside(request)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
