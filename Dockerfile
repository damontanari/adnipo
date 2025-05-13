FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rodar o manage.py por padrão (mas pode sobrescrever no compose se quiser)
CMD ["flask", "run", "--host=0.0.0.0"]
