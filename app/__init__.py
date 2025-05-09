import os
from dotenv import load_dotenv

# Carregar as variáveis do .env
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Configurações do aplicativo usando variáveis de ambiente
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Usando variável de ambiente
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Usando variável de ambiente
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV')  # Usando variável de ambiente

    # Inicializa o banco de dados
    db.init_app(app)

    # Importa e configura rotas
    from app.routes import configure_routes
    configure_routes(app)

    return app
