#!/bin/bash

# Espera o banco ficar disponível
echo "Aguardando o banco de dados iniciar..."

while ! nc -z postgres 5432; do
  sleep 1
done

echo "Banco de dados disponível!"

# Cria o banco e tabelas
flask create_db

# (opcional) cria um admin padrão
flask create_admin Admin admin@adnipo.com admin

# Inicia a aplicação Flask
flask run --host=0.0.0.0
