from flask.cli import with_appcontext
import os
import sys
from aka_app import create_app
from aka_app.socketio_app import start_background_task, socketio  # Correct imports

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create the Flask app
app = create_app()

# Integrate Flask app with SocketIO
socketio.init_app(app, cors_allowed_origins="*")  # Initialize with Flask app

# Start the background task after initialization
start_background_task(app)

if __name__ == "__main__":
    socketio.run(app, debug=True)
