import socket
import psutil
import shutil
import smtplib
import re
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from loguru import logger
import logging
import random
import time
from redis import Redis
import os
import logging
import subprocess
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import requests
import aiohttp
import asyncio

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("ADMIN_ID")
API_URL = os.getenv("API_URL")
WEB_APP_URL = os.getenv("WEB_APP_URL")
WEB_DOWNLOAD_URL = os.getenv("WEB_DOWNLOAD_URL")
TUTORIAL_URL = os.getenv("TUTORIAL_URL")


# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка наличия токена
if not TOKEN:
    logger.error("Токен не загружен! Проверьте файл .env")

# Глобальная переменная для статуса аутентификации
authenticated_users = {}


# Полный список команд для помощи
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/info - Информация о боте\n"
        "/web - Перейти в приложение\n"
        "/webdownload - Скачать приложение\n"
        "/tutorial - Документация\n"
        "/send_main_menu - В главное меню\n"
        "/enter_token - Ввести API ключ\n"
        "/bye - Завершить работу с ботом\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception in {update}: {context.error}")
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Произошла ошибка! Сообщение отправлено разработчику.",
        )


async def api_authenticated_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    authenticated_menu_buttons = [
        [
            InlineKeyboardButton(
                "🛠 Управление сервером", callback_data="server_management"
            ),
            InlineKeyboardButton("📄 Помощь", callback_data="help"),
        ],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="API ключ принят. Выберите действие:",
        reply_markup=InlineKeyboardMarkup(authenticated_menu_buttons),
    )


async def default_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    default_menu_text = "Ассалам алейкум, брат! Добро пожаловать."
    default_menu_buttons = [
        [InlineKeyboardButton("🔑 Ввести API", callback_data="enter_token")],
        [
            InlineKeyboardButton(
                "💻 Приложение", url="https://t.me/kalinuxsecurity_bot/application_tg"
            )
        ],
        [
            InlineKeyboardButton(
                "💠 Установить...", url="https://kalinux.org.ru/webdownload"
            )
        ],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")],
        [InlineKeyboardButton("📋 Список команд", callback_data="help")],
        [
            InlineKeyboardButton(
                "📚 Гайд 'Быстрый старт'", url="https://kalinux.org.ru/tutorial"
            )
        ],
        [InlineKeyboardButton("👋 Завершить", callback_data="bye")],
        [
            InlineKeyboardButton(
                "🛠 Управление сервером", callback_data="server_management"
            )
        ],
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=default_menu_text,
        reply_markup=InlineKeyboardMarkup(default_menu_buttons),
    )


# Полное меню управления сервером
async def server_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server_menu_buttons = [
        [InlineKeyboardButton("🛠 Мониторинг", callback_data="monitor")],
        [InlineKeyboardButton("🛡 Статус Брандмауэра", callback_data="firewall_status")],
        [InlineKeyboardButton("📋 Задачи", callback_data="tasks_setting")],
        [InlineKeyboardButton("📤 Отправить отчёт", callback_data="send_scan_report")],
        [InlineKeyboardButton("💻 Информация о системе", callback_data="system_info")],
        [InlineKeyboardButton("🧹 Очистка диска", callback_data="disk_cleanup")],
        [InlineKeyboardButton("🔄 Перезагрузить сервис", callback_data="restart_service")],
        [InlineKeyboardButton("⚙️ Проверка состояния сервера", callback_data="server_health_check")],
        [InlineKeyboardButton("📩 Отправить отчёт администратору", callback_data="send_system_report")],
        [InlineKeyboardButton("👋 Завершить", callback_data="bye")],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="<b>Выберите действие:</b>",
        reply_markup=InlineKeyboardMarkup(server_menu_buttons),
        parse_mode="HTML",
    )


# Команда для старта, запускается при первом использовании бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /help to get a command list or use buttons"
    )
    await default_menu(update, context)


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Этот бот помогает управлять системой безопасности вашего сервера"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Этот бот помогает управлять системой безопасности вашего сервера",
        )


