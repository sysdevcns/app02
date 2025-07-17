import os
import psycopg
import streamlit as st
from datetime import datetime, timedelta
from extra_streamlit_components import CookieManager
from urllib.parse import urlparse

# 1. PRIMEIRO: Configuração da página (DEVE ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Gestão e Controle",
    page_icon=":gear:",
    layout="wide"
)

# 2. Inicializa o gerenciador de cookies APÓS set_page_config()
cookie_manager = CookieManager(key='auth_manager')

# Configuração do CSS externo
def load_css():
    try:
        with open("w3s.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        w3schools_css = """
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            h1, h2, h3 { color: #4CAF50; }
            .stButton>button { background-color: #4CAF50; color: white; }
        </style>
        """
        st.markdown(w3schools_css, unsafe_allow_html=True)

# Conexão Postgre
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        st.error("Variável DATABASE_URL não encontrada!")
        return None
    try:
        url = urlparse(db_url)
        conn = psycopg.connect(
            host=url.hostname,
            port=url.port,
            dbname=url.path[1:],
            user=url.username,
            password=url.password
        )
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None


# Autenticação
def authenticate_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Users WHERE Username = %s AND Password = %s", 
                (username, password)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            st.error(f"Erro ao autenticar: {e}")
        finally:
            conn.close()
    return False

# Verificação de autenticação
def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    auth_cookie = cookie_manager.get('auth')
    if auth_cookie:
        st.session_state['authenticated'] = True
        st.session_state['username'] = auth_cookie['username']

# Página de Login
def login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Login"):
            if authenticate_user(username, password):
                cookie_manager.set(
                                   'auth',
                                   {'username': username},
                                   expires_at=datetime.now() + timedelta(days=1))
                st.session_state.update({
                                         'authenticated': True,
                                         'username': username
                                        })
                                  
                st.rerun()
            else:
                st.error("Credenciais inválidas")

# Logout
def logout():
    """Função de logout segura que evita problemas com rerun"""
    try:
        # Limpa os cookies
        if cookie_manager.get('auth'):
            cookie_manager.delete('auth')
    except Exception as e:
        st.warning(f"Erro ao limpar cookies: {str(e)}")
    
    # Marca para redirecionar para login
    st.session_state.clear()
    st.session_state['redirect_to_login'] = True

# Menu Principal
def main_menu():
    # Botão de logout (mantém o mesmo)
    st.sidebar.button("Logout", on_click=logout)
    
    # Restante da sua lógica de menu...
    if st.session_state.get('redirect_to_login'):
        return  # Sai da função se logout foi acionado
    
    st.title(f"Bem-vindo, {st.session_state['username']}!")
    
    menu = {
        "Dashboard": dashboard_page,
        "Processos": processos_page,
        "Itens": itens_page,
        "Relatórios": relatorios_page,
        "Configurações": configuracoes_page
    }
    
    selected = st.sidebar.radio("Menu", list(menu.keys()))
    menu[selected]()

# Páginas de conteúdo (implemente conforme necessário)
def dashboard_page(): st.write("Dashboard")
def processos_page(): st.write("Processos")
def itens_page(): st.write("Itens")
def relatorios_page(): st.write("Relatórios")
def configuracoes_page(): st.write("Configurações")

# Função principal
def main():
    load_css()
    # Verifica redirecionamento de logout
    if st.session_state.get('redirect_to_login', False):
        st.session_state.pop('redirect_to_login', None)
        login_page()
        return  # Importante para evitar execução dupla
    check_authentication()    
    if st.session_state.get('authenticated'):
        main_menu()
    else:
        login_page()

if __name__ == "__main__":
    # 4. Ponto de entrada principal
    main()
