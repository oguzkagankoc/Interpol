from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_creation import (
    PersonalInformation,
    ChangeLogInformation,
    PictureInformation,
    ArrestWarrantInformation,
    NationalityInformation,
    LanguageInformation,
)

engine = create_engine(
    "postgresql+psycopg2://postgres:122333@localhost:5432/task"
)

Session = sessionmaker(bind=engine)
session = Session()

entity_classes = [    LanguageInformation,    NationalityInformation,    ArrestWarrantInformation,    PictureInformation,    ChangeLogInformation,    PersonalInformation,]

for entity_class in entity_classes:
    entity_ids = session.query(entity_class.entity_id).all()
    entity_ids = [entity_id[0] for entity_id in entity_ids]
    for entity_id in entity_ids:
        session.query(entity_class).filter_by(entity_id=entity_id).delete()

session.commit()
