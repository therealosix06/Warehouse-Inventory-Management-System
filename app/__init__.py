import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-this')

    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/wims_db'
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    from . import models
    from .routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app