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

# Retrieve Flask host and port from environment variables
host = os.getenv('FLASK_HOST')
port = int(os.getenv('FLASK_PORT'))


@app.route('/results')
def results():
    # Get the page number from the URL query parameter, or use 1 as default
    page = request.args.get('page', 1, type=int)
    # Query the database for the list of persons and paginate the results
    persons_query = AppPersonalInformation.query.order_by(AppPersonalInformation.name).paginate(page=page, per_page=5)
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
    return render_template('results.html', persons=persons, pagination=persons_query, pages=pages, next_url=next_url,
                           prev_url=prev_url)


# Define a route for displaying person details
@app.route('/details/<path:entity_id>')
def person_details(entity_id):
    # Query the database for the AppPersonalInformation record based on entity_id
    person = AppPersonalInformation.query.get(entity_id)
    # Query the database for AppLanguageInformation, AppNationalityInformation, AppArrestWarrantInformation, AppPictureInformation, AppChangeAppLogInformation, AppLogInformation records based on entity_id
    language_info = AppLanguageInformation.query.filter_by(entity_id=entity_id).all()
    nationality_info = AppNationalityInformation.query.filter_by(entity_id=entity_id).all()
    arrest_warrant_info = AppArrestWarrantInformation.query.filter_by(entity_id=entity_id).all()
    picture_info = AppPictureInformation.query.filter_by(entity_id=entity_id).all()
    change_log_info = AppChangeAppLogInformation.query.filter_by(entity_id=entity_id).all()
    log_info = AppLogInformation.query.filter_by(entity_id=entity_id).all()

    # Render the HTML template with the person details and related information
    return render_template('details.html', person=person, language_info=language_info,
                           nationality_info=nationality_info,
                           arrest_warrant_info=arrest_warrant_info, picture_info=picture_info,
                           change_log_info=change_log_info,
                           log_info=log_info)


@app.route('/check_new_data')
def check_new_data():
    # Check for new data
    new_data_added = AppLogInformation.query.filter_by(action='Added').count()
    new_data_deleted = AppLogInformation.query.filter_by(action='Deleted').count()
    new_data_changed = AppChangeAppLogInformation.query.count()

    # Check if there is new data
    has_new_data_added = new_data_added > check_new_data.counter_added
    has_new_data_deleted = new_data_deleted > check_new_data.counter_deleted
    has_new_data_changed = new_data_changed > check_new_data.counter_changed

    # Update the counters
    check_new_data.counter_added = max(new_data_added, check_new_data.counter_added)
    check_new_data.counter_deleted = max(new_data_deleted, check_new_data.counter_deleted)
    check_new_data.counter_changed = max(new_data_changed, check_new_data.counter_changed)

    # Return the result as JSON
    return jsonify({
        'has_new_data_added': has_new_data_added,
        'has_new_data_deleted': has_new_data_deleted,
        'has_new_data_changed': has_new_data_changed
    })


check_new_data.counter_added = 0
check_new_data.counter_deleted = 0
check_new_data.counter_changed = 0


def application():
    app.run(host=host, port=port)

