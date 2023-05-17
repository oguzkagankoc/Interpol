CREATE TABLE IF NOT EXISTS personal_informations (
    entity_id VARCHAR(20) PRIMARY KEY NOT NULL,
    forename VARCHAR(50),
    name VARCHAR(50),
    sex_id VARCHAR(10),
    date_of_birth DATE,
    place_of_birth VARCHAR(100),
    country_of_birth_id VARCHAR(50),
    weight DECIMAL,
    height DECIMAL,
    distinguishing_marks VARCHAR(1000),
    eyes_colors_id VARCHAR(20),
    hairs_id VARCHAR(20),
    is_active BOOLEAN NOT NULL,
    thumbnail TEXT
);

CREATE TABLE IF NOT EXISTS language_informations (
    language_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    languages_spoken_id VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS nationality_informations (
    nationality_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    nationality VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS arrest_warrant_informations (
    arrest_warrant_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    issuing_country_id VARCHAR(30),
    charge VARCHAR(1000),
    charge_translation VARCHAR(1000)
);

CREATE TABLE IF NOT EXISTS picture_informations (
    picture_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    picture_url VARCHAR(200),
    picture_base64 TEXT
);

CREATE TABLE IF NOT EXISTS change_log (
    log_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    table_name VARCHAR(50) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    description TEXT,
    change_date TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES personal_informations (entity_id)
);

CREATE TABLE IF NOT EXISTS log (
    log_id INTEGER PRIMARY KEY,
    entity_id VARCHAR(20) REFERENCES personal_informations (entity_id),
    table_name VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    column_data JSONB,
    description TEXT,
    FOREIGN KEY (entity_id) REFERENCES personal_informations (entity_id)
);
