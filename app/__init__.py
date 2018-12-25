import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config.from_object('config')
app.config.from_pyfile('../config.py')
# path for images from platform photos
app.config['MEDIA_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'datasets')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['IDR'] = None

app.config['DGW'] = None
app.config['TRAINER'] = None

db = SQLAlchemy(app)

from web.app import controllers, models

if __name__ == '__main__':
    app.run()
