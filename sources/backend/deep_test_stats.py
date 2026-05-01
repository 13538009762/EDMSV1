from app import create_app
from app.extensions import db
from app.models.core import User
import json

app = create_app()
with app.app_context():
    # Bypass JWT by calling the inner logic
    from app.api.dashboard import get_stats
    # We can't easily call the decorated function, but we can call its __wrapped__ if it's using wraps
    # Or just mock the JWT parts.
    
    import flask_jwt_extended
    original_verify = flask_jwt_extended.verify_jwt_in_request
    flask_jwt_extended.verify_jwt_in_request = lambda *args, **kwargs: None
    
    import app.utils.auth as auth_utils
    original_current_user = auth_utils.current_user
    admin = User.query.filter_by(login_name='admin').first()
    auth_utils.current_user = lambda: admin
    
    try:
        # We need to simulate a request context for jsonify to work
        with app.test_request_context():
            resp = get_stats()
            if hasattr(resp, 'get_json'):
                data = resp.get_json()
            else:
                data = json.loads(resp.data)
            print("SUCCESS")
            print(json.dumps(data, indent=2)[:500] + "...")
    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()
    finally:
        flask_jwt_extended.verify_jwt_in_request = original_verify
        auth_utils.current_user = original_current_user
