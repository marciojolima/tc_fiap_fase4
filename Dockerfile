# 1. Imagem Base (Python 3.12 Slim para ser mais leve)
FROM python:3.12-slim

# 2. Variáveis de Ambiente para otimizar o Python no Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 3. Instalar dependências de sistema (necessárias para TensorFlow e Numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Instalar Poetry
RUN pip install --no-cache-dir poetry

# 5. Configurar diretório de trabalho
WORKDIR /app

# 6. Copiar arquivos de dependência
COPY pyproject.toml ./

# 7. Instalar Dependências
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

COPY src/ ./src/
COPY models/ ./models/

# 9. Expor a porta 8000
EXPOSE 8000

# 10. Comando para rodar a API
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
