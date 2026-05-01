from app import create_app
from app.extensions import db
from app.models.core import User
from flask import jsonify
import json

app = create_app()
with app.app_context():
    from app.api.dashboard import get_stats
    from flask import Flask, request
    
    # Mock a request for admin
    with app.test_request_context():
        from flask_jwt_extended import create_access_token, set_access_cookies
        admin = User.query.filter_by(login_name='admin').first()
        token = create_access_token(identity=admin.login_name)
        
        # We need to mock current_user() which uses verify_jwt_in_request
        # This is complex in a script. Let's just try to run the function logic directly.
        
        from app.utils.auth import current_user
        # Since we are in app context but not in a real request with JWT, 
        # we might need to mock current_user
        
        import app.api.dashboard as dashboard_mod
        original_current_user = dashboard_mod.current_user
        dashboard_mod.current_user = lambda: admin
        
        try:
            resp = get_stats()
            print("Response status:", resp[1] if isinstance(resp, tuple) else "200")
            data = resp.get_json() if hasattr(resp, 'get_json') else json.loads(resp.data)
            print("Data keys:", data.keys())
            print("Total users:", data.get('total_users'))
            print("Total docs:", data.get('total_docs'))
        except Exception as e:
            import traceback
            print(f"Failed: {e}")
            traceback.print_exc()
        finally:
            dashboard_mod.current_user = original_current_user
