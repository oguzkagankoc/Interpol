# Import necessary modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_creation import (
    PersonalInformation,
    ChangeLogInformation,
    PictureInformation,
    ArrestWarrantInformation,
    NationalityInformation,
    LanguageInformation,
    LogInformation,
)
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
# Create an engine to connect to the PostgreSQL database
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url)

# Create an engine for the database
engine = create_engine("postgresql+psycopg2://postgres:122333@localhost:5432/task")

# Create a session maker bound to the engine
Session = sessionmaker(bind=engine)

# Create a session
session = Session()

# Define the classes to be deleted
entity_classes = [
    LanguageInformation,
    NationalityInformation,
    ArrestWarrantInformation,
    PictureInformation,
    ChangeLogInformation,
    LogInformation,
    PersonalInformation,
]

# Loop through each class and delete all instances
for entity_class in entity_classes:
    # Create a new session for each iteration
    session = Session()

    # Get all the entity IDs for the class
    entity_ids = session.query(entity_class.entity_id).all()
    # Extract the entity IDs from the query result
    entity_ids = [entity_id[0] for entity_id in entity_ids]
    # Delete all the instances with matching entity IDs
    for entity_id in entity_ids:
        session.query(entity_class).filter_by(entity_id=entity_id).delete()

    # Commit the changes to the database for each iteration
    session.commit()

# Close the session
session.close()