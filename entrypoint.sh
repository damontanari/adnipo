#!/bin/bash

<<<<<<< HEAD
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
=======
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
>>>>>>> 5b46a1d6cd7952086c52a28700c55aec590211bb
