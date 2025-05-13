#!/bin/bash
set -e  # Faz o script parar se algum comando falhar

echo "Aguardando o banco de dados iniciar..."

while ! nc -z postgres 5432; do
  sleep 1
done

echo "Banco de dados disponível!"

# Cria as tabelas no banco
flask create_db

# Cria admin padrão
flask create_admin Admin admin@adnipo.com admin

# Inicia a aplicação
flask run --host=0.0.0.0
