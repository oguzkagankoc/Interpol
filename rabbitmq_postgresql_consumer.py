import datetime
from decimal import Decimal
import pika
import json
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_creation import PersonalInformation, ArrestWarrantInformation, PictureInformation, ChangeLogInformation, \
    NationalityInformation, LanguageInformation


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
        db_personal_info = self.session.query(PersonalInformation).filter_by(entity_id=entity_id).one()
        # Compare the data from the queue with the data from the database
        changes = {}
        for key, value in data.items():
            if not isinstance(value, list) and not value is None:
                if key == 'date_of_birth':
                    value = datetime.datetime.strptime(value, '%Y/%m/%d').date()
                elif key == 'height' and isinstance(value, float):
                    value = Decimal(str(value))
                elif key == 'weight' and isinstance(value, float):
                    value = Decimal(str(value))
                if getattr(db_personal_info, key) != value:
                    changes[key] = {'old_value': getattr(db_personal_info, key), 'new_value': value}
                    self.add_change_log_entry(key, db_personal_info.entity_id, changes[key]['old_value'],
                                              changes[key]['new_value'], PersonalInformation.__tablename__,
                                              'Change in personal information')
                    update_statement = update(PersonalInformation).where(
                        PersonalInformation.entity_id == entity_id).values({key: value})
                    self.session.execute(update_statement)

            elif key == 'arrest_warrants' and not value is None:
                pass
            elif key == 'nationalities' and not value is None:
                pass
            elif key == 'languages_spoken_ids' and not value is None:
                pass
            elif key == 'pictures' and not value is None:
                pass
        # add a new change log entry to the database
        if changes:
            print('#')
            print(changes)
            print('#')
            self.handle_database_transaction()

    def add_change_log_entry(self, key, entity_id, old_value, new_value, table_name, description):
        change_log_entry = ChangeLogInformation(
            entity_id=entity_id,
            table_name=table_name,
            field_name=key,
            old_value=str(old_value),
            new_value=str(new_value),
            description=description,
            change_date=datetime.datetime.now())
        self.session.add(change_log_entry)

    def callback(self, ch, method, properties, body):
        # Print the message received from the queue
        print(" [x] Received %r" % body.decode('utf-8'))
        # Parse the message data as JSON
        data = json.loads(body.decode('utf-8'))

        # Create a PersonalInformation object with the data received
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
            'thumbnail': data['thumbnail']}

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
        if not data['languages_spoken_ids'] is None:
            for l in data['languages_spoken_ids']:
                language_data = {
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l['languages_spoken_id']
                }
                language_info = LanguageInformation(**language_data)
                self.session.add(language_info)
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
