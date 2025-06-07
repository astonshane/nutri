from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from fatsecret import Fatsecret

db = SQLAlchemy()
# fs = Fatsecret()


def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    # Initialize Database Plugin
    db.init_app(app)

    with app.app_context():
        from . import routes  # Import routes

        db.create_all()  # Create database tables for our data models

        return app