import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import base64
from io import BytesIO
from datetime import datetime

# Carregar as variáveis do .env
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Configurações...
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV')
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # Filtro customizado para base64
    @app.template_filter('b64encode')
    def b64encode_filter(img_io):
        return base64.b64encode(img_io.getvalue()).decode('utf-8')

    # Context processor para data/hora atual
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # Context processor para usuário logado
    @app.context_processor
    def inject_usuario_logado():
        from flask import session
        from app.models import Usuario  # ou o caminho certo pro seu model
        usuario = None
        if 'usuario_id' in session:
            usuario = Usuario.query.get(session['usuario_id'])
        return {'usuario_logado': usuario}

    # Inicializa o banco de dados
    db.init_app(app)

    # Importa e configura rotas
    from app.routes import configure_routes
    configure_routes(app)

    return app

