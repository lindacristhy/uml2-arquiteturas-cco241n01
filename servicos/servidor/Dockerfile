FROM python:3.12-slim

# Mostra os logs na hora (sem buffer) e não gera arquivos .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHAT_HOST=0.0.0.0 \
    CHAT_PORTA=5000

WORKDIR /app
COPY *.py ./
COPY tests ./tests

# Só sobe a imagem se os testes passarem
RUN python -m unittest discover -s tests

EXPOSE 5000

# Saudável = a porta TCP do chat aceita conexões
HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=5 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 5000), 2).close()"

CMD ["python", "servidor.py"]
