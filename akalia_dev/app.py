from aka_app import create_app
from socketio_app import socketio  # Import your SocketIO instance

# Ensure the correct module search path
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create the Flask app
app = create_app()

# Integrate Flask app with SocketIO
socketio.init_app(app, cors_allowed_origins="*")  # Allow cross-origin requests for development

if __name__ == "__main__":
    # Run the app with SocketIO
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
