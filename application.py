from flask import Flask, render_template, request
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
    # Kişi listesini veritabanından al
    page = request.args.get('page', 1, type=int)
    persons_query = PersonalInformation.query.order_by(PersonalInformation.name).paginate(page=page, per_page=5)
    persons = persons_query.items
    # Sayfalama için gerekli bilgileri oluştur
    pages = range(1, persons_query.pages + 1)
    next_url = None
    if persons_query.has_next:
        next_url = f'/results?page={persons_query.next_num}'
    prev_url = None
    if persons_query.has_prev:
        prev_url = f'/results?page={persons_query.prev_num}'
    return render_template('results.html', persons=persons, pagination=persons_query, pages=pages, next_url=next_url, prev_url=prev_url)

if __name__ == '__main__':
    app.run(debug=True)
