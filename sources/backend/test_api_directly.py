from app import create_app
from app.extensions import db
from app.models.core import User
import json

app = create_app()
client = app.test_client()

with app.app_context():
    admin = User.query.filter_by(login_name='admin').first()
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=admin.login_name)
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = client.get('/api/dashboard/stats', headers=headers)
    print(f"Status: {response.status_code}")
    try:
        data = response.get_json()
        print("Keys:", data.keys() if data else "None")
        if data and 'error' in data:
            print("Error:", data['error'])
    except:
        print("Response body:", response.data[:200])
