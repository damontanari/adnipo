FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh .

RUN chmod +x ./entrypoint.sh

ENV FLASK_APP=app

ENTRYPOINT ["./entrypoint.sh"]