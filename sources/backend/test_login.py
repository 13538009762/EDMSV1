from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    login_name = 'ruk1'
    user = User.query.filter_by(login_name=login_name).first()
    print(f"User.query.filter_by(login_name='{login_name}').first() result: {user}")
    
    # Try case sensitivity
    user_case = User.query.filter(User.login_name.ilike(login_name)).first()
    print(f"ILike result: {user_case}")
    
    # Check for all users starting with ruk
    ruks = User.query.filter(User.login_name.like('ruk%')).all()
    print(f"Users starting with 'ruk': {[u.login_name for u in ruks]}")
