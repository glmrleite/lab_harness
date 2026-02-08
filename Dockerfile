FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# cria usuário não-root
RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# permissões
RUN chown -R app:app /app

USER app

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers=2", "--threads=4", "--timeout=60"]
