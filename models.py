import os
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

