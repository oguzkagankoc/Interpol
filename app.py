import time

# Wait for 5 seconds before importing Flask and other modules
time.sleep(5)

from flask import jsonify
from flask import render_template, request
from models import (
    app,
    AppPersonalInformation,
    AppLanguageInformation,
    AppNationalityInformation,
    AppPictureInformation,
    AppChangeAppLogInformation,
    AppLogInformation,
    AppArrestWarrantInformation
)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Application:
    def __init__(self, app):
        """
        Initializes the Flask application, sets up the routes, and initializes counters.
        """
        self.app = app
        # Retrieve Flask host and port from environment variables
        self.host = os.getenv('FLASK_HOST')
        self.port = int(os.getenv('FLASK_PORT'))

        # Define routes and associate them with class methods
        self.app.route('/results')(self.results)
        self.app.route('/details/<path:entity_id>')(self.person_details)
        self.app.route('/check_new_data')(self.check_new_data)

        # Initialize counters as instance attributes
        self.counter_added = 0
        self.counter_deleted = 0
        self.counter_changed = 0

    def run(self):
        self.app.run(host=self.host, port=self.port)

    def results(self):
        """
        Handles the results route and paginates the returned person data.
        """
        # Get the page number from the URL query parameter, or use 1 as default
        page = request.args.get('page', 1, type=int)
        # Query the database for the list of persons and paginate the results
        persons_query = AppPersonalInformation.query.order_by(AppPersonalInformation.name).paginate(page=page, per_page=5)
        persons = persons_query.items
        pages = range(1, persons_query.pages + 1)
        # Generate URLs for next and previous pages
        next_url = f'/results?page={persons_query.next_num}' if persons_query.has_next else None
        prev_url = f'/results?page={persons_query.prev_num}' if persons_query.has_prev else None
        # Render the HTML template with the list of persons and pagination information
        return render_template('results.html', persons=persons, pagination=persons_query, pages=pages, next_url=next_url, prev_url=prev_url)

    def person_details(self, entity_id):
        """
        Handles the details route, retrieving person and related information based on a given entity_id.
        """
        # Query the database for the AppPersonalInformation record based on entity_id
        person = AppPersonalInformation.query.get(entity_id)
        # Query the database for related information based on entity_id
        language_info = AppLanguageInformation.query.filter_by(entity_id=entity_id).all()
        nationality_info = AppNationalityInformation.query.filter_by(entity_id=entity_id).all()
        arrest_warrant_info = AppArrestWarrantInformation.query.filter_by(entity_id=entity_id).all()
        picture_info = AppPictureInformation.query.filter_by(entity_id=entity_id).all()
        change_log_info = AppChangeAppLogInformation.query.filter_by(entity_id=entity_id).all()
        log_info = AppLogInformation.query.filter_by(entity_id=entity_id).all()
        # Render the HTML template with the person details and related information
        return render_template('details.html', person=person, language_info=language_info, nationality_info=nationality_info, arrest_warrant_info=arrest_warrant_info, picture_info=picture_info, change_log_info=change_log_info, log_info=log_info)

    def check_new_data(self):
        """
         Checks if there is new data added, deleted or changed since the last check.
        """
        new_data_added = AppLogInformation.query.filter_by(action='Added').count()
        new_data_deleted = AppLogInformation.query.filter_by(action='Deleted').count()
        new_data_changed = AppChangeAppLogInformation.query.count()

        has_new_data_added = new_data_added > self.counter_added
        has_new_data_deleted = new_data_deleted > self.counter_deleted
        has_new_data_changed = new_data_changed > self.counter_changed

        self.counter_added = max(new_data_added, self.counter_added)
        self.counter_deleted = max(new_data_deleted, self.counter_deleted)
        self.counter_changed = max(new_data_changed, self.counter_changed)

        return jsonify({
            'has_new_data_added': has_new_data_added,
            'has_new_data_deleted': has_new_data_deleted,
            'has_new_data_changed': has_new_data_changed
        })

def application():
    app_flask = Application(app)
    app_flask.run()

