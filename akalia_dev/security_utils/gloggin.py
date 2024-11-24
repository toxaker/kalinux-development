import logging
from datetime import datetime

logging.basicConfig(filename="logs/app.log", level=logging.INFO)


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{timestamp} - {message}")


def send_log_to_admin(admin_id, bot):
    with open("logs/app.log", "rb") as file:
        bot.send_file(admin_id, file)


def get_log_summary():
    with open("logs/app.log", "r") as file:
        logs = file.readlines()
    return f"Log Summary: {len(logs)} entries"


def clear_logs():
    with open("logs/app.log", "w") as file:
        file.write("")
