from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit

# ------------------------------
# Flask App & DB Setup
# ------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

socketio = SocketIO(app, cors_allowed_origins="*")

# Database
uri = os.environ.get("DB_URI", "sqlite:///prize.db")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': NullPool # <--- CORRECTED
}
db = SQLAlchemy(app)
Bootstrap5(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to login page if not authenticated

# ------------------------------
# Database Models
# ------------------------------
class Prize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)  # Store hashed passwords

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ------------------------------
# Flask-WTF Forms
# ------------------------------
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PrizeForm(FlaskForm):
    label = StringField("Prize Label", validators=[DataRequired()])
    submit = SubmitField("Add Prize")

# ------------------------------
# Routes
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def Home():
    user_count = User.query.count()
    form = RegisterForm()
    
    if user_count == 0 and form.validate_on_submit():
        username = form.username.data
        password = request.form.get("password")
        admin_user = User(username=username)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        flash("Admin registered successfully. Please log in.", "success")
        return redirect(url_for("login"))
    
    prizes = Prize.query.all()
    return render_template(
        "index.html", 
        prizes=prizes, 
        user_count=user_count, 
        form=form, 
        is_authenticated=current_user.is_authenticated
    )

@app.route("/add_prize", methods=["GET", "POST"])
@login_required
def add_prize():
    form = PrizeForm()
    if form.validate_on_submit():
        label = form.label.data
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        prize = Prize(label=label, color=color)
        db.session.add(prize)
        db.session.commit()
        return redirect(url_for("Home"))
    return render_template("add.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("Home"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("Home"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)

@socketio.on("spin")
def handle_spin():
    if not current_user.is_authenticated:
        return
    prizes = Prize.query.all()
    if not prizes:
        return
    chosen = random.choice(prizes)
    index = prizes.index(chosen)  # position in the sectors list
    emit("wheelSpin", {
        "label": chosen.label,
        "color": chosen.color,
        "index": index
    }, broadcast=True)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/delete_all")
@login_required
def delete_all():
    # Delete all Prize rows
    Prize.query.delete()
    db.session.commit()
    return redirect(url_for("Home"))

# ------------------------------
# Run App
# ------------------------------

if __name__ == "__main__":
    socketio.run(app, debug=False)
