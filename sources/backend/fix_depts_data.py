from app import create_app
from app.extensions import db
from app.models import Department

app = create_app()
with app.app_context():
    updates = [
        (1, "总经办", "Executive Office"),
        (2, "研发部", "Research & Development"),
        (3, "人力资源部", "Human Resources"),
        (4, "财务部", "Finance"),
        (5, "宣传部门", "Publicity Department"),
    ]
    for dept_id, name, name_en in updates:
        d = db.session.get(Department, dept_id)
        if d:
            d.name = name
            d.name_en = name_en
            print(f"Updated Dept {dept_id}: {name} / {name_en}")
    db.session.commit()
