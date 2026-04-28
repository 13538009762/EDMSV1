import os
from app import create_app
from app.extensions import db
from app.models import User, Department, Document

# Mock environment for fresh init
os.environ['DATABASE_URL'] = 'sqlite:///test_fresh_init.db'

app = create_app()
with app.app_context():
    print("--- Starting Fresh Init Test ---")
    try:
        # 1. Clean start
        if os.path.exists('test_fresh_init.db'):
            os.remove('test_fresh_init.db')
        
        # 2. Run create_all
        db.create_all()
        print("[SUCCESS] db.create_all success")
        
        # 3. Check for admin (should have been created by _bootstrap_admin in app context)
        # Note: _bootstrap_admin is called inside with app.app_context() in __init__.py
        admin = User.query.filter_by(login_name='admin').first()
        if admin:
            print(f"[SUCCESS] Admin user found: {admin.login_name}, Dept: {admin.department.name if admin.department else 'None'}")
        else:
            print("[ERROR] Admin user NOT found after init")
            
        # 4. Check for default department
        dept = Department.query.first()
        if dept:
            print(f"[SUCCESS] Default department found: {dept.name}")
        else:
            print("[ERROR] Default department NOT found after init")

        print("--- Test Completed ---")
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists('test_fresh_init.db'):
            # os.remove('test_fresh_init.db') # Keep for inspection if needed
            pass
