import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pika
import requests
import os
from dotenv import load_dotenv

from database_creation import PersonalInformation
from models import InterpolPerson
# Load the .env file
load_dotenv()

# Access variables
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Create the database connection URL
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the engine
engine = create_engine(db_url)
DBSession = sessionmaker(bind=engine)
session = DBSession()



class Producer:
    # Initialize the Producer class
    def __init__(self, key):
        self.key = key
        # Create a new connection to the RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # Create a new channel on the connection
        self.channel = self.connection.channel()
        # Declare the name of the queue that will be used to send messages
        self.channel.queue_declare(queue=self.key)

    # Publish a message to the queue
    def publish(self, message):
        # Use the basic_publish method to send the message to the queue
        self.channel.basic_publish(exchange='', routing_key=self.key, body=message)

    # Close the connection to the RabbitMQ server
    def close(self):
        self.connection.close()


def main():
    list_interpol = "https://ws-public.interpol.int/notices/v1/red?nationality=US&resultPerPage=20&page=1"

    # Get the first page and retrieve the total number of pages
    response = requests.get(list_interpol, headers={}, data={})
    json_list = response.json()
    total_pages = int(json_list['total'] / 20 + 2)

    for page_num in range(1, total_pages):
        # Construct the page link for each page
        page_link = f"https://ws-public.interpol.int/notices/v1/red?nationality=US&resultPerPage=20&page={page_num}"

        # Get the list of persons for the current page
        response = requests.get(page_link, headers={}, data={})
        persons_list = response.json()['_embedded']['notices']

        # Process each person
        for person in persons_list:
            person_links = person['_links']['self']['href']
            interpol_person = InterpolPerson(person_links)
            personal_info_data = interpol_person.get_personal_info_data()
            entity_id = personal_info_data['entity_id']

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


if __name__ == "__main__":
    main()
