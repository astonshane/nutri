from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from .fatsecret.fatsecret import Fatsecret

db = SQLAlchemy()
migrate = Migrate()
fs = Fatsecret()


def create_app(test_config=None):
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    if test_config is not None:
        app.config.update(test_config)

    # Initialize Database Plugin
    db.init_app(app)
    migrate.init_app(app, db)
    fs.setToken(app.config['FATSECRET_CLIENT_ID'], app.config['FATSECRET_CLIENT_SECRET'])

    with app.app_context():
        # Import routes
        from .routes import main  
        from .routes import dishes

        db.create_all()  # Create database tables for our data models

        return app