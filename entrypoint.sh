#!/bin/bash

# Espera o banco estar pronto
echo "Aguardando o banco de dados..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "Banco de dados está pronto!"

# Cria as tabelas se ainda não existirem
flask create_db

# Sobe o servidor Flask
exec flask run --host=0.0.0.0 --port=5000
