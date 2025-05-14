# app/routes.py
from flask import render_template, request, redirect, url_for, flash, session, abort, jsonify
from app import db
from app.models import Membro, Usuario
from datetime import datetime
from functools import wraps
import qrcode
from io import BytesIO
import os
from werkzeug.utils import secure_filename
from app.utils import allowed_file


# Função para recuperar o usuário logado
def get_usuario_logado():
    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = Usuario.query.get(usuario_id)
        return usuario
    return None

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
        if not usuario.is_admin:
            flash('Acesso restrito a administradores.')
            return redirect(url_for('listar_membros'))
        return f(*args, **kwargs)
    return decorated_function

def configure_routes(app):

    @app.route('/setup_db')
    def setup_db():
        db.create_all()

        if not Usuario.query.filter_by(email="daniel@adnipo.com").first():
            admin_daniel = Usuario(nome="Daniel", email="daniel@adnipo.com", is_admin=True)
            admin_daniel.set_senha("senha123")
            db.session.add(admin_daniel)

        if not Usuario.query.filter_by(email="richard@adnipo.com").first():
            admin_richard = Usuario(nome="Richard", email="richard@adnipo.com", is_admin=True)
            admin_richard.set_senha("senha123")
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
                return redirect(url_for('admin_home'))
            else:
                flash('Credenciais inválidas!')

        return render_template('auth/login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logout realizado!')
        return redirect(url_for('login'))

    @app.route('/')
    def site_home():
        return render_template('site/home.html', now=datetime.now())

    @app.route('/admin')
    def admin_home():
        usuario_logado = get_usuario_logado()
        if not usuario_logado:
            flash("Você precisa estar logado para acessar o painel.")
            return redirect(url_for('login'))
        return render_template('home.html', usuario_logado=usuario_logado)

    @app.route('/membros')
    @login_requerido
    def listar_membros():
        # Pega parâmetros da URL
        nome = request.args.get('nome')
        cidade = request.args.get('cidade')
        sexo = request.args.get('sexo')
        oficio = request.args.get('oficio')
        status_membro = request.args.get('status_membro')

        # Monta query base
        query = Membro.query

        # Aplica filtros se existirem
        if nome:
            query = query.filter(Membro.nome.ilike(f'%{nome}%'))
        if cidade:
            query = query.filter(Membro.cidade.ilike(f'%{cidade}%'))
        if sexo:
            query = query.filter(Membro.sexo == sexo)
        if oficio:
            query = query.filter(Membro.oficio.ilike(f'%{oficio}%'))
        if status_membro:
            query = query.filter(Membro.membro_tipo == status_membro)

        # Total de membros filtrados
        total_membros = query.count()

        # Resultado da busca
        membros = query.all()

        # Dashboards de estatísticas
        membros_por_oficio = db.session.query(Membro.oficio, db.func.count(Membro.id)).group_by(Membro.oficio).all()
        membros_por_cidade = db.session.query(Membro.cidade, db.func.count(Membro.id)).group_by(Membro.cidade).all()
        membros_por_status = db.session.query(Membro.membro_tipo, db.func.count(Membro.id)).group_by(Membro.membro_tipo).all()

        # Ofícios disponíveis para o select de filtro
        oficios_disponiveis = [o[0] for o in db.session.query(Membro.oficio).distinct().all()]

        return render_template('membros/lista.html',
                            membros=membros,
                            total_membros=total_membros,
                            membros_por_oficio=membros_por_oficio,
                            membros_por_cidade=membros_por_cidade,
                            membros_por_status=membros_por_status,
                            oficios_disponiveis=oficios_disponiveis,
                            usuario_logado=get_usuario_logado())



    @app.route('/membros/novo', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def novo_membro():
        if request.method == 'POST':
            # dados do formulário
            nome = request.form.get('nome')
            endereco = request.form.get('endereco')
            numero = request.form.get('numero')
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

            foto = request.files.get('foto')
            foto_filename = None
            if foto and allowed_file(foto.filename):
                foto_filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))

            def parse_date(date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

            data_nascimento = parse_date(request.form.get('data_nascimento'))
            data_casamento  = parse_date(request.form.get('data_casamento'))
            data_batismo    = parse_date(request.form.get('data_batismo'))

            novo_membro = Membro(
                nome=nome,
                endereco=endereco,
                numero=numero,
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
                data_batismo=data_batismo,
                escolaridade=escolaridade,
                profissao=profissao,
                nome_pai=nome_pai,
                nome_mae=nome_mae,
                membro_tipo=membro_tipo,
                oficio=oficio,
                pastor_batismo=pastor_batismo,
                igreja_batismo=igreja_batismo,
                foto=foto_filename,
                data_cadastro=datetime.utcnow(),
                usuario_id=session.get('usuario_id')  # aqui pega o usuário logado
            )

            db.session.add(novo_membro)
            db.session.commit()

            flash('Membro cadastrado com sucesso!')
            return redirect(url_for('listar_membros'))

        return render_template('membros/novo.html')

    @app.route('/membros/editar/<int:membro_id>', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def editar_membro(membro_id):
        membro = Membro.query.get_or_404(membro_id)

        if request.method == 'POST':
            membro.nome = request.form.get('nome')
            membro.endereco = request.form.get('endereco')
            membro.numero = request.form.get('numero')
            membro.cidade = request.form.get('cidade')
            membro.uf = request.form.get('uf')
            membro.pais = request.form.get('pais')
            membro.cep = request.form.get('cep')
            membro.telefone = request.form.get('telefone')
            membro.email = request.form.get('email')
            membro.naturalidade = request.form.get('naturalidade')
            membro.sexo = request.form.get('sexo')
            membro.estado_civil = request.form.get('estado_civil')
            membro.nome_conjuge = request.form.get('nome_conjuge')
            membro.escolaridade = request.form.get('escolaridade')
            membro.profissao = request.form.get('profissao')
            membro.nome_pai = request.form.get('nome_pai')
            membro.nome_mae = request.form.get('nome_mae')
            membro.membro_tipo = request.form.get('membro_tipo')
            membro.oficio = request.form.get('oficio')
            membro.pastor_batismo = request.form.get('pastor_batismo')
            membro.igreja_batismo = request.form.get('igreja_batismo')

            foto = request.files.get('foto')
            if foto and allowed_file(foto.filename):
                foto_filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))
                membro.foto = foto_filename

            membro.data_nascimento = request.form['data_nascimento'] or None
            membro.data_casamento = request.form['data_casamento'] or None
            membro.data_batismo = request.form['data_batismo'] or None

            db.session.commit()
            flash('Membro atualizado com sucesso!')
            return redirect(url_for('listar_membros'))

        return render_template('membros/editar.html', membro=membro)

    @app.route('/membros/excluir/<int:membro_id>', methods=['POST'])
    @login_requerido
    @admin_requerido
    def excluir_membro(membro_id):
        membro = Membro.query.get_or_404(membro_id)
        db.session.delete(membro)
        db.session.commit()
        flash('Membro excluído com sucesso!')
        return redirect(url_for('listar_membros'))

    @app.route('/membro/<int:membro_id>/carteirinha')
    @login_requerido
    def carteirinha_membro(membro_id):
        membro = Membro.query.get_or_404(membro_id)
        data_para_qr = f"https://7e75-189-113-26-36.ngrok-free.app/membro/{membro.id}"

        qr = qrcode.make(data_para_qr)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        return render_template('membros/carteirinha.html', membro=membro, qr_code=img_io)

    # 👉 API JSON de membros ordenada por nome
    @app.route('/api/membros', methods=['GET'])
    def api_membros():
        membros = Membro.query.order_by(Membro.nome).all()
        membros_json = [m.to_dict() for m in membros]
        return jsonify(membros_json)
    
    @app.route('/exportar_membros')
    def exportar_membros():
        from io import BytesIO
        import pandas as pd
        from flask import send_file

        membros = Membro.query.all()

        data = [{
            'ID': m.id,
            'Nome': m.nome,
            'Endereço': m.endereco,
            'Cidade': m.cidade,
            'UF': m.uf,
            'País': m.pais,
            'CEP': m.cep,
            'Telefone': m.telefone,
            'Email': m.email,
            'Data de Nascimento': m.data_nascimento.strftime('%d/%m/%Y') if m.data_nascimento else '',
            'Naturalidade': m.naturalidade,
            'Sexo': m.sexo,
            'Estado Civil': m.estado_civil,
            'Nome do Cônjuge': m.nome_conjuge,
            'Data de Casamento': m.data_casamento.strftime('%d/%m/%Y') if m.data_casamento else '',
            'Data de Batismo': m.data_batismo.strftime('%d/%m/%Y') if m.data_batismo else '',
            'Escolaridade': m.escolaridade,
            'Profissão': m.profissao,
            'Nome do Pai': m.nome_pai,
            'Nome da Mãe': m.nome_mae,
            'Tipo de Membro': m.membro_tipo,
            'Ofício': m.oficio,
            'Pastor do Batismo': m.pastor_batismo,
            'Igreja do Batismo': m.igreja_batismo,
            'Foto': m.foto,
            'Data de Cadastro': m.data_cadastro.strftime('%d/%m/%Y %H:%M')
        } for m in membros]

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Membros')

        output.seek(0)
        return send_file(output, download_name='membros_completo.xlsx', as_attachment=True)


