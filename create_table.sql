CREATE TABLE IF NOT EXISTS personal_informations (
  entity_id VARCHAR(20) NOT NULL PRIMARY KEY,
  forename VARCHAR(50),
  name VARCHAR(50),
  sex_id VARCHAR(10),
  date_of_birth DATE,
  place_of_birth VARCHAR(100),
  country_of_birth_id VARCHAR(50),
  weight NUMERIC(5, 2),
  height NUMERIC(5, 2),
  distinguishing_marks VARCHAR(1000),
  eyes_colors_id VARCHAR(20),
  hairs_id VARCHAR(20),
  is_active BOOLEAN NOT NULL,
  thumbnail TEXT
);

CREATE TABLE IF NOT EXISTS language_informations (
  language_id SERIAL PRIMARY KEY,
  entity_id VARCHAR(20) NOT NULL,
  languages_spoken_id VARCHAR(20),
  FOREIGN KEY (entity_id)
    REFERENCES personal_informations (entity_id)
);

CREATE TABLE IF NOT EXISTS nationality_informations (
  nationality_id SERIAL PRIMARY KEY,
  entity_id VARCHAR(20) NOT NULL,
  nationality VARCHAR(30),
  FOREIGN KEY (entity_id)
    REFERENCES personal_informations (entity_id)
);

CREATE TABLE IF NOT EXISTS arrest_warrant_informations (
  arrest_warrant_id SERIAL PRIMARY KEY,
  entity_id VARCHAR(20) NOT NULL,
  issuing_country_id VARCHAR(30),
  charge VARCHAR(1000),
  charge_translation VARCHAR(1000),
  FOREIGN KEY (entity_id)
    REFERENCES personal_informations (entity_id)
);

CREATE TABLE IF NOT EXISTS picture_informations (
  picture_id SERIAL PRIMARY KEY,
  entity_id VARCHAR(20) NOT NULL,
  picture_url VARCHAR(200),
  picture_base64 TEXT,
  FOREIGN KEY (entity_id)
    REFERENCES personal_informations (entity_id)
);

CREATE TABLE IF NOT EXISTS change_log (
  log_id SERIAL PRIMARY KEY,
  entity_id VARCHAR(20) NOT NULL,
  table_name VARCHAR(50) NOT NULL,
  field_name VARCHAR(50) NOT NULL,
  old_value TEXT,
  new_value TEXT,
  description TEXT,
  change_date TIMESTAMP,
  FOREIGN KEY (entity_id)
    REFERENCES personal_informations (entity_id)
);
