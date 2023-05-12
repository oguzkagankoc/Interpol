import datetime
from decimal import Decimal
import pika
import json
from sqlalchemy import create_engine, update, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_creation import (
    PersonalInformation,
    ArrestWarrantInformation,
    PictureInformation,
    ChangeLogInformation,
    NationalityInformation,
    LanguageInformation
)


# Define a class to consume messages from a RabbitMQ queue
class RabbitMQConsumer:
    def __init__(self):
        # Create an engine to connect to the PostgreSQL database
        self.engine = create_engine(
            "postgresql+psycopg2://postgres:122333@localhost:5432/task")
        # Create a session to work with the database
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        # Create a connection to the local RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare queues to consume messages from
        self.channel.queue_declare(queue='add_data')
        self.channel.queue_declare(queue='change_data')

        # Set up consumers to consume messages from the queue and call the callback function for each message
        self.channel.basic_consume(queue='add_data', on_message_callback=self.callback, auto_ack=True)
        self.channel.basic_consume(queue='change_data', on_message_callback=self.callback_change, auto_ack=True)

    # Define callback functions to be called for each message consumed from the queue
    def callback_change(self, ch, method, properties, body):

        # Print the message received from the queue
        print(" [x] Received %r" % body.decode('utf-8'))
        # Parse the message data as JSON
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

            elif key == 'pictures' and value is not None:
                # Retrieve existing PictureInformation objects from the database for the given entity_id
                db_picture_ids = [d.picture_id for d in
                                  self.session.query(PictureInformation).filter_by(entity_id=entity_id).all()]
                if data['pictures']:
                    queue_picture_ids = [q['picture_id'] for q in data['pictures']]

                    # Delete PictureInformation objects from the database that are not in the queue
                    delete_ids = [q for q in db_picture_ids if q not in queue_picture_ids]
                    self.session.query(PictureInformation).filter(PictureInformation.picture_id.in_(delete_ids)).delete(
                        synchronize_session=False)

                    # Add new PictureInformation objects to the database that are not in the database but in the queue
                    new_picture_ids = [p for p in queue_picture_ids if p not in db_picture_ids]
                    new_pictures = [
                        PictureInformation(
                            picture_id=p,
                            entity_id=entity_id,
                            picture_url=f['picture_url'],
                            picture_base64=f['picture_base64']
                        ) for p in new_picture_ids for f in data['pictures'] if p == f['picture_id']
                    ]
                    self.session.add_all(new_pictures)
                elif not data['pictures'] and db_picture_ids:
                    self.session.query(PictureInformation).filter_by(entity_id=entity_id).delete()

        # add a new change log entry to the database

        self.handle_database_transaction()

    def process_data(self, data, entity_id, table_name):
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

                # Check existing items and remove items that are not in the new data
                for item in items_list:
                    if item not in data:
                        for id in ids_list:
                            if all(id[column] == item[column] for column in columns[1:]):
                                filter_conditions = []
                                filter_conditions.append(getattr(table_name, columns[0]) == id[columns[0]])
                                self.session.query(table_name).filter(*filter_conditions).delete()
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
        elif db_infos and not data:
            self.session.query(table_name).filter_by(entity_id=entity_id).delete()

    def add_change_log_entry(self, key, entity_id, old_value, new_value, table_name, description):
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

    def callback(self, ch, method, properties, body):
        # Print the message received from the queue
        print(" [x] Received %r" % body.decode('utf-8'))

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

        # Add language information to the database, if any
        if not data['languages_spoken_ids'] is None:
            for l in data['languages_spoken_ids']:
                language_data = {
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l['languages_spoken_id']
                }
                language_info = LanguageInformation(**language_data)
                self.session.add(language_info)

        # Add nationality information to the database, if any
        if not data['nationalities'] is None:
            for n in data['nationalities']:
                nationality_data = {
                    'entity_id': data['entity_id'],
                    'nationality': n['nationality']
                }
                nationality_info = NationalityInformation(**nationality_data)
                self.session.add(nationality_info)

        self.handle_database_transaction()

    def handle_database_transaction(self):
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
        finally:
            self.session.close()

    def start_consuming(self):
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def close(self):
        self.connection.close()

consumer = RabbitMQConsumer()
consumer.start_consuming()
