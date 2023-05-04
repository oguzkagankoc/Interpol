import base64
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pika
import requests

from database_creation import PersonalInformation

engine = create_engine(
    "postgresql+psycopg2://postgres:122333@localhost:5432/task")
Session = sessionmaker(bind=engine)
session = Session()

class InterpolPerson:
    def __init__(self, person_url):
        # Initialize instance variables
        self.person_url = person_url
        self.personal_info_data = {}

    def _get_data(self):
        # Get data from the provided URL
        response = requests.get(self.person_url)
        data = response.json()

        # Get the person's image URL, retrieve the image and encode it to base64
        image_url = data['_links']['images']['href']
        image_response = requests.get(image_url)
        image_content = image_response.content
        image_base64 = base64.b64encode(image_content).decode('utf-8')

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
            'eyes_colors_id': data['eyes_colors_id'],
            'hairs_id': data['hairs_id'],
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
        pictures_link = requests.request("GET", data['_links']['images']['href'], headers={}, data={}).json()["_embedded"]['images']
        if pictures_link is None:
            self.personal_info_data.update({'pictures': None})
        else:
            for p in pictures_link:
                url = p['_links']['self']['href']
                response = requests.get(url)
                image_content = response.content
                image_base64 = base64.b64encode(image_content).decode('utf-8')
                picture_data = {
                    'entity_id': data['entity_id'],
                    'picture_id': p['picture_id'],
                    'picture_url': p['_links']['self']['href'],
                    'picture_base64': image_base64
                }
                pictures.append(picture_data)
            self.personal_info_data.update({'pictures': pictures})

    def get_personal_info_data(self):
        if not self.personal_info_data:
            self._get_data()
        return self.personal_info_data

class Producer:
    # Initialize the Producer class
    def __init__(self):
        # Create a new connection to the RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # Create a new channel on the connection
        self.channel = self.connection.channel()
        # Declare the name of the queue that will be used to send messages
        self.channel.queue_declare(queue='kuyruk_adi')

    # Publish a message to the queue
    def publish(self, message):
        # Use the basic_publish method to send the message to the queue
        self.channel.basic_publish(exchange='', routing_key='kuyruk_adi', body=message)

    # Close the connection to the RabbitMQ server
    def close(self):
        self.connection.close()


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
            print(f"{entity_id}: Kayıt var")
        else:
            # Add the person to the database and publish their personal information
            json_data = json.dumps(personal_info_data)
            producer = Producer()
            producer.publish(json_data)
            producer.close()
            print(f"{entity_id}: Kayıt eklendi")