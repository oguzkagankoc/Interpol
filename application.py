from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:122333@localhost:5432/task'
db = SQLAlchemy(app)

class PersonalInformation(db.Model):
    __tablename__ = "personal_informations"
    entity_id = db.Column(db.String(20), primary_key=True, nullable=False)
    forename = db.Column(db.String(50))
    name = db.Column(db.String(50))
    sex_id = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    place_of_birth = db.Column(db.String(100))
    country_of_birth_id = db.Column(db.String(50))
    weight = db.Column(db.Numeric(5, 2))
    height = db.Column(db.Numeric(5, 2))
    distinguishing_marks = db.Column(db.String(1000))
    eyes_colors_id = db.Column(db.String(20))
    hairs_id = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, nullable=False)
    thumbnail = db.Column(db.Text)

@app.route('/results')
def results():
    persons = PersonalInformation.query.all()
    print(persons)
    has_next = False
    return render_template('results.html', persons=persons, has_next=has_next)

if __name__ == '__main__':
    app.run(debug=True)

