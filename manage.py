from app import create_app, db
from app.models import Usuario, Publico
import click
from flask.cli import with_appcontext

app = create_app()

@app.cli.command("create_db")
@with_appcontext
def create_db():
    """Cria as tabelas no banco"""
    db.create_all()
    click.echo("Banco de dados criado!")

@app.cli.command("drop_db")
@with_appcontext
def drop_db():
    """Remove todas as tabelas"""
    db.drop_all()
    click.echo("Banco de dados removido!")

@app.cli.command("create_admin")
@click.argument("nome")
@click.argument("email")
@click.argument("senha")
@with_appcontext
def create_admin(nome, email, senha):
    """Cria um usuário admin"""
    if Usuario.query.filter_by(email=email).first():
        print("Já existe um usuário com esse email.")
        return

    novo_admin = Usuario(
        nome=nome,
        email=email,
        is_admin=True
    )
    novo_admin.set_senha(senha)
    db.session.add(novo_admin)
    db.session.commit()
    print(f"Admin {nome} ({email}) criado com sucesso.")

@app.cli.command("create_publicos")
@with_appcontext
def create_publicos():
    """Insere públicos padrão"""
    publicos_padrao = [
        'Todos',
        'Sem ofício',
        'Cooperador',
        'Louvor',
        'Líderes',
        'Diaconato',
        'Presbiterio',
        'Pastoreio'
    ]

    for nome in publicos_padrao:
        if not Publico.query.filter_by(nome=nome).first():
            db.session.add(Publico(nome=nome))
    db.session.commit()
    print("Públicos padrão inseridos com sucesso.")


@app.cli.command("reset_db")
@click.argument("admin_nome")
@click.argument("admin_email")
@click.argument("admin_senha")
@with_appcontext
def reset_db(admin_nome, admin_email, admin_senha):
    """Remove todas as tabelas, recria o banco, cria públicos e o admin"""
    # Dropa tudo
    db.drop_all()
    click.echo("Banco de dados removido.")

    # Cria novamente
    db.create_all()
    click.echo("Banco de dados recriado.")

    # Adiciona públicos padrão
    publicos_padrao = [
        'Todos',
        'Sem ofício',
        'Cooperador',
        'Louvor',
        'Líderes',
        'Diaconato',
        'Presbiterio',
        'Pastoreio'
    ]

    from app.models import Publico, Usuario

    for nome in publicos_padrao:
        if not Publico.query.filter_by(nome=nome).first():
            db.session.add(Publico(nome=nome))
    click.echo("Públicos padrão inseridos.")

    # Cria admin
    if Usuario.query.filter_by(email=admin_email).first():
        click.echo("Já existe um usuário com esse email.")
    else:
        novo_admin = Usuario(
            nome=admin_nome,
            email=admin_email,
            is_admin=True
        )
        novo_admin.set_senha(admin_senha)
        db.session.add(novo_admin)
        click.echo(f"Admin {admin_nome} ({admin_email}) criado.")

    # Commit final
    db.session.commit()
    click.echo("Reset completo.")
