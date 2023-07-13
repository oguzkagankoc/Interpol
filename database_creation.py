import os

from dotenv import load_dotenv
from sqlalchemy import Column, String, ForeignKey, Integer, Date, Boolean, Text, DateTime, DECIMAL, MetaData
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import relationship

# Load the .env file
load_dotenv()

# Access variables
db_username = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')

# Create the database connection URL
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the engine
engine = create_engine(db_url)
Base = declarative_base()
DBSession = sessionmaker(bind=engine)
session = DBSession()


class PersonalInformation(Base):
    # Table for storing personal information
    __tablename__ = "personal_informations"
    entity_id = Column('entity_id', String(20), primary_key=True, nullable=False)
    forename = Column('forename', String(50))
    name = Column('name', String(50))
    sex_id = Column('sex_id', String(10))
    date_of_birth = Column('date_of_birth', Date)
    place_of_birth = Column('place_of_birth', String(100))
    country_of_birth_id = Column('country_of_birth_id', String(50))
    weight = Column('weight', DECIMAL())
    height = Column('height', DECIMAL())
    distinguishing_marks = Column('distinguishing_marks', String(1000))
    eyes_colors_id = Column('eyes_colors_id', String(20))
    hairs_id = Column('hairs_id', String(20))
    is_active = Column('is_active', Boolean, nullable=False)
    thumbnail = Column('thumbnail', Text)


class LanguageInformation(Base):
    # Table for storing language information
    __tablename__ = "language_informations"
    language_id = Column('language_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    languages_spoken_id = Column('languages_spoken_id', String(20))
    personal_informations = relationship(
        "PersonalInformation", backref="language", lazy=True, foreign_keys=[entity_id])


class NationalityInformation(Base):
    # Table for storing nationality information
    __tablename__ = "nationality_informations"
    nationality_id = Column('nationality_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    nationality = Column('nationality', String(30))
    personal_informations = relationship(
        "PersonalInformation", backref="nationality", lazy=True, foreign_keys=[entity_id])


class ArrestWarrantInformation(Base):
    # Table for storing arrest warrant information
    __tablename__ = "arrest_warrant_informations"
    arrest_warrant_id = Column('arrest_warrant_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    issuing_country_id = Column('issuing_country_id', String(30))
    charge = Column('charge', String(1000))
    charge_translation = Column('charge_translation', String(1000))
    personal_informations = relationship(
        "PersonalInformation", backref="arrest_warrant", lazy=True, foreign_keys=[entity_id])


class PictureInformation(Base):
    # Table for storing picture information
    __tablename__ = "picture_informations"
    picture_id = Column('picture_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    picture_url = Column('picture_url', String(200))
    picture_base64 = Column('picture_base64', Text)
    personal_informations = relationship(
        "PersonalInformation", backref="picture_of_the_criminal", lazy=True, foreign_keys=[entity_id])


class ChangeLogInformation(Base):
    # Table for storing change log information
    __tablename__ = "change_log"
    log_id = Column('log_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    table_name = Column(String(50), nullable=False)
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    description = Column(Text)
    change_date = Column(DateTime)
    personal_informations = relationship(
        "PersonalInformation", backref="change_log", lazy=True, foreign_keys=[entity_id])


class LogInformation(Base):
    # Table for storing log information
    __tablename__ = "log"
    log_id = Column('log_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    table_name = Column(String(50), nullable=False)
    action = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    column_data = Column(JSONB)
    description = Column(Text)
    personal_informations = relationship(
        "PersonalInformation", backref="log", lazy=True, foreign_keys=[entity_id])


def table_exists(table_name):
    """
    Checks whether the specified table exists in the database.

    Args:
        table_name (str): The name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    meta = MetaData()
    meta.reflect(bind=engine)
    return table_name in meta.tables

def create_table_if_not_exists(table_name):
    """
    Creates the specified table in the database if it does not already exist.

    Args:
        table_name (str): The name of the table to create.
    """
    if not table_exists(table_name):
        Base.metadata.tables[table_name].create(engine)
        print(f"Table {table_name} has been created.")
    else:
        print(f"Table {table_name} already exists.")

def create_tables():
    # List of table names to create
    table_names = [
        "personal_informations",
        "language_informations",
        "nationality_informations",
        "arrest_warrant_informations",
        "picture_informations",
        "change_log",
        "log"
    ]
    for table_name in table_names:
        create_table_if_not_exists(table_name)
if __name__ == "__main__":
    # Call create_tables() function to create the tables if they don't exist
    create_tables()
