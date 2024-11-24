import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from .models import User

api_bp = Blueprint("routes", __name__)
limiter = Limiter(key_func=get_remote_address)


# Utility: Log visitor IP
def log_ip_access(endpoint_name):
    user_ip = (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For")
        or request.remote_addr
    )
    if user_ip:
        logging.info(f"Visitor with IP {user_ip} accessed {endpoint_name}")
    else:
        logging.warning(f"Unable to retrieve visitor's IP address for {endpoint_name}")


# Authentication Routes
@api_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("routes.secure_home"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@api_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.login"))


# Public Pages
@api_bp.route("/")
@limiter.limit("5 per minute")
def index():
    log_ip_access("Index Page")
    return render_template("index.html")


@api_bp.route("/home")
@limiter.limit("10 per minute")
def home():
    log_ip_access("Home Page")
    return render_template("home.html")


@api_bp.route("/clientside")
def clientside():
    log_ip_access("Client-Side Page")
    return render_template("clientside4.html")


@api_bp.route("/toolsmenu")
def toolsmenu():
    log_ip_access("Tools Menu")
    return render_template("toolsmenu.html")


@api_bp.route("/info")
def info():
    log_ip_access("Information Page")
    return render_template("info.html")


@api_bp.route("/scantools")
def scantools():
    log_ip_access("Scan Tools Page")
    return render_template("scantools.html")


@api_bp.route("/webtools")
def webtools():
    log_ip_access("Web Tools Page")
    return render_template("webtools.html")


@api_bp.route("/tutorial")
def tutorial():
    log_ip_access("Tutorial Page")
    return render_template("tutorial.html")


@api_bp.route("/faq")
def faq():
    log_ip_access("FAQ Page")
    return render_template("faq.html")


@api_bp.route("/help")
def help():
    log_ip_access("Help Page")
    return render_template("help.html")


@api_bp.route("/webdownload")
def webdownload():
    log_ip_access("Web Download Page")
    return render_template("webdownload.html")


@api_bp.route("/hisecurity")
def hisecurity():
    log_ip_access("High Security Page")
    return render_template("hisecurity.html")


# Secure Section: Requires Login
@api_bp.route("/secure/")
@login_required
def secure_home():
    """
    Home page for the secure area.
    """
    log_ip_access("Secure Home Page")
    return render_template("secure_home.html", title="Secure Area")


@api_bp.route("/secure/page1")
@login_required
def secure_page1():
    """
    First additional secure page.
    """
    log_ip_access("Secure Page 1")
    return render_template("secure_page1.html", title="Secure Page 1")


@api_bp.route("/secure/page2")
@login_required
def secure_page2():
    """
    Second additional secure page.
    """
    log_ip_access("Secure Page 2")
    return render_template("secure_page2.html", title="Secure Page 2")