async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать! Пожалуйста, введите API ключ для доступа к функциям бота."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Посетить приложения разработчика можно тут: {WEB_APP_URL}",
        )


async def webdownload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать! Пожалуйста, введите API ключ для доступа к функциям бота."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Скачать приложение: WEB_DOWNLOAD_URL",
        )


async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(
            "Добро пожаловать! Пожалуйста, введите API ключ для доступа к функциям бота."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Документация: {TUTORIAL_URL}"
        )


# Ввод API ключа и проверка
async def enter_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(text=help_text)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, отправьте ваш API ключ."
        )


async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text
    # Проверка API ключа
    if token == BOT_TOKEN:  # Замените на реальную проверку
        authenticated_users[update.effective_chat.id] = True
        await api_authenticated_menu(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Poshel nahuy)"
        )


# Кнопки основного меню задач
async def tasks_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks_setting_buttons = [
        [InlineKeyboardButton("📝 Отчёт проверки", callback_data="scan_report")],
        [InlineKeyboardButton("🔄 Запустить задачу", callback_data="start_task")],
        [InlineKeyboardButton("⏹ Остановить задачу", callback_data="stop_task")],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="main_menu")],
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите действие для задач:",
        reply_markup=InlineKeyboardMarkup(tasks_setting_buttons),
    )


# Основной обработчик кнопок с условием для вызова меню и команд
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    elif query.data == "system_info":
        await system_info(update, context)
    elif query.data == "disk_cleanup":
        await disk_cleanup(update, context)
    elif query.data == "restart_service":
        await restart_service(update, context)
    elif query.data == "server_health_check":
        await server_health_check(update, context)
    elif query.data == "send_system_report":
        await send_system_report(update, context)
    elif query.data == "bye":
        await query.message.reply_text("До встречи!")
    elif query.data == "info":
        await info(update, context)
    elif query.data == "web":
        await web(update, context)
    elif query.data == "webdownload":
        await webdownload(update, context)
    elif query.data == "tutorial":
        await tutorial(update, context)
    if query.data == "enter_token":
        await enter_token(update, context)
    elif query.data == "server_management":
        await server_management_menu(update, context)
    elif query.data == "monitor":
        await monitor(update, context)
    elif query.data == "firewall_status":
        await firewall_status(update, context)
    elif query.data == "tasks_setting":
        await tasks_setting(update, context)
    elif query.data == "scan_report":
        await scan_report(update, context)
    elif query.data == "help":
        await help(update, context)  # вывод справочной информации
    elif query.data == "main_menu":
        await default_menu(update, context)  # возврат в главное меню



   

# ========== Network Utilities ==========


def get_server_ip():
    """Retrieve server's public and private IP addresses."""
    try:
        hostname = socket.gethostname()
        private_ip = socket.gethostbyname(hostname)
        public_ip = requests.get("https://api.ipify.org").text
        return {"private_ip": private_ip, "public_ip": public_ip}
    except Exception as e:
        logger.error(f"Error getting IPs: {e}")
        return {"error": str(e)}


async def ping_host(host):
    """Ping a host to check if it's reachable (async version)."""
    try:
        process = await asyncio.create_subprocess_shell(
            f"ping -c 1 {host}", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return f"{host} is reachable."
        else:
            return f"{host} is not reachable."
    except Exception as e:
        return f"Error pinging host: {e}"


# ========== System Monitoring Utilities ==========

async def system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = time.time() - psutil.boot_time()
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))

    system_info_text = (
        f"<b>System Information:</b>\n"
        f"<b>CPU Usage:</b> {cpu_usage}%\n"
        f"<b>Memory Usage:</b> {memory.percent}% ({memory.available / (1024 * 1024):.2f} MB free)\n"
        f"<b>Disk Usage:</b> {disk.percent}% ({disk.free / (1024 * 1024):.2f} MB free)\n"
        f"<b>Uptime:</b> {uptime_str}"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=system_info_text, parse_mode="HTML"
    )

