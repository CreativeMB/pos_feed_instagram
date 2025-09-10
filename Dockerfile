FROM python:3.12-slim

WORKDIR /app
COPY app.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Gunicorn escuchando en el puerto que Fly asigna
CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "app:app"]
