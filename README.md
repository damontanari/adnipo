# 📊 ADNIPO - Sistema de Cadastro de Membros

Sistema web para cadastro e gerenciamento de membros de uma igreja, desenvolvido com Flask e SQLite.

---

## 📦 Pré-requisitos

- Python 3.x
- Virtualenv (opcional, mas recomendado)
- Dependências instaladas:
  ```bash
  pip install -r requirements.txt


🔧 Como rodar a aplicação
📌 1. Ativar ambiente virtual (se estiver usando)
Windows (PowerShell):
.\venv\Scripts\Activate


📌 2. Variáveis de ambiente
Certifique-se de que existe um arquivo .env com:
SECRET_KEY=ifHOEU9cmFGaaG71FH8P
DATABASE_URL=sqlite:///adnipo.db
FLASK_APP=manage.py
FLASK_ENV=development


📌 3. Criar o banco de dados
flask create_db


📌 4. Criar um usuário administrador
flask create_admin admin@admin.com 123456


📌 5. Rodar a aplicação
Localhost:
flask run

Em rede (acessível pelo IP):
flask run --host=0.0.0.0 --port=5000


📋 Comandos disponíveis via manage.py

| Comando              | Descrição                               |
| :------------------- | :-------------------------------------- |
| `flask create_db`    | Cria todas as tabelas no banco de dados |
| `flask drop_db`      | Remove todas as tabelas do banco        |
| `flask create_admin` | Cria um usuário administrador           |


📁 Estrutura de pastas
app/
  templates/
    base.html
    home.html
    auth/
      login.html
    membros/
      lista.html
      novo.html
      editar.html
  routes.py
  models.py
  __init__.py
manage.py
.env
requirements.txt



📌 Comando para debug/logs detalhados
flask run --reload --debugger --host=0.0.0.0



---

## 📦 Exemplo de Makefile

Se quiser deixar tudo ainda mais rápido:

```makefile
run:
	flask run --host=0.0.0.0 --port=5000

create-db:
	flask create_db

drop-db:
	flask drop_db

create-admin:
	flask create_admin admin@admin.com 123456

--

## 📦 Utilizando os comandos com docker
docker compose up -d --build
docker compose exec flask_app flask create_db
docker compose exec flask_app flask create_admin "Admin" "admin@email.com" "senha123"