# Function to trigger disk cleanup
async def disk_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Perform cleanup by deleting unnecessary files, temporary files, or logs.
    temp_dir = "/tmp"  # Example temp directory
    logs_dir = "/var/log"  # Example logs directory
    cleanup_logs = []

    for directory in [temp_dir, logs_dir]:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    cleanup_logs.append(f"Deleted {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    cleanup_logs.append(f"Deleted directory {file_path}")
            except Exception as e:
                cleanup_logs.append(f"Failed to delete {file_path}: {e}")

    cleanup_report = "\n".join(cleanup_logs) if cleanup_logs else "No files to clean."
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<b>Disk Cleanup Complete:</b>\n{cleanup_report}",
        parse_mode="HTML",
    )

# Function to restart the bot
async def restart_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bot is restarting..."
    )

    # Perform restart (use system command or restart the bot application)
    os.execv(sys.argv[0], sys.argv)

# Function to check server health (check critical services)




# Function to send a system health report to admin
async def send_system_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    system_report = (
        "Generating system health report...\n\n"
        "CPU Usage, Memory Usage, Disk Usage, Uptime, and other critical information."
    )
    # Example report could include more detailed system stats
    await context.bot.send_message(
        chat_id=CHAT_ID, text=system_report, parse_mode="HTML"
    )
    await update.message.reply_text("System report has been sent to the admin.")

# Function to check if user is authenticated
async def check_authenticated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in authenticated_users:
        await update.message.reply_text("You are authenticated.")
    else:
        await update.message.reply_text("You are not authenticated.")

# Function to log out user (invalidate authentication)
async def logout_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in authenticated_users:
        del authenticated_users[update.effective_chat.id]
        await update.message.reply_text("You have been logged out.")
    else:
        await update.message.reply_text("You were not authenticated.")

def get_cpu_usage():
    """Get current CPU usage as a percentage."""
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    """Get memory usage stats."""
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "percent": memory.percent,
    }


def get_disk_usage(path="/"):
    """Get disk usage stats for a specified path."""
    disk = shutil.disk_usage(path)
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": (disk.used / disk.total) * 100,
    }


# ========== Security Utilities ==========


def check_firewall_status():
    """Check UFW firewall status and return results."""
    try:
        result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
        return (
            result.stdout if result.returncode == 0 else "Firewall status unavailable."
        )
    except Exception as e:
        logger.error(f"Error checking firewall: {e}")
        return f"Error: {str(e)}"


