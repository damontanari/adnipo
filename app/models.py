from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Membro(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Dados Pessoais
    nome = db.Column(db.String(150), nullable=False)
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    cep = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    data_nascimento = db.Column(db.Date)
    naturalidade = db.Column(db.String(100))
    sexo = db.Column(db.String(20))

    # Dados Complementares
    estado_civil = db.Column(db.String(30))
    nome_conjuge = db.Column(db.String(150))
    data_casamento = db.Column(db.Date)
    escolaridade = db.Column(db.String(100))
    profissao = db.Column(db.String(100))
    nome_pai = db.Column(db.String(150))
    nome_mae = db.Column(db.String(150))

    # Dados Eclesiásticos
    membro_tipo = db.Column(db.String(30))  # Membro, Visitante, Não Membro
    oficio = db.Column(db.String(50))       # Pastoreio, Presbiterio, Diaconato, Líderes, Musico, Cooperador...

    # Batismo
    data_batismo = db.Column(db.Date)
    pastor_batismo = db.Column(db.String(150))
    igreja_batismo = db.Column(db.String(150))

    # Registro
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com o usuário que cadastrou
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = relationship('Usuario', backref='membros_cadastrados')

    # Nova coluna para a foto
    foto = db.Column(db.String(120), nullable=True)  # Caminho da foto

    def __repr__(self):
        return f"<Membro {self.nome}>"
    

