import sys
import os

# Add sources/backend to sys.path
sys.path.append(os.path.abspath('sources/backend'))

try:
    from app import create_app
    from app.extensions import db
    from app.models import User
    
    app = create_app()
    with app.app_context():
        print("Backend Initialization: OK")
        # Test a simple query
        user_count = User.query.count()
        print(f"Database connectivity: OK (User count: {user_count})")
        
except Exception as e:
    print("\n--- BACKEND CRASH DETECTED ---")
    import traceback
    traceback.print_exc()
    sys.exit(1)
