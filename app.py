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
    return render_template('results.html', persons=persons, pagination=persons_query, pages=pages, next_url=next_url, prev_url=prev_url)


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
    return render_template('details.html', person=person, language_info=language_info, nationality_info=nationality_info,
                    arrest_warrant_info=arrest_warrant_info, picture_info=picture_info, change_log_info=change_log_info,
                    log_info=log_info)

def has_new_data():
    # Check if there are new records in the AppLogInformation table
    new_data = AppLogInformation.query.filter_by(action='Added').count()
    # Check if there are new records in the AppChangeAppLogInformation table
    new_data_change = AppChangeAppLogInformation.query.count()
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

# Define an application function that runs the application in debug mode
def application():
    app.run(debug=True)