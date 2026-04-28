from app import create_app
from app.models import User
from flask import request

app = create_app()
with app.app_context():
    # Simulate a search for 'linyuan'
    search_term = 'linyuan'
    s = f"%{search_term}%"
    query = User.query.filter_by(registration_status='active')
    query = query.filter(
        (User.first_name.like(s)) | 
        (User.last_name.like(s)) |
        (User.login_name.like(s)) |
        (User.employee_no.like(s))
    )
    users = query.all()
    print(f"Search for '{search_term}' found {len(users)} users:")
    for u in users:
        print(f"Match: {u.login_name}")

    # Simulate a search for '何 欢恒'
    search_term = '何 欢恒'
    s = f"%{search_term.strip()}%"
    query = User.query.filter_by(registration_status='active')
    from sqlalchemy import func
    query = query.filter(
        (User.first_name.like(s)) | 
        (User.last_name.like(s)) |
        (User.login_name.like(s)) |
        (User.employee_no.like(s)) |
        (User.position_short.like(s)) |
        (func.concat(User.last_name, User.first_name).like(s)) |
        (func.concat(User.last_name, " ", User.first_name).like(s))
    )
    users = query.all()
    print(f"Search for '{search_term}' found {len(users)} users:")
    for u in users:
        print(f"Match: {u.login_name} ({u.last_name} {u.first_name})")
