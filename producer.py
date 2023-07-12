import json
import os
import time
import pika
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import datetime
from database_creation import PersonalInformation, ChangeLogInformation
from models import InterpolPerson

# Load the .env file
load_dotenv()

# Access variables
db_username = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')
rabbitmq_host = os.getenv('RABBITMQ_HOST')

# Create the database connection URL
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the engine
engine = create_engine(db_url)
DBSession = sessionmaker(bind=engine)
session = DBSession()


class Producer:
    """
    The Producer class for publishing messages to RabbitMQ.
    """

    def __init__(self, key):
        """
        Initialize the Producer class.

        Args:
            key (str): The routing key for the message queue.
        """
        self.key = key
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.key)

    def publish(self, message):
        """
        Publish a message to the RabbitMQ queue.

        Args:
            message (str): The message to be published.
        """
        self.channel.basic_publish(exchange='', routing_key=self.key, body=message)

    def close(self):
        """
        Close the connection to RabbitMQ.
        """
        self.connection.close()


def perform_request(url, params=None):
    """
    Perform an HTTP GET request.

    Args:
        url (str): The URL to make the request.
        params (dict, optional): Dictionary or bytes to be sent in the query string for the Request.

    Returns:
        requests.Response: The response object.

    Raises:
        requests.exceptions.RequestException: If an error occurs during the request.
    """
    while True:
        try:
            response = requests.get(url, headers={}, params=params)
            return response
        except requests.exceptions.RequestException:
            print("Internet connection lost. Trying to reconnect...")
            time.sleep(5)

def main():
    """
    The main function that performs the data retrieval and database operations.
    """
    time.sleep(2)
    # Get the first page and retrieve the total number of pages
    url = "https://ws-public.interpol.int/notices/v1/red"
    params = {
        "nationality": "US",
        "resultPerPage": 160,
        "page": 1
    }

    response = perform_request(url, params)
    json_list = response.json()

    entity_id_list = []

    persons_list = json_list['_embedded']['notices']

    # Process each person
    for person in persons_list:
        person_links = person['_links']['self']['href']
        interpol_person = InterpolPerson(person_links)
        personal_info_data = interpol_person.get_personal_info_data()
        entity_id = personal_info_data['entity_id']
        entity_id_list.append(entity_id)

        # Check if the person is already in the database
        if session.query(PersonalInformation).filter_by(entity_id=entity_id).first():
            print(f"The data with {entity_id} entity_id already exists in the database.")
            json_data = json.dumps(personal_info_data)
            producer = Producer('change_data')
            producer.publish(json_data)
            producer.close()
        else:
            # Add the person to the database and publish their personal information
            json_data = json.dumps(personal_info_data)
            producer = Producer('add_data')
            producer.publish(json_data)
            producer.close()
            print(f"The data with {entity_id} entity_id has been added to the database.")

    # Get the existing entity IDs from the database
    existing_entity_ids = session.query(PersonalInformation.entity_id).all()
    existing_entity_ids = [entity_id[0] for entity_id in existing_entity_ids]

    # Update the is_active value for records with missing entity IDs
    for entity_id in existing_entity_ids:
        if entity_id not in entity_id_list:
            person = session.query(PersonalInformation).filter_by(entity_id=entity_id).first()
            #If the "is_active" property of the person not in the database is "True", set it to "False".
            if person.is_active == True:
                person.is_active = False
                change_log_entry = ChangeLogInformation(
                    entity_id=entity_id,
                    table_name="personal_informations",
                    field_name="is_active",
                    old_value=True,
                    new_value=False,
                    description="Change in personal information",
                    change_date=datetime.datetime.now()
                )
                # Add the ChangeLogInformation object to the session to be committed to the database
                session.add(change_log_entry)

    # Commit the changes
    try:
        session.commit()
    except IntegrityError:
        # If there is an integrity error during commit, rollback the transaction
        session.rollback()


if __name__ == "__main__":
    while True:
        time.sleep(2)
        main()
