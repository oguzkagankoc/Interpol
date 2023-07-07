import base64
import os
import time

import requests
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# Access variables
db_username = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')
# Create a Flask application instance
app = Flask(__name__)

# Configure the database connection URL
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Initialize a SQLAlchemy object
db = SQLAlchemy(app)

def perform_request(url):
    while True:
        try:
            response = requests.get(url, headers={}, data={})
            return response
        except requests.exceptions.RequestException:
            print("Internet connection lost. Trying to reconnect...")
            time.sleep(5)

# Define a model for the "personal_informations" table
class AppPersonalInformation(db.Model):
    __tablename__ = "personal_informations"
    entity_id = db.Column(db.String(20), primary_key=True, nullable=False)
    forename = db.Column(db.String(50))
    name = db.Column(db.String(50))
    sex_id = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    place_of_birth = db.Column(db.String(100))
    country_of_birth_id = db.Column(db.String(50))
    weight = db.Column(db.DECIMAL())
    height = db.Column(db.DECIMAL())
    distinguishing_marks = db.Column(db.String(1000))
    eyes_colors_id = db.Column(db.String(20))
    hairs_id = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, nullable=False)
    thumbnail = db.Column(db.Text)


# Define a model for the "language_informations" table
class AppLanguageInformation(db.Model):
    __tablename__ = "language_informations"
    language_id = db.Column('language_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    languages_spoken_id = db.Column('languages_spoken_id', db.String(20))
    personal_informations = db.relationship("AppPersonalInformation", backref="language", lazy=True,
                                            foreign_keys=[entity_id])


# Define a model for the "nationality_informations" table
class AppNationalityInformation(db.Model):
    __tablename__ = "nationality_informations"
    nationality_id = db.Column('nationality_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    nationality = db.Column('nationality', db.String(30))
    personal_informations = db.relationship("AppPersonalInformation", backref="nationality", lazy=True,
                                            foreign_keys=[entity_id])


# Define a model for the "picture_informations" table
class AppPictureInformation(db.Model):
    __tablename__ = "picture_informations"
    picture_id = db.Column('picture_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    picture_url = db.Column('picture_url', db.String(200))
    picture_base64 = db.Column('picture_base64', db.Text)
    personal_informations = db.relationship("AppPersonalInformation", backref="picture_of_the_criminal", lazy=True,
                                            foreign_keys=[entity_id])


# Define a model for the "change_log" table
class AppChangeAppLogInformation(db.Model):
    __tablename__ = "change_log"
    log_id = db.Column('log_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    table_name = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    description = db.Column(db.Text)
    change_date = db.Column(db.DateTime)
    personal_informations = db.relationship("AppPersonalInformation", backref="change_log", lazy=True,
                                            foreign_keys=[entity_id])


# Define a model for the "log" table
class AppLogInformation(db.Model):
    __tablename__ = "log"
    log_id = db.Column('log_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    table_name = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    column_data = db.Column(db.TEXT)
    description = db.Column(db.Text)
    personal_informations = db.relationship("AppPersonalInformation", backref="log", lazy=True,
                                            foreign_keys=[entity_id])


# Define a model for the "arrest_warrant_informations" table
class AppArrestWarrantInformation(db.Model):
    __tablename__ = "arrest_warrant_informations"
    arrest_warrant_id = db.Column('arrest_warrant_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey("personal_informations.entity_id"))
    issuing_country_id = db.Column('issuing_country_id', db.String(30))
    charge = db.Column('charge', db.String(1000))
    charge_translation = db.Column('charge_translation', db.String(1000))
    personal_informations = db.relationship("AppPersonalInformation", backref="arrest_warrant", lazy=True,
                                            foreign_keys=[entity_id])


class InterpolPerson:
    def __init__(self, person_url):
        # Initialize instance variables
        self.person_url = person_url
        self.personal_info_data = {}

    def _get_data(self):
        # Get data from the provided URL
        response = perform_request(self.person_url)
        data = response.json()

        # Get the person's image URL, retrieve the image and encode it to base64
        if "thumbnail" in data['_links'].keys():
            image_url = data['_links']['thumbnail']['href']
            image_response = perform_request(image_url)
            image_content = image_response.content
            image_base64 = base64.b64encode(image_content).decode("utf-8")
        else:
            image_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAKoAAACqAgMAAABAGDwRAAAADFBMVEWutLfk5ufb3d/EyMpaqx/2AAACUUlEQVRYw+3YK3LcQBAA0LZUBgJKkI8gHiLgoD3CAu1IVREQ3wU6gi6xPNQh2QMEzA2CdASDsFCTOJWsVur5dPeM7VTsKgm/mur5dfcIdsHfFla72tWudrVv0359/BFqTwDwEGYP8Oe7D7FK/7XvQux5WM/AHqsnm8u2mSikR9H2FwuFaPVsc8nWM4VUsu1iYRRsj2wpWI1sxluFKCS8rbBNeYunZk/Otp1hC9ZuDFuyVhs2Y61B4YqztWkTzlamTTnbmBaOjG0tOzJ2a9kbxnaWLRjbR9iNZcsIe83Y4Rk2Y6y2bP4fLLyxcV+jzV7oPMScs5iz3j/DFhH3+CYiP4wReecYnvsgIqeyeVJF5GrrQOSsHSLqRR9Rhzp6Kxzb0Mvr2DqiHu/oZXDtQJ10j+3I0u3ahpyaaxXZlnj6s4EK12MPVMvlsTXVyvn61NNkbwNsS7Sp3h785B/Wa/f+Yf3vgL2G98fQ94W6+xfvlv3jB/j+KyRe9W1aswfRqp/zHn8ULKLOEtv2ZNzN+114nkyZPKki6ttnu3YbURi2dqjxMjNs71o8MLbKQ3HE2B58Fl18bLXX3vrsJy9FWQLZzm+Xq4+sJmzm2oagSxCLpUJYgljsQNrStoqk83bMtqFtals63Dng2Q6MLS3L0EvAF1txNjFty1kwbcfa0bADawvDatZm2CqWTgsx2Yq3CbYNb1Nst7w9X9DJdoIdkd0ItkB2EGyJrBbsNbICPW/G2SrJ5outJXv1NFtJNllsI9n0abZ9SQtofb9I3/pPd7Wv0v4Gki3y31ZD0i8AAAAASUVORK5CYII='

        # Save the personal information data in a dictionary
        self.personal_info_data = {
            'entity_id': data['entity_id'],
            'name': data['name'],
            'forename': data['forename'],
            'sex_id': data['sex_id'],
            'country_of_birth_id': data['country_of_birth_id'],
            'place_of_birth': data['place_of_birth'],
            'date_of_birth': data['date_of_birth'],
            'height': data['height'],
            'eyes_colors_id': None if data['eyes_colors_id'] == None else data['eyes_colors_id'][0],
            'hairs_id': None if data['hairs_id'] == None else data['hairs_id'][0],
            'distinguishing_marks': data['distinguishing_marks'],
            'weight': data['weight'],
            'is_active': True,
            'thumbnail': image_base64
        }

        # Add nationality information to the personal information data
        nationalities = []
        if data['nationalities'] is None:
            self.personal_info_data.update({'nationalities': None})
        else:
            for l in data['nationalities']:
                nationalities.append({
                    'entity_id': data['entity_id'],
                    'nationality': l
                })
            self.personal_info_data.update({'nationalities': nationalities})

        # Add languages spoken information to the personal information data
        languages_spoken_ids = []
        if data['languages_spoken_ids'] is None:
            self.personal_info_data.update({'languages_spoken_ids': None})
        else:
            for l in data['languages_spoken_ids']:
                languages_spoken_ids.append({
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l
                })
            self.personal_info_data.update({'languages_spoken_ids': languages_spoken_ids})

        # Add arrest warrants information to the personal information data
        arrest_warrants = []
        if data['arrest_warrants'] is None:
            self.personal_info_data.update({'arrest_warrants': None})
        else:
            for a in data['arrest_warrants']:
                a.update({'entity_id': data['entity_id']})
                arrest_warrants.append(a)
            self.personal_info_data.update({'arrest_warrants': arrest_warrants})

        # Add pictures information to the personal information data
        pictures = []
        pictures_link = \
            perform_request(data['_links']['images']['href']).json()["_embedded"]['images']
        if pictures_link is None:
            self.personal_info_data.update({'pictures': None})
        else:
            for p in pictures_link:
                url = p['_links']['self']['href']
                response = perform_request(url)
                image_content = response.content
                image_base64 = base64.b64encode(image_content).decode("utf-8")
                picture_data = {
                    'entity_id': data['entity_id'],
                    'picture_id': p['picture_id'],
                    'picture_url': p['_links']['self']['href'],
                    'picture_base64': image_base64
                }
                pictures.append(picture_data)
            self.personal_info_data.update({'pictures': pictures})

    def get_personal_info_data(self):
        if not self.personal_info_data:
            self._get_data()
        return self.personal_info_data
