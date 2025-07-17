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
#def processos_page(): st.write("Processos")
def itens_page(): st.write("Itens")
def relatorios_page(): st.write("Relatórios")
def configuracoes_page(): st.write("Configurações")


def processos_page():
    st.title("📋 Gestão de Processos")
    
    # Carrega os processos do banco de dados
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Processos ORDER BY DataInicio DESC")
                processos = cursor.fetchall()
                
                # Exibe como dataframe
                df = pd.DataFrame(processos, columns=[desc[0] for desc in cursor.description])
                st.dataframe(df, use_container_width=True)
                
                # Botão para adicionar novo processo
                if st.button("➕ Adicionar Processo"):
                    st.session_state['show_processo_modal'] = True
                    st.session_state['current_processo'] = None
                
                # Modal para edição/criação
                if st.session_state.get('show_processo_modal'):
                    with st.form(key='processo_form'):
                        st.subheader("Editar Processo" if st.session_state.get('current_processo') else "Novo Processo")
                        
                        # Campos do formulário
                        numero = st.text_input("Número do Processo", 
                                             value=st.session_state.get('current_processo', {}).get('NumeroProcesso', ''))
                        titulo = st.text_input("Título", 
                                             value=st.session_state.get('current_processo', {}).get('Titulo', ''))
                        descricao = st.text_area("Descrição", 
                                               value=st.session_state.get('current_processo', {}).get('Descricao', ''))
                        status = st.selectbox("Status", 
                                            options=['Pendente', 'Em Andamento', 'Concluído', 'Cancelado'],
                                            index=['Pendente', 'Em Andamento', 'Concluído', 'Cancelado'].index(
                                                st.session_state.get('current_processo', {}).get('Status', 'Pendente')))
                        
                        col1, col2 = st.columns(2)
                        data_inicio = col1.date_input("Data Início", 
                                                     value=pd.to_datetime(st.session_state.get('current_processo', {}).get('DataInicio', datetime.now())))
                        data_fim = col2.date_input("Data Fim (opcional)", 
                                                  value=pd.to_datetime(st.session_state.get('current_processo', {}).get('DataFim', None))
                        
                        # Botões do formulário
                        submitted = st.form_submit_button("Salvar")
                        if submitted:
                            # Lógica para salvar no banco de dados
                            try:
                                if st.session_state.get('current_processo'):
                                    # Atualizar processo existente
                                    cursor.execute("""
                                        UPDATE Processos 
                                        SET NumeroProcesso = %s, Titulo = %s, Descricao = %s, 
                                            Status = %s, DataInicio = %s, DataFim = %s
                                        WHERE ProcessoID = %s
                                    """, (numero, titulo, descricao, status, data_inicio, data_fim, 
                                          st.session_state['current_processo']['ProcessoID']))
                                else:
                                    # Criar novo processo
                                    cursor.execute("""
                                        INSERT INTO Processos 
                                        (NumeroProcesso, Titulo, Descricao, Status, DataInicio, DataFim)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (numero, titulo, descricao, status, data_inicio, data_fim))
                                
                                conn.commit()
                                st.success("Processo salvo com sucesso!")
                                st.session_state['show_processo_modal'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar processo: {e}")
                        
                        if st.form_submit_button("Cancelar"):
                            st.session_state['show_processo_modal'] = False
                
                # Adiciona botões de ação para cada processo
                st.write("## Ações")
                for processo in processos:
                    with st.expander(f"Processo {processo[1]} - {processo[2]}"):
                        col1, col2 = st.columns(2)
                        if col1.button(f"✏️ Editar", key=f"edit_{processo[0]}"):
                            st.session_state['show_processo_modal'] = True
                            st.session_state['current_processo'] = {
                                'ProcessoID': processo[0],
                                'NumeroProcesso': processo[1],
                                'Titulo': processo[2],
                                'Descricao': processo[3],
                                'Status': processo[4],
                                'DataInicio': processo[5],
                                'DataFim': processo[6]
                            }
                        
                        if col2.button(f"🗑️ Excluir", key=f"del_{processo[0]}"):
                            try:
                                cursor.execute("DELETE FROM Processos WHERE ProcessoID = %s", (processo[0],))
                                conn.commit()
                                st.success(f"Processo {processo[1]} excluído!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir: {e}")
                
        except Exception as e:
            st.error(f"Erro ao carregar processos: {e}")
        finally:
            conn.close()


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
