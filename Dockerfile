# Usa uma imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de requirements e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto para o container
COPY . .

# Torna o entrypoint executável
RUN chmod +x /entrypoint.sh

# Expõe a porta 5000
EXPOSE 5000

# Define a variável de ambiente padrão para o Flask
ENV FLASK_APP=manage.py
ENV FLASK_ENV=development

# Define o entrypoint do container
ENTRYPOINT ["/entrypoint.sh"]
