from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   EDMS Backend WSGI Server")
    print("="*50)
    print(" * AI Question & Answer logging is ACTIVE")
    print(" * Backend Console will display all AI interactions")
    print("="*50 + "\n")

    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5000, 
        debug=True, 
        allow_unsafe_werkzeug=True,
        use_reloader=False  # Prevent double-init issues with thread pool
    )
