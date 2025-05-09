# app/routes.py

from flask import render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Membro, Usuario
from datetime import datetime
from functools import wraps

# Decorador de login
def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar essa página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para garantir que o usuário é um administrador
def admin_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar essa página.')
            return redirect(url_for('login'))
        
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario.is_admin:  # Verifica se o usuário tem a flag de admin
            flash('Acesso restrito a administradores.')
            return redirect(url_for('listar_membros'))
        
        return f(*args, **kwargs)
    return decorated_function

# Função para registrar as rotas
def configure_routes(app):

    @app.route('/setup_db')
    def setup_db():
        # Criando o banco de dados se não existir
        db.create_all()

        # Verificando se os administradores já existem
        if not Usuario.query.filter_by(email="daniel@adnipo.com").first():
            admin_daniel = Usuario(nome="Daniel", email="daniel@adnipo.com", is_admin=True)
            admin_daniel.set_senha("senha123")  # Definindo senha para o admin Daniel
            db.session.add(admin_daniel)

        if not Usuario.query.filter_by(email="richard@adnipo.com").first():
            admin_richard = Usuario(nome="Richard", email="richard@adnipo.com", is_admin=True)
            admin_richard.set_senha("senha123")  # Definindo senha para o admin Richard
            db.session.add(admin_richard)

        db.session.commit()

        return "Banco de dados configurado e administradores criados!"

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            senha = request.form.get('senha')
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.checar_senha(senha):
                session['usuario_id'] = usuario.id
                session['usuario_nome'] = usuario.nome
                flash('Login realizado com sucesso!')
                return redirect(url_for('listar_membros'))
            else:
                flash('Credenciais inválidas!')

        return render_template('auth/login.html')

    # Logout
    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logout realizado!')
        return redirect(url_for('login'))

    # Home (redireciona)
    @app.route('/')
    @login_requerido
    def home():
        return redirect(url_for('listar_membros'))

    # Listar membros
    @app.route('/membros')
    @login_requerido
    def listar_membros():
        nome = request.args.get('nome')
        cidade = request.args.get('cidade')
        sexo = request.args.get('sexo')
        oficio = request.args.get('oficio')
        query = Membro.query

        # Filtro por nome
        if nome:
            query = query.filter(Membro.nome.ilike(f'%{nome}%'))
        # Filtro por cidade
        if cidade:
            query = query.filter(Membro.cidade.ilike(f'%{cidade}%'))
        # Filtro por sexo
        if sexo:
            query = query.filter(Membro.sexo == sexo)
        # Filtro por ofício
        if oficio:
            query = query.filter(Membro.oficio.ilike(f'%{oficio}%'))
        
        membros = query.all()

        # Estatísticas de membros por ofício e cidade
        membros_por_oficio = db.session.query(Membro.oficio, db.func.count(Membro.id).label('total')).group_by(Membro.oficio).all()
        membros_por_cidade = db.session.query(Membro.cidade, db.func.count(Membro.id).label('total')).group_by(Membro.cidade).all()

        return render_template('membros/lista.html', membros=membros, 
                            membros_por_oficio=membros_por_oficio, membros_por_cidade=membros_por_cidade)

    # Novo membro
    @app.route('/membros/novo', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def novo_membro():
        if request.method == 'POST':
            # Pegando dados do form
            nome = request.form.get('nome')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            uf = request.form.get('uf')
            pais = request.form.get('pais')
            cep = request.form.get('cep')
            telefone = request.form.get('telefone')
            email = request.form.get('email')
            naturalidade = request.form.get('naturalidade')
            sexo = request.form.get('sexo')
            estado_civil = request.form.get('estado_civil')
            nome_conjuge = request.form.get('nome_conjuge')
            escolaridade = request.form.get('escolaridade')
            profissao = request.form.get('profissao')
            nome_pai = request.form.get('nome_pai')
            nome_mae = request.form.get('nome_mae')
            membro_tipo = request.form.get('membro_tipo')
            oficio = request.form.get('oficio')
            pastor_batismo = request.form.get('pastor_batismo')
            igreja_batismo = request.form.get('igreja_batismo')

            # Convertendo datas (YYYY-MM-DD → datetime.date)
            def parse_date(date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

            data_nascimento = parse_date(request.form.get('data_nascimento'))
            data_casamento  = parse_date(request.form.get('data_casamento'))
            data_batismo    = parse_date(request.form.get('data_batismo'))

            novo_membro = Membro(
                nome=nome,
                endereco=endereco,
                cidade=cidade,
                uf=uf,
                pais=pais,
                cep=cep,
                telefone=telefone,
                email=email,
                data_nascimento=data_nascimento,
                naturalidade=naturalidade,
                sexo=sexo,
                estado_civil=estado_civil,
                nome_conjuge=nome_conjuge,
                data_casamento=data_casamento,
                escolaridade=escolaridade,
                profissao=profissao,
                nome_pai=nome_pai,
                nome_mae=nome_mae,
                membro_tipo=membro_tipo,
                oficio=oficio,
                data_batismo=data_batismo,
                pastor_batismo=pastor_batismo,
                igreja_batismo=igreja_batismo,
                data_cadastro=datetime.utcnow()
            )

            db.session.add(novo_membro)
            db.session.commit()

            flash('Membro cadastrado com sucesso!')
            return redirect(url_for('listar_membros'))

        return render_template('membros/novo.html')

    # Editar membro
    @app.route('/membros/editar/<int:membro_id>', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def editar_membro(membro_id):
        membro = Membro.query.get_or_404(membro_id)

        if request.method == 'POST':
            # Atualizando os dados com base no formulário
            membro.nome = request.form.get('nome')
            membro.endereco = request.form.get('endereco')
            membro.cidade = request.form.get('cidade')
            membro.uf = request.form.get('uf')
            membro.pais = request.form.get('pais')
            membro.cep = request.form.get('cep')
            membro.telefone = request.form.get('telefone')
            membro.email = request.form.get('email')
            membro.data_nascimento = request.form.get('data_nascimento')
            membro.naturalidade = request.form.get('naturalidade')
            membro.sexo = request.form.get('sexo')
            membro.estado_civil = request.form.get('estado_civil')
            membro.nome_conjuge = request.form.get('nome_conjuge')
            membro.data_casamento = request.form.get('data_casamento')
            membro.escolaridade = request.form.get('escolaridade')
            membro.profissao = request.form.get('profissao')
            membro.nome_pai = request.form.get('nome_pai')
            membro.nome_mae = request.form.get('nome_mae')
            membro.membro_tipo = request.form.get('membro_tipo')
            membro.oficio = request.form.get('oficio')
            membro.data_batismo = request.form.get('data_batismo')
            membro.pastor_batismo = request.form.get('pastor_batismo')
            membro.igreja_batismo = request.form.get('igreja_batismo')

            db.session.commit()
            flash('Dados atualizados com sucesso!')
            return redirect(url_for('listar_membros'))

        return render_template('membros/editar.html', membro=membro)


    # Excluir membro
    @app.route('/membros/excluir/<int:membro_id>')
    @login_requerido
    def excluir_membro(membro_id):
        membro = Membro.query.get_or_404(membro_id)
        db.session.delete(membro)
        db.session.commit()
        flash('Membro excluído com sucesso!')
        return redirect(url_for('listar_membros'))
    
    @app.context_processor
    def inject_user():
        from app.models import Usuario
        usuario_logado = None
        if 'usuario_id' in session:
            usuario_logado = Usuario.query.get(session['usuario_id'])
        return dict(usuario_logado=usuario_logado)

