from app import create_app, db
from app.models import Usuario
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
def create_admin(nome, email, senha):
    from app import db
    from app.models import Usuario

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
