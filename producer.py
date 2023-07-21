import base64
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
from models import AppPersonalInformation, AppChangeAppLogInformation

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


class InterpolPerson:
    """
    This class is responsible for retrieving and processing data about a single criminal from Interpol.

    Attributes:
    person_url (str): The URL where the data about the criminal is located.
    personal_info_data (dict): A dictionary to hold the processed data.
    """

    def __init__(self, person_url):
        # Initialize instance variables
        self.person_url = person_url
        self.personal_info_data = {}

    def _get_data(self):
        """
        This method processes and parses the data from the request,
        and adds it appropriately to the personal_info_data dictionary.
        """
        # Get data from the provided URL
        response = self.perform_request(self.person_url)
        data = response.json()

        # Get the person's image URL, retrieve the image and encode it to base64
        if "thumbnail" in data['_links'].keys():
            image_url = data['_links']['thumbnail']['href']
            image_response = self.perform_request(image_url)
            image_content = image_response.content
            image_base64 = base64.b64encode(image_content).decode("utf-8")
        else:
            # If there is no "thumbnail" information, a default image is assigned to the image_base64 value.
            image_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAKoAAACqAgMAAABAGDwRAAAADFBMVEWutLfk5ufb3d/EyMpaqx/2AAACUUlEQVRYw+3YK3LcQBAA0LZUBgJKkI8gHiLgoD3CAu1IVREQ3wU6gi6xPNQh2QMEzA2CdASDsFCTOJWsVur5dPeM7VTsKgm/mur5dfcIdsHfFla72tWudrVv0359/BFqTwDwEGYP8Oe7D7FK/7XvQux5WM/AHqsnm8u2mSikR9H2FwuFaPVsc8nWM4VUsu1iYRRsj2wpWI1sxluFKCS8rbBNeYunZk/Otp1hC9ZuDFuyVhs2Y61B4YqztWkTzlamTTnbmBaOjG0tOzJ2a9kbxnaWLRjbR9iNZcsIe83Y4Rk2Y6y2bP4fLLyxcV+jzV7oPMScs5iz3j/DFhH3+CYiP4wReecYnvsgIqeyeVJF5GrrQOSsHSLqRR9Rhzp6Kxzb0Mvr2DqiHu/oZXDtQJ10j+3I0u3ahpyaaxXZlnj6s4EK12MPVMvlsTXVyvn61NNkbwNsS7Sp3h785B/Wa/f+Yf3vgL2G98fQ94W6+xfvlv3jB/j+KyRe9W1aswfRqp/zHn8ULKLOEtv2ZNzN+114nkyZPKki6ttnu3YbURi2dqjxMjNs71o8MLbKQ3HE2B58Fl18bLXX3vrsJy9FWQLZzm+Xq4+sJmzm2oagSxCLpUJYgljsQNrStoqk83bMtqFtals63Dng2Q6MLS3L0EvAF1txNjFty1kwbcfa0bADawvDatZm2CqWTgsx2Yq3CbYNb1Nst7w9X9DJdoIdkd0ItkB2EGyJrBbsNbICPW/G2SrJ5outJXv1NFtJNllsI9n0abZ9SQtofb9I3/pPd7Wv0v4Gki3y31ZD0i8AAAAASUVORK5CYII='

        # Save the personal information data in a dictionary
        self.personal_info_data = {
            'entity_id': data['entity_id'],
            'name': data['name'],
            'forename': data['forename'],
            'sex_id': data['sex_id'],
            'country_of_birth_id': data['country_of_birth_id'],
            'place_of_birth': data['place_of_birth'],
            'date_of_birth': data['date_of_birth'],
            'height': data['height'],
            'eyes_colors_id': None if data['eyes_colors_id'] == None else data['eyes_colors_id'][0],
            'hairs_id': None if data['hairs_id'] == None else data['hairs_id'][0],
            'distinguishing_marks': data['distinguishing_marks'],
            'weight': data['weight'],
            'is_active': True,
            'thumbnail': image_base64
        }

        # Add nationality information to the personal information data
        nationalities = []
        if data['nationalities'] is None:
            self.personal_info_data.update({'nationalities': None})
        else:
            for l in data['nationalities']:
                nationalities.append({
                    'entity_id': data['entity_id'],
                    'nationality': l
                })
            self.personal_info_data.update({'nationalities': nationalities})

        # Add languages spoken information to the personal information data
        languages_spoken_ids = []
        if data['languages_spoken_ids'] is None:
            self.personal_info_data.update({'languages_spoken_ids': None})
        else:
            for l in data['languages_spoken_ids']:
                languages_spoken_ids.append({
                    'entity_id': data['entity_id'],
                    'languages_spoken_id': l
                })
            self.personal_info_data.update({'languages_spoken_ids': languages_spoken_ids})

        # Add arrest warrants information to the personal information data
        arrest_warrants = []
        if data['arrest_warrants'] is None:
            self.personal_info_data.update({'arrest_warrants': None})
        else:
            for a in data['arrest_warrants']:
                a.update({'entity_id': data['entity_id']})
                arrest_warrants.append(a)
            self.personal_info_data.update({'arrest_warrants': arrest_warrants})

        # Add pictures information to the personal information data
        pictures = []
        pictures_link = self.perform_request(data['_links']['images']['href']).json()["_embedded"]['images']
        if pictures_link is None:
            self.personal_info_data.update({'pictures': None})
        else:
            for p in pictures_link:
                url = p['_links']['self']['href']
                response = self.perform_request(url)
                image_content = response.content
                image_base64 = base64.b64encode(image_content).decode("utf-8")
                picture_data = {
                    'entity_id': data['entity_id'],
                    'picture_id': p['picture_id'],
                    'picture_url': p['_links']['self']['href'],
                    'picture_base64': image_base64
                }
                pictures.append(picture_data)
            self.personal_info_data.update({'pictures': pictures})

    @staticmethod
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

    def get_personal_info_data(self):
        """
        Retrieves and returns the processed data. If data has not been retrieved and processed yet, it does so first.

        Returns:
            personal_info_data (dict): The processed data about the criminal.
        """
        if not self.personal_info_data:
            self._get_data()
        return self.personal_info_data


