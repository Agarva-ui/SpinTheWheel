# ============================================================
# Imports
# ============================================================
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import random
import os
import smtplib
from email.mime.text import MIMEText
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_socketio import SocketIO, emit

# ============================================================
# Profanity Filtering
# ============================================================
SWEAR_WORDS = [
    "motherfucker", "fucking", "asshole", "bastard", "sharmota", "mutanakk",
    "mokhannath", "douche", "bitch", "whore", "slut", "damn", "fuck", "shit",
    "dick", "crap", "piss", "ass", "mom", "كس", "زب", "نيك", "طيز", "شرموط",
    "لعنة", "قحبة", "خرا", "متناك", "مخنث", "مومس", "هرم", "كلب", "كلبة",
    "شرموط", "والد"
]

SWEAR_WORDS = sorted(set(SWEAR_WORDS), key=lambda w: -len(w))

_regex_cache = []
for word in SWEAR_WORDS:
    escaped = re.escape(word)
    chunk_chars = r'(?:[^A-Za-z\u0600-\u06FF0-9])*'
    spaced = chunk_chars.join(list(escaped))
    try:
        pattern = re.compile(spaced, re.IGNORECASE | re.UNICODE)
    except re.error:
        spaced_fallback = r'\W*'.join(list(escaped))
        pattern = re.compile(spaced_fallback, re.IGNORECASE)
    _regex_cache.append(pattern)


def filter_message(text: str, mask: bool = True) -> str:
    if not text:
        return text
    cleaned = text
    replacement = '***' if mask else ''
    for pat in _regex_cache:
        cleaned = pat.sub(replacement, cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def contains_profanity(text: str) -> bool:
    if not text:
        return False
    for pat in _regex_cache:
        if pat.search(text):
            return True
    return False


# ============================================================
# Theme Colors
# ============================================================
theme_colors = [
    "#d4af37", "#cda434", "#b8860b", "#f5d76e",
    "#e5c07b", "#8b7500", "#2b2b2b"
]

# ============================================================
# Flask App Setup
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

socketio = SocketIO(app, cors_allowed_origins="*")
Bootstrap5(app)

# ============================================================
# Database Configuration
# ============================================================
uri = os.environ.get("DB_URI", "sqlite:///prize.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}

db = SQLAlchemy(app)

# ============================================================
# Flask-Login Setup
# ============================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ============================================================
# Database Models
# ============================================================
class Prize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)


class VipPrize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)

class Messages_vip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

# ============================================================
# Flask-WTF Forms
# ============================================================
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class PrizeForm(FlaskForm):
    label = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Add Customer")

class DeleteUserForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Delete Customer")

# ============================================================
# Routes
# ============================================================
@app.route("/", methods=["GET", "POST"])
def Home():
    NormalForm = PrizeForm(prefix="normal")
    VipForm = PrizeForm(prefix="vip")
    DeleteForm = DeleteUserForm()

     # Normal prizes
    if NormalForm.validate_on_submit() and NormalForm.submit.data:
        label = NormalForm.label.data
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        db.session.add(Prize(label=label, color=color))
        db.session.commit()
        return redirect(url_for("Home"))
    
     # VIP prizes
    if VipForm.validate_on_submit() and VipForm.submit.data:
        label = VipForm.label.data
        color = random.choice(theme_colors)
        db.session.add(VipPrize(label=label, color=color))
        db.session.commit()
        return redirect(url_for("VIP"))
    
    # Delete user
    if DeleteForm.validate_on_submit():
        username = DeleteForm.username.data.strip()
        deleted = Prize.query.filter_by(label=username).delete()
        db.session.commit()

        return redirect(url_for("Home"))
    messages = Messages.query.all()
    prizes = Prize.query.all()
    return render_template("index.html", prizes=prizes,
                           is_authenticated=current_user.is_authenticated,
                           messages=messages,
                           NormalForm=NormalForm, 
                           VipForm=VipForm,
                           DeleteUserForm=DeleteForm)


@app.route("/VIP", methods=["GET", "POST"])
def VIP():
    messages = Messages_vip.query.all()
    prizes = VipPrize.query.all()
    return render_template("vip.html", prizes=prizes,
                           is_authenticated=current_user.is_authenticated,
                           messages=messages)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("Home"))

    user_count = User.query.count()
    form = RegisterForm() if user_count == 0 else LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = request.form.get("password")

        # Registration if no users exist
        if user_count == 0:
            admin_user = User(username=username)
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            flash("Admin registered successfully. Please log in.", "success")
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for("Home"))
            else:
                flash("Invalid username or password.", "danger")

    return render_template("login.html", form=form, user_count=user_count)

MY_EMAIL = os.environ.get("email")
PASSWORD = os.environ.get("email_password")
@app.route("/info/<text>", methods=["GET", "POST"])
def info(text):
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=PASSWORD)
        msg = MIMEText(f"This user finished their purchase: {text}")
        msg["Subject"] = "Purchase Notification"
        msg["From"] = MY_EMAIL
        msg["To"] = os.environ.get("to_email")
        connection.send_message(msg)
    return "Email sent!", 200

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/delete_all")
@login_required
def delete_all():
    Prize.query.delete()
    db.session.commit()
    return redirect(url_for("Home"))

@app.route("/VIP/delete_all")
@login_required
def delete_all_vip():
    VipPrize.query.delete()
    db.session.commit()
    return redirect(url_for("VIP"))

@app.route("/delete_messages")
@login_required
def delete_messages():
    Messages.query.delete()
    db.session.commit()
    return redirect(url_for("Home"))

@app.route("/VIP/delete_messages")
@login_required
def delete_messages_vip():
    Messages_vip.query.delete()
    db.session.commit()
    return redirect(url_for("VIP"))

# ============================================================
# Socket.IO Events
# ============================================================
@socketio.on("spin")
def handle_spin():
    if not current_user.is_authenticated:
        return
    prizes = Prize.query.all()
    if not prizes:
        return
    chosen = random.choice(prizes)
    index = prizes.index(chosen)
    emit("wheelSpin", {
        "label": chosen.label,
        "color": chosen.color,
        "index": index
    }, broadcast=True)


@socketio.on("spin_vip")
def handle_spin_vip():
    if not current_user.is_authenticated:
        return
    prizes = VipPrize.query.all()
    if not prizes:
        return
    chosen = random.choice(prizes)
    index = prizes.index(chosen)
    emit("wheelSpin_vip", {
        "label": chosen.label,
        "color": chosen.color,
        "index": index
    }, broadcast=True)


@socketio.on('send_message')
def handle_message(data):
    filtered_msg = filter_message(data['message'], mask=False)
    if not filtered_msg.strip():
        return
    db.session.add(Messages(message=filtered_msg))
    db.session.commit()
    data['message'] = filtered_msg
    emit('receive_message', data, broadcast=True)


@socketio.on('send_message_vip')
def handle_message_vip(data):
    filtered_msg = filter_message(data['message'], mask=False)
    if not filtered_msg.strip():
        return
    db.session.add(Messages(message=filtered_msg))
    db.session.commit()
    data['message'] = filtered_msg
    emit('receive_message_vip', data, broadcast=True)


# ============================================================
# Run App
# ============================================================
if __name__ == "__main__":
    socketio.run(app, debug=False)
