from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Integer, Date, Boolean, Text, DateTime, DECIMAL
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
import psycopg2
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Değişkenlere erişim
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Veritabanı bağlantısı için URL oluştur
db_url = f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Engine oluştur
engine = create_engine(db_url)
insp = inspect(engine)
Base = declarative_base()
DBSession = sessionmaker(bind=engine)
session = DBSession()




class PersonalInformation(Base):
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

if not insp.has_table("personal_informations"):
    Base.metadata.tables['personal_informations'].create(engine)


class LanguageInformation(Base):
    __tablename__ = "language_informations"
    language_id = Column('language_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    languages_spoken_id = Column('languages_spoken_id', String(20))
    personal_informations = relationship(
        "PersonalInformation", backref="language", lazy=True, foreign_keys=[entity_id])


if not insp.has_table("language_informations"):
    Base.metadata.tables['language_informations'].create(engine)


class NationalityInformation(Base):
    __tablename__ = "nationality_informations"
    nationality_id = Column('nationality_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    nationality = Column('nationality', String(30))
    personal_informations = relationship(
        "PersonalInformation", backref="nationality", lazy=True, foreign_keys=[entity_id])


if not insp.has_table("nationality_informations"):
    Base.metadata.tables['nationality_informations'].create(engine)


class ArrestWarrantInformation(Base):
    __tablename__ = "arrest_warrant_informations"
    arrest_warrant_id = Column('arrest_warrant_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    issuing_country_id = Column('issuing_country_id', String(30))
    charge = Column('charge', String(1000))
    charge_translation = Column('charge_translation', String(1000))
    personal_informations = relationship(
        "PersonalInformation", backref="arrest_warrant", lazy=True, foreign_keys=[entity_id])


if not insp.has_table("arrest_warrant_informations"):
    Base.metadata.tables['arrest_warrant_informations'].create(engine)


class PictureInformation(Base):
    __tablename__ = "picture_informations"
    picture_id = Column('picture_id', Integer, primary_key=True)
    entity_id = Column('entity_id', String(20), ForeignKey(
        "personal_informations.entity_id"))
    picture_url = Column('picture_url', String(200))
    picture_base64 = Column('picture_base64', Text)
    personal_informations = relationship(
        "PersonalInformation", backref="picture_of_the_criminal", lazy=True, foreign_keys=[entity_id])


if not insp.has_table("picture_informations"):
    Base.metadata.tables['picture_informations'].create(engine)


class ChangeLogInformation(Base):
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

if not insp.has_table("change_log"):
    Base.metadata.tables['change_log'].create(engine)

class LogInformation(Base):
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

if not insp.has_table("log"):
    Base.metadata.tables['log'].create(engine)