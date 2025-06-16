FROM python:3-alpine

LABEL org.opencontainers.image.source https://github.com/ThinkSalat/Reddit-Post-Notifier

ENV PYTHONUNBUFFERED 1

RUN adduser -D python
USER python

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ai.py .
COPY alert.py .
COPY app.py .
COPY config.py .
COPY lib.py .
COPY test.py .

ENTRYPOINT ["python", "app.py"]
