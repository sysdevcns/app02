#!/bin/bash
# Executa o script de pré-build se existir
if [ -f ./setup.sh ]; then
    ./setup.sh
fi

# Inicia a aplicação Streamlit
streamlit run seu_app.py