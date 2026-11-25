FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHAT_HOST=servidor \
    CHAT_PORTA=5000

WORKDIR /app
COPY *.py ./

# Padrão: cliente interativo. O serviço "demo" do docker-compose roda o demo.py.
CMD ["python", "cliente.py"]
