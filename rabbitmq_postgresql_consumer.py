import pika
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_creation import PersonalInformation, ArrestWarrantInformation, PictureInformation, ChangeLogInformation, \
    NationalityInformation, LanguageInformation
# Create an engine to connect to the PostgreSQL database
engine = create_engine(
    "postgresql+psycopg2://postgres:122333@localhost:5432/task")

# Create a session to work with the database
Session = sessionmaker(bind=engine)
session = Session()

# Define a class to consume messages from a RabbitMQ queue
class RabbitMQConsumer:
    def __init__(self):
        # Create a connection to the local RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare a queue to consume messages from
        self.channel.queue_declare(queue='kuyruk_adi')

        # Set up a consumer to consume messages from the queue and call the callback function for each message
        self.channel.basic_consume(queue='kuyruk_adi', on_message_callback=self.callback, auto_ack=True)

    # Define the callback function to be called for each message consumed from the queue
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
        session.add(personal_info)

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
                session.add(warrant_info)

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
                session.add(picture_info)
        if not data['languages_spoken_ids'] is None:
            for l in data['languages_spoken_ids']:
                language_data = {
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l['languages_spoken_id']
                }
                language_info = LanguageInformation(**language_data)
                session.add(language_info)
        if not data['nationalities'] is None:
            for n in data['nationalities']:
                nationality_data = {
                    'entity_id': data['entity_id'],
                    'nationality': n['nationality']
                }
                nationality_info = NationalityInformation(**nationality_data)
                session.add(nationality_info)

        session.commit()

    def start_consuming(self):
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def close(self):
        self.connection.close()

consumer = RabbitMQConsumer()
consumer.start_consuming()
