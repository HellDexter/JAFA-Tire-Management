from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
from extensions import db, login_manager

# Konfigurace aplikace
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tajny_klic_pro_vyvoj')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jafa_tire_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit pro uploady

# Zajistíme, že složka pro uploady existuje
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Konfigurace logování
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializace rozšíření s aplikací
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Pro přístup k této stránce se musíte přihlásit.'
login_manager.login_message_category = 'info'

# Kontext procesory - přidáváme proměnné dostupné ve všech šablonách
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

# Import a registrace routes až po definování app
with app.app_context():
    import models
    import routes
    routes.register_routes(app)
    
    # Registrace API routů
    from api import register_api
    register_api(app)

# Vytvoření výchozího admin uživatele
def create_default_admin():
    from models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@jafa.cz',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info('Vytvořen výchozí administrátorský účet')

# Spuštění aplikace
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Vytvoření databáze, pokud neexistuje
        create_default_admin()  # Vytvoření výchozího admin účtu, pokud neexistuje
    app.run(debug=True)
