#!/bin/bash

# Configurações do servidor Streamlit
PORT=${PORT:-8501}
ADDRESS="0.0.0.0"

# Executa o script de pré-build se existir
if [ -f ./setup.sh ]; then
    chmod +x ./setup.sh
    ./setup.sh
fi

# Instala dependências adicionais se necessário
if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi

# Inicia a aplicação Streamlit
echo "Iniciando servidor Streamlit na porta $PORT..."
streamlit run app.py \
    --server.port=$PORT \
    --server.address=$ADDRESS \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false