import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
from dotenv import load_dotenv

load_dotenv()

MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_RECIPIENTS = os.getenv('MAILGUN_RECIPIENTS')

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    role = SelectField('Role?', choices=[('Administrator', 'Administrator'), ('Moderator', 'Moderator'), ('User', 'User')])
    submit = SubmitField('Submit')


def send_email(name, prontuario):
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Sua Aplicação <mailgun@{MAILGUN_DOMAIN}>",
            "to": MAILGUN_RECIPIENTS.split(','),
            "subject": "Novo Usuário Cadastrado",
            "text": f"""
            Um novo usuário foi cadastrado!

            Nome: {name}
            Prontuário: {prontuario}
            """
        }
    )

    if response.status_code != 200:
        error_message = f"Status code: {response.status_code}, Resposta: {response.text}"
        raise Exception(error_message)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    users = User.query.all()
    roles = Role.query.all()

    user_by_role = []
    for role in roles:
        obj_rel = {
            'role': role.name,
            'users': role.users.all()
        }
        user_by_role.append(obj_rel)

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            role = Role.query.filter_by(name=form.role.data).first()
            user = User(username=form.name.data, role=role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            flash('You were successfully registered.')
            send_email(form.name.data, "PT123456")
