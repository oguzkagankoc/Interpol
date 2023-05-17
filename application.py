# Import Flask and SQLAlchemy modules
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import os
from dotenv import load_dotenv
# Load the .env file
load_dotenv()

# Access variables
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Create a Flask application instance
app = Flask(__name__)

# Configure the database connection URL
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Initialize a SQLAlchemy object
db = SQLAlchemy(app)

# Define a model for PersonalInformation table
class PersonalInformation(db.Model):
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

class LanguageInformation(db.Model):
    __tablename__ = "language_informations"
    language_id = db.Column('language_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    languages_spoken_id = db.Column('languages_spoken_id', db.String(20))
    personal_informations = db.relationship(
        "PersonalInformation", backref="language", lazy=True, foreign_keys=[entity_id])

class NationalityInformation(db.Model):
    __tablename__ = "nationality_informations"
    nationality_id = db.Column('nationality_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    nationality = db.Column('nationality', db.String(30))
    personal_informations = db.relationship(
        "PersonalInformation", backref="nationality", lazy=True, foreign_keys=[entity_id])

class PictureInformation(db.Model):
    __tablename__ = "picture_informations"
    picture_id = db.Column('picture_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    picture_url = db.Column('picture_url', db.String(200))
    picture_base64 = db.Column('picture_base64', db.Text)
    personal_informations = db.relationship(
        "PersonalInformation", backref="picture_of_the_criminal", lazy=True, foreign_keys=[entity_id])

class ChangeLogInformation(db.Model):
    __tablename__ = "change_log"
    log_id = db.Column('log_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    table_name = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    description = db.Column(db.Text)
    change_date = db.Column(db.DateTime)
    personal_informations = db.relationship(
        "PersonalInformation", backref="change_log", lazy=True, foreign_keys=[entity_id])

class LogInformation(db.Model):
    __tablename__ = "log"
    log_id = db.Column('log_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    table_name = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    column_data = db.Column(db.TEXT)
    description = db.Column(db.Text)
    personal_informations = db.relationship(
        "PersonalInformation", backref="log", lazy=True, foreign_keys=[entity_id])


class ArrestWarrantInformation(db.Model):
    __tablename__ = "arrest_warrant_informations"
    arrest_warrant_id = db.Column('arrest_warrant_id', db.Integer, primary_key=True)
    entity_id = db.Column('entity_id', db.String(20), db.ForeignKey(
        "personal_informations.entity_id"))
    issuing_country_id = db.Column('issuing_country_id', db.String(30))
    charge = db.Column('charge', db.String(1000))
    charge_translation = db.Column('charge_translation', db.String(1000))
    personal_informations = db.relationship(
        "PersonalInformation", backref="arrest_warrant", lazy=True, foreign_keys=[entity_id])


# Define a route for displaying the list of persons
@app.route('/results')
def results():
    # Get the page number from the URL query parameter, or use 1 as default
    page = request.args.get('page', 1, type=int)
    # Query the database for the list of persons and paginate the results
    persons_query = PersonalInformation.query.order_by(PersonalInformation.name).paginate(page=page, per_page=5)
    # Extract the items (persons) from the pagination object
    persons = persons_query.items
    # Generate a list of page numbers for navigation
    pages = range(1, persons_query.pages + 1)
    # Generate URLs for next and previous pages
    next_url = None
    if persons_query.has_next:
        next_url = f'/results?page={persons_query.next_num}'
    prev_url = None
    if persons_query.has_prev:
        prev_url = f'/results?page={persons_query.prev_num}'
    # Render the HTML template with the list of persons and pagination information
    return render_template('results.html', persons=persons, pagination=persons_query, pages=pages, next_url=next_url, prev_url=prev_url)


# Define a route for displaying person details
@app.route('/details/<path:entity_id>')

def person_details(entity_id):
    # Query the database for the PersonalInformation record based on entity_id
    person = PersonalInformation.query.get(entity_id)
    # Query the database for LanguageInformation, NationalityInformation, ArrestWarrantInformation, PictureInformation, ChangeLogInformation, LogInformation records based on entity_id
    language_info = LanguageInformation.query.filter_by(entity_id=entity_id).all()
    nationality_info = NationalityInformation.query.filter_by(entity_id=entity_id).all()
    arrest_warrant_info = ArrestWarrantInformation.query.filter_by(entity_id=entity_id).all()
    picture_info = PictureInformation.query.filter_by(entity_id=entity_id).all()
    change_log_info = ChangeLogInformation.query.filter_by(entity_id=entity_id).all()
    log_info = LogInformation.query.filter_by(entity_id=entity_id).all()

    # Render the HTML template with the person details and related information
    return render_template('details.html', person=person, language_info=language_info, nationality_info=nationality_info,
                    arrest_warrant_info=arrest_warrant_info, picture_info=picture_info, change_log_info=change_log_info,
                    log_info=log_info)

def has_new_data():
    # Check if there are new records in the LogInformation table
    new_data = LogInformation.query.filter_by(action='Added').count()
    # Check if there are new records in the ChangeLogInformation table
    new_data_change = ChangeLogInformation.query.count()
    # If there are more new records than the previous count, update the counter and return True
    if new_data > has_new_data.counter or new_data_change > has_new_data.counter:
        has_new_data.counter = max(new_data, new_data_change)
        return True
    # Otherwise, return False
    return False

has_new_data.counter = 0

@app.route('/check_new_data')
def check_new_data():
    # Check for new data
    new_data = has_new_data()
    # Return the result as JSON
    return jsonify({'has_new_data': new_data})

if __name__ == '__main__':
    app.run(debug=True)