from sqlalchemy.orm import validates
from sqlalchemy import event
import transliterate
from transliterate import detect_language, translit

from web.app import db
from web.app.serverside.serverside_table import ServerSideTable
from web.app.serverside import table_schemas


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    manufacturer = db.Column(db.String(100))
    amount = db.Column(db.Integer, default=0)
    mg_content = db.Column(db.SmallInteger, default=0)
    ml_volume = db.Column(db.SmallInteger, default=0)
    release_form = db.Column(db.String(100))
    width = db.Column(db.Integer)
    length = db.Column(db.Integer)
    height = db.Column(db.Integer)
    barcode = db.Column(db.String(100))
    train_status = db.Column(db.SmallInteger)
    timestamp = db.Column(db.DateTime)
    unique_name = db.Column(db.String(140))

    def __init__(self, form):
        self.name = form['name']
        self.width = form['width']
        self.height = form['height']
        self.length = form['length']
        self.manufacturer = form['manufacturer']
        self.amount = form['amount']
        self.release_form = form['release_form']
        self.mg_content = form['mg_content']
        self.ml_volume = form['ml_volume']
        self.barcode = form['barcode']
        self.unique_name = self.translite_string()
        self.train_status = 0

    @validates('amount', 'mg_content', 'ml_volume')
    def validate_name(self, key, value):
        if value == '':
            value = 0
        return value

    def __repr__(self):
        return '<Package %r>' % (self.name)

    def save_changes(self, form, new=False):
        """
        Save the changes to the database
        """
        # Get data from form and assign it to the correct attributes
        # of the SQLAlchemy table object

        self.name = form['name']
        self.width = form['width']
        self.height = form['height']
        self.length = form['length']
        self.manufacturer = form['manufacturer']
        self.amount = form['amount']
        self.release_form = form['release_form']
        self.mg_content = form['mg_content']
        self.ml_volume = form['ml_volume']
        self.barcode = form['barcode']
        self.unique_name = self.translite_string()

        # utilities.change_folder_name(self.barcode, utilities.DATASET_NEW_NAME)
        if new:
            # Add the new album to the database
            db.session.add(self)

        # commit the data to the database
        db.session.commit()

    def translite_string(self):
        language = detect_language(self.name)
        print(language)
        # ru uk
        # translite_string = translit(self.name, 'uk', reversed=True)
        try:
            translite_string = translit(self.name, language, reversed=True)
        except transliterate.exceptions.LanguageDetectionError:
            translite_string = self.name
        translite_string = translite_string.lower()
        exists_package = Package.get_by_unique(translite_string)
        # check dataset path folder
        if exists_package:
            translite_string += str(self.barcode)
        result = translite_string.replace(' ', '_').lower()
        return result

    @staticmethod
    def get_by_unique(name):
        model = db.session.query(Package).filter_by(unique_name=name).first()
        return model

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'barcode': self.barcode,
            'release_form': self.release_form,
            'amount': self.amount,
            'mg_content': self.mg_content,
            'ml_volume': self.ml_volume,
            'train_status': self.train_status,
        }

    @staticmethod
    def make_data_packages_from_db():
        newlist = []
        for row in Package.query.all():
            newlist.append(row.serialize)
        return newlist


# standard decorator style
@event.listens_for(Package, 'before_delete')
def receive_before_delete(mapper, connection, target):
    print(target)
    print(connection)
    print(mapper)


event.listen(Package, 'before_delete', receive_before_delete)


class TableBuilder(object):

    def collect_data_clientside(self):
        return {'data': Package.make_data_packages_from_db()}

    @staticmethod
    def collect_data_serverside(request):
        columns = table_schemas.SERVERSIDE_TABLE_COLUMNS
        data = Package.make_data_packages_from_db()
        result = ServerSideTable(request, data, columns).output_result()
        return result


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    value = db.Column(db.String(140))

    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value

    def __repr__(self):
        return '<Setting %r>' % (self.name)

    @staticmethod
    def init_setting_model(name, value):
        s = Setting(name, value)
        db.session.add(s)
        db.session.commit()
        return s

    @staticmethod
    def get_by_name(name):
        setting = db.session.query(Setting).filter_by(name=name).first()
        return setting

    def change_value(self, value):
        """
        Save the changes to the database
        """
        # Get data from form and assign it to the correct attributes
        # of the SQLAlchemy table object

        self.value = value
        # commit the data to the database
        db.session.commit()