async def run_security_scan():
    """Run a combined security scan (e.g., chkrootkit, rkhunter)."""
    try:
        chkrootkit_proc = await asyncio.create_subprocess_shell(
            "chkrootkit", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        rkhunter_proc = await asyncio.create_subprocess_shell(
            "rkhunter --check", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        chkrootkit_result, _ = await chkrootkit_proc.communicate()
        rkhunter_result, _ = await rkhunter_proc.communicate()

        return f"chkrootkit results:\n{chkrootkit_result.decode()}\nrkhunter results:\n{rkhunter_result.decode()}"
    except Exception as e:
        logger.error(f"Error during security scan: {e}")
        return f"Security scan error: {e}"


# ========== Bot Administration Utilities ==========


async def send_alert_to_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send a critical alert to the administrator via Telegram."""
    await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 ALERT 🚨\n{message}")


async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send a system status report."""
    report = {
        "CPU Usage": f"{get_cpu_usage()}%",
        "Memory Usage": get_memory_usage(),
        "Disk Usage": get_disk_usage(),
        "Firewall Status": check_firewall_status(),
    }
    report_text = (
        f"System Status Report:\n"
        f"CPU Usage: {report['CPU Usage']}\n"
        f"Memory Usage: {report['Memory Usage']}\n"
        f"Disk Usage: {report['Disk Usage']}\n"
        f"Firewall Status:\n{report['Firewall Status']}"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=report_text)


# ========== Telegram Bot Handlers ==========


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command handler to get system information."""
    await generate_report(update, context)


async def firewall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Firewall status command handler."""
    status = check_firewall_status()
    await update.message.reply_text(f"Firewall Status:\n{status}")


async def monitor_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor CPU usage."""
    cpu_usage = get_cpu_usage()
    await update.message.reply_text(f"Current CPU usage: {cpu_usage}%")


async def monitor_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor memory usage."""
    memory = get_memory_usage()
    await update.message.reply_text(
        f"Memory Usage:\nTotal: {memory['total']}, Used: {memory['used']}, "
        f"Available: {memory['available']}, Usage: {memory['percent']}%"
    )


async def monitor_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor disk usage."""
    disk = get_disk_usage()
    await update.message.reply_text(
        f"Disk Usage:\nTotal: {disk['total']}, Used: {disk['used']}, "
        f"Free: {disk['free']}, Usage: {disk['percent']}%"
    )


async def perform_security_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform a security scan."""
    scan_result = await run_security_scan()
    await update.message.reply_text(f"Security Scan Results:\n{scan_result}")


# ========== Telegram Bot Customization ==========



# Default list of services to monitor
default_services = ["apache2", "nginx", "mysql"]

# Function to check the status of services
async def server_health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the services from the user's message or use default ones
    services_to_check = default_services
    if context.args:
        services_to_check = context.args

    # Check the status of each service
    health_report = []
    for service in services_to_check:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            service_status = result.stdout.decode().strip()

            if service_status == "active":
                health_report.append(f"<b>{service}</b> is <b>running</b>.")
            else:
                health_report.append(f"<b>{service}</b> is <b>NOT running</b>!")
        except Exception as e:
            health_report.append(f"<b>{service}</b> check failed: {str(e)}")

    # Send the health status to the user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\n".join(health_report),
        parse_mode="HTML",
    )

# Command to allow user to specify services to check
async def check_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await server_health_check(update, context)
    else:
        # If no service is specified, check default services
        await update.message.reply_text(
            "Please specify one or more services to check (e.g., /check_services apache2 mysql)"
        )
        # Optionally, provide a list of common services:
        await update.message.reply_text(
            "Common services: apache2, nginx, mysql, redis, postgresql."
        )
# Register the handler for the `/check_services` command
check_services_handler = CommandHandler("check_services", check_services)
dispatcher.add_handler(check_services_handler)


admin_id = os.getenv('ADMIN_ID')  # Replace with your admin Telegram user ID

# Function to allow the admin to set the list of services to monitor
async def set_monitored_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == admin_id:
        if context.args:
            # Update the services list with the new input
            global default_services
            default_services = context.args
            await update.message.reply_text(
                f"Monitored services updated: {', '.join(default_services)}"
            )
        else:
            await update.message.reply_text(
                "Please provide a list of services to monitor, separated by spaces (e.g., /set_monitored_services apache2 nginx mysql)."
            )
    else:
        await update.message.reply_text("You are not authorized to perform this action.")

# Register the handler for the `/set_monitored_services` command
set_monitored_services_handler = CommandHandler("set_monitored_services", set_monitored_services)
dispatcher.add_handler(set_monitored_services_handler)



# ========== Bot Setup ==========

if __name__ == "__main__":
    # Create the Telegram application and register handlers
    bot_app = ApplicationBuilder().token(TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("status", status))
    bot_app.add_handler(CommandHandler("firewall", firewall))
    bot_app.add_handler(CommandHandler("monitor_cpu", monitor_cpu))
    bot_app.add_handler(CommandHandler("monitor_memory", monitor_memory))
    bot_app.add_handler(CommandHandler("monitor_disk", monitor_disk))
    bot_app.add_handler(CommandHandler("security_scan", perform_security_scan))
    bot_app.add_handler(CommandHandler("info", info))
    bot_app.add_handler(CommandHandler("web", web))
    bot_app.add_handler(CommandHandler("webdownload", webdownload))
    bot_app.add_handler(CommandHandler("tutorial", tutorial))
    bot_app.add_handler(CommandHandler("help", help))
    bot_app.add_handler(CommandHandler("enter_token", enter_token))
    bot_app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_token_input)
    )
    bot_app.add_handler(CallbackQueryHandler(button))
    bot_app.add_error_handler(error_handler)

    bot_app.run_polling()


# Инициализация приложения Telegram
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()


if __name__ == "__main__":
    main()
