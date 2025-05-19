from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

# Tabela de associação Evento ↔ Publico
evento_publico_associacao = db.Table('evento_publico_associacao',
    db.Column('evento_id', db.Integer, db.ForeignKey('evento.id'), primary_key=True),
    db.Column('publico_id', db.Integer, db.ForeignKey('publico.id'), primary_key=True)
)

# Tabela de associação Usuario ↔ Publico
usuario_publico_associacao = db.Table('usuario_publico_associacao',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('publico_id', db.Integer, db.ForeignKey('publico.id'), primary_key=True)
)

membro_publico = db.Table('membro_publico',
    db.Column('membro_id', db.Integer, db.ForeignKey('membro.id'), primary_key=True),
    db.Column('publico_id', db.Integer, db.ForeignKey('publico.id'), primary_key=True)
)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relacionamento opcional com um membro
    membro_id = db.Column(db.Integer, db.ForeignKey('membro.id'), nullable=True)
    membro = relationship(
        'Membro',
        backref='usuario_vinculado',
        uselist=False,
        foreign_keys='Usuario.membro_id'
    )

    publicos = db.relationship(
        'Publico',
        secondary=usuario_publico_associacao,
        back_populates='usuarios'
    )

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
    usuario = relationship('Usuario', backref='membros_cadastrados', foreign_keys='Membro.usuario_id')
    publicos = db.relationship('Publico', secondary=membro_publico, backref='membros')

    # Nova coluna para a foto
    foto = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Membro {self.nome}>"


class Reuniao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    local = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    def __repr__(self):
        return f"<Reuniao {self.titulo}>"


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    local = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    publicos = db.relationship('Publico', secondary=evento_publico_associacao, back_populates='eventos')

    def __repr__(self):
        return f"<Evento {self.titulo}>"

class Publico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    eventos = db.relationship('Evento', secondary=evento_publico_associacao, back_populates='publicos')
    usuarios = db.relationship('Usuario', secondary=usuario_publico_associacao, back_populates='publicos')
    
    def __repr__(self):
        return f"<Publico {self.nome}>"
    

class Recado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    criador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    publico_id = db.Column(db.Integer, db.ForeignKey('publico.id'), nullable=True)  # opcional: recado pode ser para um público ou para todos

    criador = db.relationship('Usuario', backref='recados')
    publico = db.relationship('Publico', backref='recados')

    def __repr__(self):
        return f"<Recado {self.titulo}>"
    
class RecadoLeitura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    recado_id = db.Column(db.Integer, db.ForeignKey('recado.id'))
    data_leitura = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='recados_lidos')
    recado = db.relationship('Recado', backref='leituras')



