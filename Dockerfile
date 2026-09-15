FROM python:3.12-slim

WORKDIR /app

# Instala dependências de sistema necessárias para imagens e geoprocessamento
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do projeto
COPY . .

CMD ["python", "main.py"]