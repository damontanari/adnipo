# app/routes.py
from flask import render_template, request, redirect, url_for, flash, session, abort, jsonify
from app import db
from app.models import Membro, Usuario, Evento, Publico, Recado, Presenca
from datetime import datetime, timedelta
from functools import wraps
import qrcode
from io import BytesIO
import base64
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from app.utils import allowed_file
import requests
import random

# Função para recuperar o usuário logado
def get_usuario_logado():
    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = Usuario.query.get(usuario_id)
        return usuario
    return None

# Verificando se existe recados não lidos
def get_recados_nao_lidos(usuario):
    todos_recados = Recado.query.order_by(Recado.data_criacao.desc()).all()
    return [r for r in todos_recados if usuario not in r.lido_por]


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


# Configuração das rotas
def configure_routes(app):

    # Carregar os recados que não foram lidos
    @app.context_processor
    def carregar_recados_nao_lidos():
        usuario_logado = get_usuario_logado()
        if not usuario_logado:
            return dict(novos_recados=0, recados=[])
        
        if usuario_logado.is_admin:
            # Para admins, pegar todos recados que não foram lidos
            recados_pendentes = Recado.query.filter(~Recado.lido_por.any(id=usuario_logado.id)) \
                .order_by(Recado.data_criacao.desc()).limit(5).all()
        else:
            oficio_usuario = usuario_logado.membro.oficio if usuario_logado.membro else None

            recados_pendentes = Recado.query.join(Recado.publicos).filter(
                ((Publico.nome == 'Todos') | (Publico.nome == oficio_usuario)) &
                (~Recado.lido_por.any(id=usuario_logado.id))
            ).order_by(Recado.data_criacao.desc()).limit(5).all()

        return dict(novos_recados=len(recados_pendentes), recados=recados_pendentes)



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

        try:
            versiculos = [
                "João 3:16", "Salmos 23:1", "Provérbios 3:5", "Filipenses 4:13",
                "Romanos 8:28", "Isaías 41:10", "Mateus 6:33", "Salmos 37:5",
                "Tiago 1:5", "Jeremias 29:11", "Salmos 46:1", "Mateus 11:28",
                "Romanos 12:2", "Salmos 91:1", "Isaías 40:31", "2 Coríntios 5:17"
            ]

            verso_aleatorio = random.choice(versiculos)
            response = requests.get(f'https://bible-api.com/{verso_aleatorio}?translation=almeida')
            versiculo = response.json()

        except Exception as e:
            versiculo = {
                "reference": "Erro ao buscar versículo",
                "text": f"{e}",
                "translation_name": ""
            }
        
        if not usuario_logado:
            flash("Você precisa estar logado para acessar o painel.")
            return redirect(url_for('login'))

        # Eventos ativos futuros (limitados a 3)
        eventos = Evento.query\
            .filter(Evento.data_hora >= datetime.now(), Evento.ativo == True)\
            .order_by(Evento.data_hora.asc())\
            .limit(3)\
            .all()

        # Recados futuros (limitados a 3)
        recados = Recado.query\
            .filter(Recado.data_criacao >= datetime.now())\
            .order_by(Recado.data_criacao.asc())\
            .limit(3)\
            .all()

        # Evento ativo do dia (considerando somente ativos)
        evento_ativo = Evento.query.filter(
            Evento.data_hora >= datetime.now(),
            Evento.ativo == True
        ).order_by(Evento.data_hora.asc()).first()

        publicos = Publico.query.all()
        membro_id = usuario_logado.membro.id if usuario_logado.membro else None

        return render_template(
            'home.html',
            usuario_logado=usuario_logado,
            timedelta=timedelta,
            eventos=eventos,
            recados=recados,
            publicos=publicos,
            evento_ativo=evento_ativo,
            membro_id=membro_id,
            versiculo=versiculo
        )

        

    @app.route('/perfil')
    @login_requerido
    def perfil():
        usuario = Usuario.query.get(session['usuario_id'])
        return render_template('perfil.html', usuario=usuario)
    

    @app.route('/alterar_senha', methods=['POST'])
    @login_requerido
    def alterar_senha():
        usuario = Usuario.query.get(session['usuario_id'])

        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if not check_password_hash(usuario.senha_hash, senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return redirect(url_for('perfil'))

        if nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem.', 'danger')
            return redirect(url_for('perfil'))

        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()

        flash('Senha atualizada com sucesso!', 'success')
        return redirect(url_for('perfil'))


    @app.route('/membros')
    @login_requerido
    @admin_requerido
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

            # Cria o novo membro
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
                usuario_id=session.get('usuario_id')
            )

            db.session.add(novo_membro)
            db.session.commit()  # precisa antes para pegar novo_membro.id

            # Cria usuário vinculado ao membro
            novo_usuario = Usuario(
                nome=novo_membro.nome,
                email=novo_membro.email,
                is_admin=False,
                membro_id=novo_membro.id
            )
            novo_usuario.set_senha('adnipo')  # senha padrão

            db.session.add(novo_usuario)
            db.session.commit()

            flash(f'Membro {novo_membro.nome} cadastrado e usuário criado com senha padrão.', 'success')
            return redirect(url_for('listar_membros'))

        return render_template('membros/novo.html')
    

    @app.route('/membros/cadastrar', methods=['GET', 'POST'])
    def membro_cadastrar():
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

            # Cria o novo membro
            membro_cadastrar = Membro(
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
                usuario_id=session.get('usuario_id')
            )

            db.session.add(membro_cadastrar)
            db.session.commit()  # precisa antes para pegar novo_membro.id

            # Cria usuário vinculado ao membro
            novo_usuario = Usuario(
                nome=membro_cadastrar.nome,
                email=membro_cadastrar.email,
                is_admin=False,
                membro_id=membro_cadastrar.id
            )
            novo_usuario.set_senha('adnipo')  # senha padrão

            db.session.add(novo_usuario)
            db.session.commit()

            flash(f'Membro {membro_cadastrar.nome} cadastrado e usuário criado com senha padrão.', 'success')
            return redirect(url_for('login'))

        return render_template('membros/cadastro.html')


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

            # Processar datas com conversão para datetime.date
            def parse_date(field_name):
                data_str = request.form.get(field_name)
                if data_str:
                    try:
                        return datetime.strptime(data_str, '%Y-%m-%d').date()
                    except ValueError:
                        return None
                return None

            membro.data_nascimento = parse_date('data_nascimento')
            membro.data_casamento = parse_date('data_casamento')
            membro.data_batismo = parse_date('data_batismo')

            # Foto upload
            foto = request.files.get('foto')
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                foto.save(foto_path)
                membro.foto = filename

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
        # Usar a rota de checkin para o QR code:
        data_para_qr = url_for('checkin_scan', membro_id=membro.id, _external=True)

        qr = qrcode.make(data_para_qr)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        qr_base64 = base64.b64encode(img_io.getvalue()).decode()
        return render_template('membros/carteirinha.html', membro=membro, qr_code=qr_base64)



    # 👉 API JSON de membros ordenada por nome
    @app.route('/api/membros', methods=['GET'])
    def api_membros():
        membros = Membro.query.order_by(Membro.nome).all()
        membros_json = [m.to_dict() for m in membros]
        return jsonify(membros_json)
    

    @app.route('/exportar_membros')
    @login_requerido
    @admin_requerido
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


    

    ## Eventos
    @app.route('/eventos')
    @login_requerido
    def listar_eventos():
        usuario_logado = get_usuario_logado()

        if usuario_logado:
            print(usuario_logado, usuario_logado.is_admin)
        else:
            print("Nenhum usuário logado.")

        if usuario_logado.is_admin:
            # Admin vê todos os eventos
            eventos_para_mim = Evento.query.order_by(Evento.data_hora.asc()).all()
            aviso = None
        else:
            if usuario_logado.membro and usuario_logado.membro.oficio:
                oficio_usuario = usuario_logado.membro.oficio
                eventos_para_mim = Evento.query.join(Evento.publicos).filter(
                    (Publico.nome == 'Todos') | (Publico.nome == oficio_usuario)
                ).order_by(Evento.data_hora.asc()).all()
                aviso = None
            else:
                # Sem membro ou sem oficio — vê só os eventos públicos
                eventos_para_mim = Evento.query.join(Evento.publicos).filter(
                    Publico.nome == 'Todos'
                ).order_by(Evento.data_hora.asc()).all()
                aviso = "Seu usuário não está vinculado a um membro ou ofício. Você verá apenas eventos públicos."

        return render_template('eventos/lista.html', eventos=eventos_para_mim, usuario_logado=usuario_logado, aviso=aviso)
    

    @app.route('/eventos/novo', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def novo_evento():
        if request.method == 'POST':
            titulo = request.form['titulo']
            data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
            local = request.form['local']
            descricao = request.form['descricao']
            publicos_ids = request.form.getlist('publicos')

            novo_evento = Evento(
                titulo=titulo,
                data_hora=data_hora,
                local=local,
                descricao=descricao,
                criador_id=session.get('usuario_id')
            )

            # agora associa os públicos selecionados
            if 'Todos' in publicos_ids:
                todos_publicos = Publico.query.all()
                novo_evento.publicos = todos_publicos
            else:
                publicos_selecionados = Publico.query.filter(Publico.id.in_(publicos_ids)).all()
                novo_evento.publicos = publicos_selecionados

            db.session.add(novo_evento)
            db.session.commit()

            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('listar_eventos'))

        publicos = Publico.query.all()
        return render_template('eventos/novo.html', publicos=publicos)


    @app.route('/eventos/editar/<int:evento_id>', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def editar_evento(evento_id):
        usuario_logado = get_usuario_logado()
        evento = Evento.query.get_or_404(evento_id)

        if request.method == 'POST':
            evento.titulo = request.form['titulo']
            evento.data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
            evento.local = request.form['local']
            evento.descricao = request.form['descricao']

            # Atualiza os públicos
            publicos_ids = request.form.getlist('publicos')
            evento.publicos.clear()
            for publico_id in publicos_ids:
                publico = Publico.query.get(publico_id)
                evento.publicos.append(publico)

            db.session.commit()
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('listar_eventos'))
        
        publicos = Publico.query.all()
        return render_template('eventos/editar.html', evento=evento, usuario_logado=usuario_logado, publicos=publicos)

    
    @app.route('/eventos/excluir/<int:evento_id>', methods=['POST'])
    @login_requerido
    @admin_requerido
    def excluir_evento(evento_id):
        evento = Evento.query.get_or_404(evento_id)
        db.session.delete(evento)
        db.session.commit()
        flash('Evento excluído com sucesso!', 'success')
        return redirect(url_for('listar_eventos'))
    

    @app.route('/api/eventos')
    def api_eventos():
        usuario_logado = get_usuario_logado()

        if usuario_logado.is_admin:
            eventos = Evento.query.order_by(Evento.data_hora.asc()).all()
        elif usuario_logado.membro:
            publicos_usuario = [p.id for p in usuario_logado.membro.publicos]
            eventos = Evento.query\
                .join(Evento.publicos)\
                .filter(Publico.id.in_(publicos_usuario))\
                .order_by(Evento.data_hora.asc())\
                .all()
        else:
            eventos = []

        eventos_json = [{
            'title': e.titulo,
            'start': e.data_hora.isoformat(),
            'description': e.descricao,
            'location': e.local
        } for e in eventos]

        return jsonify(eventos_json)
    

    ## Recados

    @app.route('/recados')
    @login_requerido
    def listar_recados():
        usuario_logado = get_usuario_logado()

        if usuario_logado.is_admin:
            # pega os 3 últimos recados cadastrados (mais recentes)
            recados_para_mim = Recado.query.order_by(Recado.data_criacao.desc()).limit(3).all()
        else:
            oficio_usuario = usuario_logado.membro.oficio if usuario_logado.membro else None

            recados_para_mim = Recado.query.join(Recado.publicos).filter(
                (Publico.nome == 'Todos') |
                (Publico.nome == oficio_usuario)
            ).order_by(Recado.data_criacao.desc()).limit(3).all()

        return render_template('recados/lista.html', recados=recados_para_mim, usuario_logado=usuario_logado)


    @app.route('/recados/novo', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def novo_recado():
        if request.method == 'POST':
            titulo = request.form['titulo']
            descricao = request.form['descricao']
            publicos_ids = request.form.getlist('publicos')

            novo_recado = Recado(
                titulo=titulo,
                descricao=descricao,
                criador_id=session.get('usuario_id')
            )

            # agora associa os públicos selecionados
            if 'Todos' in publicos_ids:
                todos_publicos = Publico.query.all()
                novo_recado.publicos = todos_publicos
            else:
                publicos_selecionados = Publico.query.filter(Publico.id.in_(publicos_ids)).all()
                novo_recado.publicos = publicos_selecionados

            db.session.add(novo_recado)
            db.session.commit()

            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('listar_recados'))

        publicos = Publico.query.all()
        return render_template('recados/novo.html', publicos=publicos)


    @app.route('/recados/editar/<int:recado_id>', methods=['GET', 'POST'])
    @login_requerido
    @admin_requerido
    def editar_recado(recado_id):
        usuario_logado = get_usuario_logado()
        recado = Recado.query.get_or_404(recado_id)

        if request.method == 'POST':
            recado.titulo = request.form['titulo']
            recado.descricao = request.form['descricao']

            db.session.commit()
            flash('Recado atualizado com sucesso!', 'success')
            return redirect(url_for('listar_recados'))

        return render_template('recados/editar.html', recado=recado, usuario_logado=usuario_logado)


    @app.route('/recados/excluir/<int:recado_id>', methods=['POST'])
    @login_requerido
    @admin_requerido
    def excluir_recado(recado_id):
        recado = Recado.query.get_or_404(recado_id)
        db.session.delete(recado)
        db.session.commit()
        flash('Recado excluído com sucesso!', 'success')
        return redirect(url_for('listar_recados'))


    @app.route('/recados/ver/<int:recado_id>')
    @login_requerido
    def ver_recado(recado_id):
        recado = Recado.query.get_or_404(recado_id)
        usuario = get_usuario_logado()

        if usuario not in recado.lido_por:
            recado.lido_por.append(usuario)
            db.session.commit()

        return render_template('recados/ver.html', recado=recado, usuario_logado=usuario)
    
    @app.route('/recados/limpar', methods=['POST'])
    @login_requerido
    def limpar_recados():
        usuario = get_usuario_logado()

        # pega todos os recados não lidos pra esse usuário
        recados_nao_lidos = Recado.query.filter(~Recado.lido_por.any(id=usuario.id)).all()

        for recado in recados_nao_lidos:
            recado.lido_por.append(usuario)

        db.session.commit()
        flash('Notificações limpas!', 'success')
        return redirect(request.referrer or url_for('listar_recados'))



    @app.route('/api/recados')
    @login_requerido
    def api_recados():
        recados = Recado.query.all()

        list_recados = []
        for r in recados:
            list_recados.append({
                'id': r.id,
                'title': f"Recado - {r.titulo}",
                'description': r.descricao,
                'allDay': False
            })

        return jsonify(list_recados)
    

    # Oferta/Dizimos
    @app.route('/oferta')
    @login_requerido
    def oferta_pix():
        usuario = get_usuario_logado()

        # se quiser futuramente puxar a chave via config de banco:
        chave_pix = '00020126360014BR.GOV.BCB.PIX0114068138600001205204000053039865802BR5901N6001C62100506ADNIPO6304FE4F'  # ou email/celular/chave aleatória
        qr_code_url = url_for('static', filename='img/qrcode-pix.png')

        return render_template('ofertas/pix.html', chave_pix=chave_pix, qr_code_url=qr_code_url, usuario_logado=usuario)


    ## Prensença Membro
    @app.route('/eventos/toggle/<int:evento_id>', methods=['POST'])
    @login_requerido
    @admin_requerido
    def toggle_evento(evento_id):
        evento = Evento.query.get_or_404(evento_id)

        evento.ativo = not evento.ativo

        db.session.commit()
        return redirect(url_for('listar_eventos'))

    @app.route('/checkin/scan')
    @login_requerido
    def checkin_scan():
        return render_template('eventos/checkin_scan.html')


    # QRCode de evento
    @app.route('/eventos/qrcode/<int:evento_id>')
    @login_requerido
    @admin_requerido
    def gerar_qrcode_evento(evento_id):
        evento = Evento.query.get_or_404(evento_id)

        checkin_url = url_for('checkin_publico', evento_id=evento.id, _external=True)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(checkin_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        return render_template('eventos/qrcode.html', evento=evento, qrcode_image=img_base64)


    # Página pública de check-in via QRCode
    @app.route('/checkin/publico/<int:evento_id>', methods=['GET', 'POST'])
    @login_requerido
    def checkin_publico(evento_id):
        evento = Evento.query.get_or_404(evento_id)

        # Tenta pegar o membro pelo usuário logado (supondo que user tem membro)
        membro = get_usuario_logado

        if request.method == 'POST':
            # Se usuário logado, usa o membro dele direto
            if membro:
                presenca_existente = Presenca.query.filter_by(membro_id=membro.id, evento_id=evento.id).first()
                if presenca_existente:
                    flash("Você já registrou presença neste evento.", "info")
                else:
                    nova_presenca = Presenca(membro_id=membro.id, evento_id=evento.id)
                    db.session.add(nova_presenca)
                    db.session.commit()
                    flash("Presença registrada com sucesso!", "success")
                return redirect(url_for('eventos/checkin_publico', evento_id=evento.id))

            # Se não logado ou não tiver membro, pede nome no form e procura
            nome = request.form.get('nome')
            if not nome:
                flash("Por favor, preencha o nome.", "warning")
            else:
                membro = Membro.query.filter_by(nome=nome).first()
                if not membro:
                    flash("Membro não encontrado.", "danger")
                else:
                    presenca_existente = Presenca.query.filter_by(membro_id=membro.id, evento_id=evento.id).first()
                    if presenca_existente:
                        flash("Você já registrou presença neste evento.", "info")
                    else:
                        nova_presenca = Presenca(membro_id=membro.id, evento_id=evento.id)
                        db.session.add(nova_presenca)
                        db.session.commit()
                        flash("Presença registrada com sucesso!", "success")
                        return redirect(url_for('checkin_publico', evento_id=evento.id))

        return render_template('eventos/checkin_publico.html', evento=evento, membro=membro)
