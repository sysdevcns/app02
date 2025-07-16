#!/bin/bash
echo "Instalando dependências do sistema para pyodbc..."

set -e  # Sai imediatamente se algum comando falhar

# Atualiza os pacotes e instala dependências necessárias
apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    tdsodbc

echo "Configurando ODBC..."
# Cria configuração básica do ODBC
cat <<EOF > /etc/odbcinst.ini
[FreeTDS]
Description = FreeTDS Driver
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
EOF

echo "Dependências instaladas com sucesso!"
