from app import create_app
from app.extensions import db
from app.models import Department

app = create_app()
with app.app_context():
    depts = Department.query.all()
    for d in depts:
        print(f"ID: {d.id}, Name: {d.name}, Name_EN: {d.name_en}")
