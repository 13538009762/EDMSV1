from app import create_app
from app.extensions import db
from app.models import Department

app = create_app()
with app.app_context():
    corrections = {
        "Executive Office": "总经理办公室",
        "Research & Development": "研发部",
        "Human Resources": "人力资源部",
        "Finance": "财务部",
        "Publicity Department": "宣传部门"
    }
    
    depts = Department.query.all()
    for d in depts:
        if d.name_en in corrections:
            print(f"Updating ID {d.id}: {d.name} ({d.name_en}) -> {corrections[d.name_en]}")
            d.name = corrections[d.name_en]
        else:
            print(f"No correction for ID {d.id}: {d.name} ({d.name_en})")
            
    db.session.commit()
    print("Done.")
