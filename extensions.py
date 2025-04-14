from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Inicializace rozšíření
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Pro přístup k této stránce se musíte přihlásit.'
login_manager.login_message_category = 'info'
