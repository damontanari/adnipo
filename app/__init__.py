import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import base64
from io import BytesIO
from werkzeug.utils import secure_filename
from datetime import datetime

# Carregar as variáveis do .env
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Configurações do aplicativo usando variáveis de ambiente
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Usando variável de ambiente
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV')  # Usando variável de ambiente

    # Configuração para upload de arquivos
    UPLOAD_FOLDER = 'app/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Função para verificar se a extensão do arquivo é permitida
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # Filtro customizado para codificar imagens em base64
    @app.template_filter('b64encode')
    def b64encode_filter(img_io):
        return base64.b64encode(img_io.getvalue()).decode('utf-8')
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # Inicializa o banco de dados
    db.init_app(app)

    # Importa e configura rotas
    from app.routes import configure_routes
    configure_routes(app)

    return app
