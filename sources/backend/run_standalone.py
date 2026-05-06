from app import create_app, socketio
import os
import sys

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = create_app()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   EDMS Backend Standalone Server")
    print("="*50)
    print(" * AI Question & Answer logging is ACTIVE")
    print(" * Backend Console will display all AI interactions")
    print(" * Access history at: http://127.0.0.1:5000/api/ai/history")
    print("="*50 + "\n")

    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5000, 
        debug=True, 
        allow_unsafe_werkzeug=True
    )
