FROM python:3.11-slim

WORKDIR /app

# Copia os arquivos necessários
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do código da aplicação
COPY . .

# Copia o entrypoint.sh e dá permissão de execução
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Define o entrypoint do container
ENTRYPOINT ["/entrypoint.sh"]
