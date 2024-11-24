from flask_socketio import SocketIO, emit, disconnect
import psutil
import threading
import time
from flask_login import current_user

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")  # Allow cross-origin requests if needed

# Background task for emitting system metrics
def emit_system_metrics():
    while True:
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=None),  # Non-blocking call for CPU percent
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_received": psutil.net_io_counters().bytes_recv,
            },
        }
        socketio.emit("system_metrics", metrics, broadcast=True)  # Broadcast to all clients
        time.sleep(1)  # Emit every 1 second

# Start the metrics emitter in a background thread
thread = threading.Thread(target=emit_system_metrics, daemon=True)
thread.start()

# Handle client connection
@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        emit("error", {"data": "Unauthorized"})
        disconnect()
    else:
        emit("my response", {"data": "Connected to the server!"})
        print(f"Client connected: {current_user.get_id()}")

# Handle client disconnection
@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")
