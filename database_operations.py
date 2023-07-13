import datetime
import json
import os
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy import create_engine, update, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database_creation import (
    PersonalInformation,
    ArrestWarrantInformation,
    PictureInformation,
    ChangeLogInformation,
    NationalityInformation,
    LanguageInformation, LogInformation
)

# Load environment variables from .env file
load_dotenv()

# Access variables
db_username = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')

# Create the database connection URL
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"


# Define database operation classes

class DatabaseOperationsCallback:
    """
    This class provides the functionalities for handling database operations
    such as creating a connection, managing sessions, and handling callbacks
    for database changes.

    Attributes:
        engine (create_engine): An instance of SQLAlchemy engine.
        Session (sessionmaker): An instance of SQLAlchemy sessionmaker, which is a factory for creating sessions.
        session (Session): An instance of SQLAlchemy Session, a handle to the database.
    """
    def __init__(self):
        # Create an engine to connect to the PostgreSQL database
        self.engine = create_engine(db_url)

        # Create a session to work with the database
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()


    def callback_change_db(self, body):
        """
        This method is responsible for changing data in the database based on the message received.
        It parses the message data as JSON and compares it with the data in the database.
        If any changes are detected, it will update the database and log the change.
        """

        # Decoding the JSON data from the body of the message
        data = json.loads(body.decode('utf-8'))
        entity_id = data['entity_id']

        # Compare the data from the queue with the data from the database
        changes = {}
        for key, value in data.items():
            db_personal_info = self.session.query(PersonalInformation).filter_by(entity_id=entity_id).one()
            if not isinstance(value, list) and value is not None:
                if key == 'date_of_birth':
                    value = datetime.datetime.strptime(value, '%Y/%m/%d').date()
                elif key in ['height', 'weight'] and isinstance(value, float):
                    value = Decimal(str(value))
                if getattr(db_personal_info, key) != value:
                    changes[key] = {'old_value': getattr(db_personal_info, key), 'new_value': value}
                    self.add_change_log_entry(
                        key, db_personal_info.entity_id, changes[key]['old_value'], changes[key]['new_value'],
                        PersonalInformation.__tablename__, 'Change in personal information'
                    )
                    update_statement = update(PersonalInformation).where(
                        PersonalInformation.entity_id == entity_id
                    ).values({key: value})
                    self.session.execute(update_statement)

            elif key == 'languages_spoken_ids':
                self.process_data(data['languages_spoken_ids'], entity_id, LanguageInformation)

            elif key == 'nationalities':
                self.process_data(data['nationalities'], entity_id, NationalityInformation)

            elif key == 'arrest_warrants':
                self.process_data(data['arrest_warrants'], entity_id, ArrestWarrantInformation)

            elif key == 'pictures':
                # Retrieve existing PictureInformation objects from the database for the given entity_id
                db_picture_ids = [d.picture_id for d in
                                  self.session.query(PictureInformation).filter_by(entity_id=entity_id).all()]
                if data['pictures'] and db_picture_ids:
                    queue_picture_ids = [int(q['picture_id']) for q in data['pictures']]

                    # Delete PictureInformation objects from the database that are not in the queue
                    delete_ids = [q for q in db_picture_ids if q not in queue_picture_ids]
                    for picture_id in delete_ids:
                        picture_info = self.session.query(PictureInformation).filter_by(picture_id=picture_id).first()
                        if picture_info:
                            picture_data = {
                                'entity_id': picture_info.entity_id,
                                'picture_id': picture_info.picture_id,
                                'picture_url': picture_info.picture_url,
                                'picture_base64': picture_info.picture_base64
                            }
                            self.session.delete(picture_info)
                            self.add_log_entry(entity_id, PictureInformation.__tablename__, 'Deleted', picture_data)

                    # Add new PictureInformation objects to the database that are not in the database but in the queue
                    new_picture_ids = [p for p in queue_picture_ids if p not in db_picture_ids]
                    new_pictures = []
                    for p in new_picture_ids:
                        for f in data['pictures']:
                            if p == int(f['picture_id']):
                                picture = PictureInformation(
                                    picture_id=p,
                                    entity_id=entity_id,
                                    picture_url=f['picture_url'],
                                    picture_base64=f['picture_base64']
                                )
                                picture_data = {
                                    'entity_id': entity_id,
                                    'picture_id': p,
                                    'picture_url': f['picture_url'],
                                    'picture_base64': f['picture_base64']
                                }
                                new_pictures.append(picture)
                                self.add_log_entry(entity_id, PictureInformation.__tablename__, 'Added', picture_data)

                    self.session.add_all(new_pictures)

                elif not data['pictures'] and db_picture_ids:
                    for db_id in db_picture_ids:
                        picture_db = self.session.query(PictureInformation).filter_by(picture_id=db_id).one()
                        picture_data = {
                            'entity_id': picture_db.entity_id,
                            'picture_id': picture_db.picture_id,
                            'picture_url': picture_db.picture_url,
                            'picture_base64': picture_db.picture_base64
                        }
                        self.session.query(PictureInformation).filter_by(picture_id=db_id).delete()
                        self.add_log_entry(picture_db.entity_id, PictureInformation.__tablename__, 'Deleted',
                                           picture_data)

        # add a new change log entry to the database

        self.handle_database_transaction()

    def process_data(self, data, entity_id, table_name):
        """
        Processes a given dataset by either updating or deleting existing database entries,
        or creating new ones as necessary. The process is executed based on the table name
        provided and the entity ID associated with the dataset.

        Parameters:
        data (list of dict): The new data to be processed.
        entity_id (int): The entity ID that the data is associated with.
        table_name (sqlalchemy.ext.declarative.api.DeclarativeMeta): The table where data will be processed.
        """
        # Retrieve the column names of the table
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name.__tablename__)
        columns = [column['name'] for column in columns]

        # Query existing data from the table
        db_infos = self.session.query(table_name).filter_by(entity_id=entity_id).all()
        items_list = []
        ids_list = []
        if data:
            if db_infos:
                # Iterate over existing items and create dictionaries for comparison
                for item in db_infos:
                    item_dict = {}
                    ids = {}
                    ids[columns[0]] = getattr(item, columns[0])
                    for column in columns[1:]:
                        if hasattr(item, column):
                            column_value = getattr(item, column)
                            item_dict[column] = column_value
                            ids[column] = column_value
                    items_list.append(item_dict)
                    ids_list.append(ids)

                # Check new data and add items that are not in the existing list
                for d in data:
                    if d not in items_list:
                        item_dict = {}
                        for column in columns[2:]:
                            column_value = d[column]
                            item_dict[column] = column_value
                        item_dict['entity_id'] = entity_id
                        item_info = table_name(**item_dict)
                        self.session.add(item_info)
                        self.add_log_entry(item_dict['entity_id'], table_name.__tablename__, 'Added', item_dict)

                # Check existing items and remove items that are not in the new data
                for item in items_list:
                    if item not in data:
                        for id in ids_list:
                            if all(id[column] == item[column] for column in columns[1:]):
                                filter_conditions = []
                                filter_conditions.append(getattr(table_name, columns[0]) == id[columns[0]])
                                dict_data = {column: id[column] for column in columns[1:]}
                                self.session.query(table_name).filter(*filter_conditions).delete()
                                self.add_log_entry(id[columns[1]], table_name.__tablename__, 'Deleted', dict_data)

            else:
                # If no existing data, add all items from the new data
                for d in data:
                    item_dict = {}
                    for column in columns[1:]:
                        column_value = d[column]
                        item_dict[column] = column_value
                    item_dict['entity_id'] = entity_id
                    item_info = table_name(**item_dict)
                    self.session.add(item_info)
                    self.add_log_entry(item_dict['entity_id'], table_name.__tablename__, 'Added', item_dict)

        elif db_infos and not data:
            # If no data, remove existing data
            for item in db_infos:
                item_dict = {}
                for column in columns[1:]:
                    if hasattr(item, column):
                        column_value = getattr(item, column)
                        item_dict[column] = column_value
                db_id_val = getattr(item, columns[0])
                self.session.query(table_name).filter(getattr(table_name, columns[0]) == db_id_val).delete()
                self.add_log_entry(item_dict['entity_id'], table_name.__tablename__, 'Deleted', item_dict)

    def add_change_log_entry(self, key, entity_id, old_value, new_value, table_name, description):
        """
        Creates a new change log entry in the database by creating a new ChangeLogInformation object,
        and then adds it to the current session to be committed later.

        Parameters:
        key (str): The field name where the change occurred.
        entity_id (int): The entity ID related to the change.
        old_value (various): The original value of the field.
        new_value (various): The new value of the field.
        table_name (str): The table name where the change occurred.
        description (str): A description of the change that occurred.
        """
        # Create a ChangeLogInformation object with the provided data
        change_log_entry = ChangeLogInformation(
            entity_id=entity_id,
            table_name=table_name,
            field_name=key,
            old_value=str(old_value),
            new_value=str(new_value),
            description=description,
            change_date=datetime.datetime.now()
        )
        # Add the ChangeLogInformation object to the session to be committed to the database
        self.session.add(change_log_entry)

    def add_log_entry(self, entity_id, table_name, action, column_data, description=None):
        """
        Creates a new log entry in the database by creating a new LogInformation object,
        and then adds it to the current session to be committed later.

        Parameters:
        entity_id (int): The entity ID related to the log.
        table_name (str): The table name related to the log.
        action (str): The action that took place ('Added', 'Updated', 'Deleted').
        column_data (dict): The data that was acted upon.
        description (str, optional): A description of the action that took place.
        """
        change_log_entry = LogInformation(
            entity_id=entity_id,
            table_name=table_name,
            action=action,
            timestamp=datetime.datetime.now(),
            column_data=column_data,
            description=description
        )
        self.session.add(change_log_entry)

    def callback_db(self, body):
        """
        A callback function that processes an incoming message and updates the database accordingly.
        This function parses the JSON data from the message, creates various database objects
        depending on the data received, and adds them to the current session to be committed later.

        Parameters:
        body (bytes): The raw message data received.
        """
        # Parse the message data as JSON
        data = json.loads(body.decode('utf-8'))

        # Create a PersonalInformation object with the received data
        personal_info_data = {
            'entity_id': data['entity_id'],
            'name': data['name'],
            'forename': data['forename'],
            'sex_id': data['sex_id'],
            'country_of_birth_id': data['country_of_birth_id'],
            'place_of_birth': data['place_of_birth'],
            'date_of_birth': data['date_of_birth'],
            'height': data['height'],
            'eyes_colors_id': data['eyes_colors_id'],
            'hairs_id': data['hairs_id'],
            'distinguishing_marks': data['distinguishing_marks'],
            'weight': data['weight'],
            'is_active': data['is_active'],
            'thumbnail': data['thumbnail']
        }

        personal_info = PersonalInformation(**personal_info_data)

        # Add the PersonalInformation object to the session to be committed to the database
        self.session.add(personal_info)
        self.add_log_entry(data['entity_id'], PersonalInformation.__tablename__, 'Added', personal_info_data)

        # If there are arrest warrants in the message, create ArrestWarrantInformation objects and add them to the session
        if not data['arrest_warrants'] is None:
            for warrant in data['arrest_warrants']:
                warrant_data = {
                    'entity_id': data['entity_id'],
                    'issuing_country_id': warrant['issuing_country_id'],
                    'charge': warrant['charge'],
                    'charge_translation': warrant['charge_translation']
                }
                warrant_info = ArrestWarrantInformation(**warrant_data)
                self.session.add(warrant_info)
                self.add_log_entry(data['entity_id'], ArrestWarrantInformation.__tablename__, 'Added', warrant_data)

        # Insert picture information into the database, if any
        if not data['pictures'] is None:
            for p in data['pictures']:
                picture_data = {
                    'entity_id': data['entity_id'],
                    'picture_id': p['picture_id'],
                    'picture_url': p['picture_url'],
                    'picture_base64': p['picture_base64']
                }
                picture_info = PictureInformation(**picture_data)
                self.session.add(picture_info)
                self.add_log_entry(data['entity_id'], PictureInformation.__tablename__, 'Added', picture_data)

        # Add language information to the database, if any
        if not data['languages_spoken_ids'] is None:
            for l in data['languages_spoken_ids']:
                language_data = {
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l['languages_spoken_id']
                }
                language_info = LanguageInformation(**language_data)
                self.session.add(language_info)
                self.add_log_entry(data['entity_id'], LanguageInformation.__tablename__, 'Added', language_data)

        # Add nationality information to the database, if any
        if not data['nationalities'] is None:
            for n in data['nationalities']:
                nationality_data = {
                    'entity_id': data['entity_id'],
                    'nationality': n['nationality']
                }
                nationality_info = NationalityInformation(**nationality_data)
                self.session.add(nationality_info)
                self.add_log_entry(data['entity_id'], NationalityInformation.__tablename__, 'Added', nationality_data)

        self.handle_database_transaction()

    def handle_database_transaction(self):
        """
        This method handles the commit and rollback operations for database transactions.
        If an IntegrityError occurs during the commit, the transaction will be rolled back.
        The session is closed at the end, regardless of whether the commit was successful or not.
        """
        try:
            self.session.commit()
        except IntegrityError:
            # If there is an integrity error during commit, rollback the transaction
            self.session.rollback()
        finally:
            # Close the session to release resources
            self.session.close()
