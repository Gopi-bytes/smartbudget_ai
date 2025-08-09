from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# Extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(get_remote_address)
csrf = CSRFProtect()

# Login configuration
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

def create_app():
    # Create Flask app with instance-relative configuration
    app = Flask(__name__, instance_relative_config=True)
    
    # Load other configuration values from Config object
    app.config.from_object(Config)

    # Ensure that the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Default to a SQLite database in the instance folder if none specified
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        db_path = os.path.join(app.instance_path, 'smartbudget.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    # Create DB tables on first run
    with app.app_context():
        db.create_all()

    # Handle CSRF errors gracefully
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template("csrf_error.html", reason=e.description), 400

    # Logging Setup
    if not os.path.exists('logs'):
        os.mkdir('logs')

    log_path = os.path.join('logs', 'audit.log')
    file_handler = RotatingFileHandler(log_path, maxBytes=10240, backupCount=3)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', "%Y-%m-%d %H:%M:%S"))
    file_handler.setLevel(logging.INFO)

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("SmartBudget AI app started.")

    return app
