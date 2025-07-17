# 0. Dependencias
import os
import psycopg
import pandas as pd
import streamlit as st

from urllib.parse import urlparse
from datetime import datetime, timedelta
from extra_streamlit_components import CookieManager


# 1. Configuração da página
st.set_page_config(
    page_title="Gestão e Controle",
    page_icon=":gear:",
    layout="wide"
)


# 2. Inicializa o gerenciador de cookies
cookie_manager = CookieManager(key='auth_manager')


# 3. Configuração do CSS externo
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


# 4. Conexão com BD Postgre
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


# 5. Autenticação de usuário
def authenticate_user(username, password):
    """Autentica usuário sem diferenciar maiúsculas/minúsculas"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM Users WHERE LOWER(Username) = LOWER(%s) AND Password = %s", 
                    (username, password))
                result = cursor.fetchone() is not None
                st.write(f"Resultado da autenticação: {result}")  # Debug
                return result
        except Exception as e:
            st.error(f"Erro ao autenticar: {e}")
            return False
        finally:
            conn.close()
    return False


# 6. Validação de sessão
def check_authentication():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    auth_cookie = cookie_manager.get('auth')
    if auth_cookie:
        st.session_state['authenticated'] = True
        st.session_state['username'] = auth_cookie['username']
    
    return st.session_state['authenticated']
    

# 7. Página de Login
def login_page():
    st.title("LOGIN - Sistema de Informações Gerenciais")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Login"):
            st.write("Botão login pressionado")  # Debug
            if authenticate_user(username, password):
                st.write("Autenticação bem-sucedida")  # Debug
                cookie_manager.set(
                    'auth',
                    {'username': username},
                    expires_at=datetime.now() + timedelta(days=1))
                st.session_state.update({
                    'authenticated': True,
                    'username': username
                })
                st.write("Session state atualizado, redirecionando...")  # Debug
                st.rerun()
            else:
                st.error("Credenciais inválidas")
                

# 8. Realizar logout
def logout():
    try:
        if cookie_manager.get('auth'):
            cookie_manager.delete('auth')
    except:
        pass
    
    # Limpeza completa da sessão
    st.session_state.clear()
    
    # Solução universal para rerun
    if hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()
    else:
        st.rerun()


# 9. Menu Principal
def main_menu():
    # Registra atividade a cada interação
    st.session_state['last_activity'] = datetime.now()
    
    st.title(f"Bem-vindo, {st.session_state['username']}!")
    
    # Botão de logout sem callback imediato
    if st.sidebar.button("Logout"):
        logout()  # Chama a função, forçar o rerun
    
    menu = {
        "Dashboard": dashboard_page,
        "Processos": processos_page,
        "Itens": itens_page,
        "Relatórios": relatorios_page,
        "Configurações": configuracoes_page
    }
    
    selected = st.sidebar.radio("Menu", list(menu.keys()))
    menu[selected]()

# 10. Páginas de conteúdo


# 10A. Páginas de conteúdo
def dashboard_page(): st.write("Dashboard")
    

# 10B. Páginas de conteúdo
def processos_page():
    st.title("📋 Gestão de Processos")
    
    # Inicializa a session_state
    if 'show_processo_modal' not in st.session_state:
        st.session_state['show_processo_modal'] = False
    if 'current_processo' not in st.session_state:
        st.session_state['current_processo'] = None
    if 'show_delete_modal' not in st.session_state:
        st.session_state['show_delete_modal'] = False

    # Carrega os processos do banco de dados
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Processos ORDER BY DataInicio DESC")
                processos = cursor.fetchall()
                
                if processos:
                    # Cria DataFrame
                    df = pd.DataFrame(processos, columns=[desc[0] for desc in cursor.description])
                    
                    # Adiciona coluna de ações
                    df['Ações'] = ""
                    
                    # Configuração das colunas para o data_editor
                    column_config = {
                        col: {"width": "medium"} for col in df.columns
                    }
                    column_config["Ações"] = st.column_config.Column(
                        "Ações",
                        width="small",
                        disabled=True
                    )
                    
                    # Exibe o DataFrame com os botões
                    st.data_editor(
                        df,
                        column_config=column_config,
                        hide_index=True,
                        use_container_width=True,
                        height=400,
                        key="processos_table"
                    )
                    
                    # Adiciona botões de ação para cada linha
                    for idx, processo in enumerate(processos):
                        cols = st.columns([1]*len(df.columns)  # Cria uma coluna para cada coluna do DF
                        
                        # Preenche as colunas com os dados
                        for i, col in enumerate(df.columns[:-1]):  # Exceto a coluna de ações
                            with cols[i]:
                                st.text(str(processo[i]))
                        
                        # Coluna de ações
                        with cols[-1]:
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️", key=f"edit_{processo[0]}"):
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
                            with col2:
                                if st.button("🗑️", key=f"del_{processo[0]}"):
                                    st.session_state['show_delete_modal'] = True
                                    st.session_state['processo_to_delete'] = processo[0]
                                    st.session_state['processo_numero'] = processo[1]
                    
                    # Botão para adicionar novo processo
                    if st.button("➕ Adicionar Processo"):
                        st.session_state['show_processo_modal'] = True
                        st.session_state['current_processo'] = None
                
                else:
                    st.info("Nenhum processo cadastrado ainda.")
                    if st.button("➕ Adicionar Processo"):
                        st.session_state['show_processo_modal'] = True
                        st.session_state['current_processo'] = None

                # Modal para edição/criação
                if st.session_state['show_processo_modal']:
                    with st.form(key='processo_form'):
                        st.subheader("📝 Editar Processo" if st.session_state['current_processo'] else "🆕 Novo Processo")
                        
                        current = st.session_state['current_processo'] or {}
                        
                        numero = st.text_input("Número do Processo*", 
                                             value=current.get('NumeroProcesso', ''))
                        titulo = st.text_input("Título*", 
                                             value=current.get('Titulo', ''))
                        descricao = st.text_area("Descrição", 
                                               value=current.get('Descricao', ''))
                        status = st.selectbox("Status*", 
                                            options=['Pendente', 'Em Andamento', 'Concluído', 'Cancelado'],
                                            index=['Pendente', 'Em Andamento', 'Concluído', 'Cancelado'].index(
                                                current.get('Status', 'Pendente')))
                        
                        col1, col2 = st.columns(2)
                        data_inicio = col1.date_input("Data Início*", 
                                                    value=pd.to_datetime(current.get('DataInicio', datetime.now())))
                        
                        data_fim_value = current.get('DataFim')
                        data_fim = col2.date_input("Data Fim (opcional)", 
                                                 value=pd.to_datetime(data_fim_value) if data_fim_value else None)
                        
                        submitted = st.form_submit_button("💾 Salvar")
                        cancelado = st.form_submit_button("❌ Cancelar")
                        
                        if submitted:
                            if not numero or not titulo:
                                st.error("Campos obrigatórios (*) devem ser preenchidos")
                            else:
                                try:
                                    if st.session_state['current_processo']:
                                        cursor.execute("""
                                            UPDATE Processos 
                                            SET NumeroProcesso = %s, Titulo = %s, Descricao = %s, 
                                                Status = %s, DataInicio = %s, DataFim = %s
                                            WHERE ProcessoID = %s
                                        """, (numero, titulo, descricao, status, data_inicio, data_fim, 
                                              st.session_state['current_processo']['ProcessoID']))
                                    else:
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
                        
                        if cancelado:
                            st.session_state['show_processo_modal'] = False
                            st.rerun()
                
                # Modal para exclusão
                if st.session_state['show_delete_modal']:
                    st.warning(f"Tem certeza que deseja excluir o processo {st.session_state['processo_numero']}?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmar"):
                            try:
                                cursor.execute("DELETE FROM Processos WHERE ProcessoID = %s", 
                                             (st.session_state['processo_to_delete'],))
                                conn.commit()
                                st.success("Processo excluído com sucesso!")
                                st.session_state['show_delete_modal'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir: {e}")
                    with col2:
                        if st.button("❌ Cancelar"):
                            st.session_state['show_delete_modal'] = False
                
        except Exception as e:
            st.error(f"Erro ao carregar processos: {e}")
        finally:
            conn.close()

# 10C. Páginas de conteúdo
def itens_page(): st.write("Itens")
    

# 10D. Páginas de conteúdo
def relatorios_page(): st.write("Relatórios")
    

# 10E. Páginas de conteúdo
def configuracoes_page(): st.write("Configurações")


# 11. Script de inicialização
def main():
    load_css()
    # Checar a sessão
    if not st.session_state.get('authenticated', False):
        login_page()
        return
    main_menu()



if __name__ == "__main__":
    # Ponto de partida
    main()
