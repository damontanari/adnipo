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
@click.argument('email')
@click.argument('senha')
@with_appcontext
def create_admin(email, senha):
    """Cria um usuário administrador"""
    admin = Usuario(nome="Admin", email=email, is_admin=True)
    admin.set_senha(senha)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin criado: {email}")