class InterpolDataRetriever:
    """
    This class is responsible for retrieving data from Interpol and performing database operations.
    """

    def __init__(self, nationality):
        # Create the engine
        self.engine = create_engine(db_url)
        self.DBSession = sessionmaker(bind=engine)
        self.session = self.DBSession()
        self.nationality = nationality

    def retrieve_data(self):
        """
        Retrieve data from Interpol, process it, and perform database operations.
        """
        # Define the URL for the Interpol Red Notices endpoint
        url = "https://ws-public.interpol.int/notices/v1/red"

        # Define the query parameters for the GET request
        params = {
            "nationality": f"{self.nationality}",  # Search for people with nationality
            "resultPerPage": 160,  # Request 160 results per page
            "page": 1  # Request the first page of results
        }

        # Perform the GET request and get the response
        response = InterpolPerson.perform_request(url, params)

        # Convert the response to JSON format
        json_list = response.json()

        # Initialize a list to hold the entity IDs of the persons
        entity_id_list = []

        # Get the list of persons from the response
        persons_list = json_list['_embedded']['notices']

        # Process each person in the list
        for person in persons_list:
            # Get the person's self link
            person_links = person['_links']['self']['href']

            # Create an InterpolPerson object for the person
            interpol_person = InterpolPerson(person_links)

            # Get the person's personal info data
            personal_info_data = interpol_person.get_personal_info_data()

            # Get the person's entity ID
            entity_id = personal_info_data['entity_id']

            # Add the entity ID to the list
            entity_id_list.append(entity_id)
            # Check if the person is already in the database
            if self.session.query(AppPersonalInformation).filter_by(entity_id=entity_id).first():
                json_data = json.dumps(personal_info_data)
                producer = Producer('change_data')
                producer.publish(json_data)
                producer.close()
                print(f"The data with {entity_id} entity_id already exists in the database.")
            else:
                # Add the person to the database and publish their personal information
                json_data = json.dumps(personal_info_data)
                producer = Producer('add_data')
                producer.publish(json_data)
                producer.close()
                print(f"The data with {entity_id} entity_id has been added to the database.")

        # Get the existing entity IDs from the database
        existing_entity_ids = self.session.query(AppPersonalInformation.entity_id).all()
        existing_entity_ids = [entity_id[0] for entity_id in existing_entity_ids]

        # Update the is_active value for records with missing entity IDs
        for entity_id in existing_entity_ids:
            if entity_id not in entity_id_list:
                person = self.session.query(AppPersonalInformation).filter_by(entity_id=entity_id).first()
                # If the "is_active" property of the person not in the database is "True", set it to "False".
                if person.is_active == True:
                    person.is_active = False
                    change_log_entry = AppChangeAppLogInformation(
                        entity_id=entity_id,
                        table_name="personal_informations",
                        field_name="is_active",
                        old_value=True,
                        new_value=False,
                        description="Change in personal information",
                        change_date=datetime.datetime.now()
                    )
                    # Add the ChangeLogInformation object to the session to be committed to the database
                    self.session.add(change_log_entry)

        # Commit the changes
        try:
            self.session.commit()
        except IntegrityError:
            # If there is an integrity error during commit, rollback the transaction
            self.session.rollback()


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

if __name__ == "__main__":
    # Sleep for 2 seconds before starting the operations. This is useful to prevent immediate connection attempts in case of restarts.
    time.sleep(2)

    # Enter an infinite loop to continuously retrieve data from Interpol.
    while True:
        # Wait for 2 seconds before each data retrieval operation.
        time.sleep(2)

        # Create an instance of the InterpolDataRetriever class with the nationality parameter set to "US" (United States of America).
        data_retriever = InterpolDataRetriever("US")

        # Call the retrieve_data method of the InterpolDataRetriever instance to retrieve data from Interpol,
        # process it, and perform database operations.
        data_retriever.retrieve_data()
