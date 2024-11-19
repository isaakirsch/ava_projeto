import streamlit as st
import cv2
import numpy as np
import plotly.graph_objects as go

import os
from PIL import Image
import io  
import base64

import mysql.connector
from mysql.connector import Error

def orb_sim(img1, img2):
    # Verifica o número de canais e converte para BGR se necessário
    if len(img1.shape) == 2: 
        gray1 = img1
    else:
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        
    if len(img2.shape) == 2: 
        gray2 = img2
    else:
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # ORB detector
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    # Verifica se há descritores válidos
    if des1 is None or des2 is None:
        return None

    # Matcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    
    # Calcular a similaridade 
    num_good_matches = 10 
    good_matches = matches[:num_good_matches]
    similarity = sum([match.distance for match in good_matches]) / num_good_matches
    
    # Normaliza a similaridade para um valor entre 0 e 1
    max_distance = 255  
    similarity_normalized = 1 - (similarity / max_distance)
    
    return similarity_normalized

# Função para carregar uma imagem a partir de um arquivo
def load_image(uploaded_file):
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    return cv2.imdecode(file_bytes, 0)

# Função para configurar a navegação
def navigate(page):
    st.session_state["page"] = page

# Inicializando o estado de sessão
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"
if "images_reference" not in st.session_state:
    st.session_state["images_reference"] = []
if "images_consent" not in st.session_state:
    st.session_state["images_consent"] = []
if "cadastro" not in st.session_state:
    st.session_state["cadastro"] = {"completed": False}

# Adicionar CSS para estilizar a aplicação
with open("styles.css") as f:
    st.markdown (f"<style>{f.read()}</style>", unsafe_allow_html=True)

def add_custom_css():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #050027, #0F006E);
    color: white;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0;
    padding: 0;
    font-family: 'Arial', sans-serif;
}

.container {
    text-align: center;
    width: 100%;
}

.logo {
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 40px;
    width: 400px;
}
        </style>
    """, unsafe_allow_html=True)

def welcome_page():
    add_custom_css()  
    st.markdown("<div class='container'><img src='data:image/png;base64,{}' class='logo' /></div>".format(image_base64), unsafe_allow_html=True)
    
    # Criar três colunas
    col1, col2, col3 = st.columns([1.5, 1.5, 1.5])
    
    # Deixar as colunas laterais vazias
    col1.write("")
    col3.write("")
    
    # Colocar os botões na coluna centra
    with col2:
        st.markdown("<style>div.stButton > button:first-child {width: 200px;}</style>", unsafe_allow_html=True)
        st.button("Cadastrar", on_click=navigate, args=("register",))
        st.button("Login", on_click=navigate, args=("login",))

# Transformar imagem para base64
import base64
from PIL import Image

def get_image_as_base64(image_path):
    img = Image.open(image_path)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

image_path = "LOGO_BRANCA-removebg-preview.png"
image_base64 = get_image_as_base64(image_path)

# Página de cadastro
def add_custom_css2():
    st.markdown("""
        <style>
           body, html, [data-testid="stAppViewContainer"] {
               background: #050027;
           }
        </style>
    """, unsafe_allow_html=True)

# Função para inserir os dados no banco de dados e retornar o código do usuário
def usuario(nome_instituicao, telefone, rua, bairro, numero_edificio, cep, cidade, senha):
    conexao = conectar_bd()
    if conexao:
        cursor = conexao.cursor()
        try:
            declaracao = """INSERT INTO usuario (nome_instituicao, telefone, rua, bairro, numero_edificio, cep, cidade, senha) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            dados = (nome_instituicao, telefone, rua, bairro, numero_edificio, cep, cidade, senha)
            cursor.execute(declaracao, dados)
            conexao.commit()
            
            # Captura o ID do usuário recém-cadastrado
            codigo_usuario = cursor.lastrowid
            return codigo_usuario
        except mysql.connector.Error as err:
            st.error(f"Erro ao inserir dados: {err}")
            return None
        finally:
            cursor.close()
            conexao.close()
    else:
        return None

# Função de registro da página
def register_page():
    add_custom_css2()  
    st.markdown("# CADASTRAR")

    with st.form(key="register_form"):
        institution_name = st.text_input("Nome da instituição")
        rua = st.text_input("Rua")
        bairro = st.text_input("Bairro")
        numero = st.text_input("Número")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        telefone = st.text_input("Telefone")
        password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirme a senha", type="password")

        submit_button = st.form_submit_button(label="Cadastrar")

    if submit_button:
        if password == confirm_password:
            # Realiza o cadastro e obtém o código do usuário
            codigo_usuario = usuario(institution_name, telefone, rua, bairro, numero, cep, cidade, password)
            if codigo_usuario is not None:
                st.success("Cadastro realizado com sucesso e salvo no banco de dados!")

                # Salva os dados na sessão, incluindo o código do usuário
                st.session_state["cadastro"] = {
                    "completed": True,
                    "codigo_usuario": codigo_usuario,
                    "nome": institution_name,
                    "rua": rua,
                    "bairro": bairro,
                    "numero": numero,
                    "cep": cep,
                    "cidade": cidade,
                    "telefone": telefone
                }
            else:
                st.error("Erro ao realizar o cadastro no banco de dados.")
        else:
            st.error("As senhas não coincidem. Tente novamente.")
    st.button("Voltar", on_click=navigate, args=("welcome",))



def add_custom_css3():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)

# Função para autenticar o usuário
def autenticar_usuario(nome_instituicao, senha):
    conexao = conectar_bd()  # Função para conectar ao banco de dados
    if conexao:
        cursor = conexao.cursor()
        try:
            # Verifica se o usuário existe com a senha fornecida
            cursor.execute("SELECT * FROM USUARIO WHERE nome_instituicao = %s AND senha = %s", (nome_instituicao, senha))
            usuario = cursor.fetchone()
            return usuario is not None  # Retorna True se o usuário foi encontrado
        except mysql.connector.Error as err:
            st.error(f"Erro ao autenticar: {err}")
            return False
        finally:
            cursor.close()
            conexao.close()
    return False

# Página de login
def login_page():
    add_custom_css3()
    st.markdown("# LOGIN")
    
    username = st.text_input("Nome da instituição")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if autenticar_usuario(username, password):
            st.success("Login realizado com sucesso!")
            st.session_state["logged_in"] = True  
            st.session_state["username"] = username  
            navigate("home")  
        else:
            st.error("Nome de instituição ou senha incorretos. Tente novamente.")

    st.button("Voltar", on_click=navigate, args=("welcome",))

def add_custom_css4():
    st.markdown("""
    <style>
        /* Estilização geral da página */
        body, html, [data-testid="stAppViewContainer"] {
            background-color: #050027;
            color: white;
            font-family: 'Arial', sans-serif;
        }

        /* Estilização específica para os botões nesta página */
        div.stButton > button {
            background-color: #1D1454  !important;  /* Cor de fundo dos botões */
            border: 2px solid white !important;    /* Borda branca ao redor dos botões */
            color: white !important;               /* Cor do texto dos botões */
            border-radius: 12px !important;        /* Bordas arredondadas */
            font-size: 18px !important;            /* Tamanho da fonte */
            padding: 10px 20px !important;         /* Espaçamento interno */
            margin-top: 10px !important;           /* Espaçamento superior */
            width: 100% !important;                /* Largura dos botões */
            box-shadow: none !important;           /* Remove a sombra padrão */
        }

        /* Remove a mudança de cor ao passar o mouse */
        div.stButton > button:hover {
            background-color: #050027 !important;
            color: white !important;
        }

        /* Remove a mudança de cor ao clicar */
        div.stButton > button:active, div.stButton > button:focus {
            background-color: #050027 !important;
            color: white !important;
        }

        /* Estilização do título */
        h1 {
            font-size: 40px;
            font-weight: bold;
            color: white;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
def home_page():
    add_custom_css4()
    st.button("Adicionar imagem de referência", on_click=navigate, args=("upload_reference",))
    st.button("Adicionar imagem de termo de consentimento", on_click=navigate, args=("upload_consent",))
    st.button("Adicionar imagem para verificação", on_click=navigate, args=("upload_verification",))
    st.button("Imagens de Referência", on_click=navigate, args=("registered_images_reference",))
    st.button("Imagens de Termo de Consentimento", on_click=navigate, args=("registered_images_consent",))
    st.button("Perfil do Usuário", on_click=navigate, args=("user_profile",))
    st.button("Voltar", on_click=navigate, args=("welcome",))

# Função para conexão com o banco
def conectar_bd():
    try:
        conexao = mysql.connector.connect(
            host='dbava.c3s2ysmoum5c.us-east-2.rds.amazonaws.com', 
            database='ava',
            user='isadora',
            password='kirsch06',
            port=3306 
        )
        return conexao
    except mysql.connector.Error as err:
        st.error(f"Erro ao conectar ao banco de dados: {err}")
        return None

# Função para inserir os dados na tabela PESSOA_TABELA_AUTORIZACAO
def pessoa(nome_pessoa, rua_pessoa, bairro_pessoa, numero_pessoa, cep_pessoa, cidade_pessoa, celular_pessoa, cpf_pessoa, imagem_tabela):
    conexao = conectar_bd()
    if conexao:
        cursor = conexao.cursor()
        try:
            declaracao = """INSERT INTO PESSOA_TABELA_AUTORIZACAO (nome_pessoa, rua_pessoa, bairro_pessoa, numero_pessoa, cep_pessoa, cidade_pessoa, celular_pessoa, cpf_pessoa, imagem_tabela) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            dados = (nome_pessoa, rua_pessoa, bairro_pessoa, numero_pessoa, cep_pessoa, cidade_pessoa, celular_pessoa, cpf_pessoa, imagem_tabela)
            cursor.execute(declaracao, dados)
            conexao.commit()
            st.success("Cadastro realizado com sucesso e salvo no banco de dados!")
        except mysql.connector.Error as err:
            st.error(f"Erro ao inserir dados: {err}")
        finally:
            cursor.close()
            conexao.close()

# Função para carregar a imagem
from PIL import Image
import numpy as np
import cv2

def load_image(uploaded_file):
    # Abrir a imagem com PIL e converter para array NumPy
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    
    # Verificar se a imagem é colorida (3 canais) e converter para escala de cinza
    if len(image_np.shape) == 3:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    return image_np

# Função para adicionar CSS personalizado
def add_custom_css5():
    st.markdown("""
    <style>
        body, html, [data-testid="stAppViewContainer"] {
            background: #050027;
        }
    </style>
    """, unsafe_allow_html=True)

# Página de upload de imagem de referência
def upload_reference_page():
    add_custom_css5()
    st.markdown("# CADASTRAR IMAGEM DE REFERÊNCIA")
  
    # Captura os dados do usuário
    st.session_state["cadastro"]["nome"] = st.text_input("Nome")
    st.session_state["cadastro"]["rua"] = st.text_input("Rua")
    st.session_state["cadastro"]["bairro"] = st.text_input("Bairro")
    st.session_state["cadastro"]["numero"] = st.text_input("Número")
    st.session_state["cadastro"]["cep"] = st.text_input("CEP")
    st.session_state["cadastro"]["cidade"] = st.text_input("Cidade")
    st.session_state["cadastro"]["telefone"] = st.text_input("Telefone")
    st.session_state["cadastro"]["cpf"] = st.text_input("CPF")
    
    uploaded_files = st.file_uploader("Faça upload das imagens de referência", accept_multiple_files=True)
    
    if st.button("Cadastrar Imagens"):
        if not st.session_state["cadastro"]["nome"]:
            st.error("Por favor, insira o nome.")
        else:
            conexao = conectar_bd()  
            cursor = conexao.cursor()

            for uploaded_file in uploaded_files:
                img_blob = uploaded_file.read()  
                
                # Verifica se a imagem não está vazia
                if img_blob is None or len(img_blob) == 0:
                    st.error("A imagem está vazia. Por favor, faça o upload de uma imagem válida.")
                    continue  

                st.session_state["images_reference"].append({
                    "name": st.session_state["cadastro"]["nome"],
                    "rua": st.session_state["cadastro"]["rua"],
                    "bairro": st.session_state["cadastro"]["bairro"],
                    "numero": st.session_state["cadastro"]["numero"],
                    "cep": st.session_state["cadastro"]["cep"],
                    "cidade": st.session_state["cadastro"]["cidade"],
                    "telefone": st.session_state["cadastro"]["telefone"],
                    "cpf": st.session_state["cadastro"]["cpf"],
                    "file": img_blob
                })
                
                # Inserir os dados na tabela PESSOA_TABELA_AUTORIZACAO
                sql = """
                    INSERT INTO PESSOA_TABELA_AUTORIZACAO (nome_pessoa, rua_pessoa, bairro_pessoa, numero_pessoa, cep_pessoa, cidade_pessoa, celular_pessoa, cpf_pessoa, imagem_tabela)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (st.session_state["cadastro"]["nome"],
                          st.session_state["cadastro"]["rua"],
                          st.session_state["cadastro"]["bairro"],
                          st.session_state["cadastro"]["numero"],
                          st.session_state["cadastro"]["cep"],
                          st.session_state["cadastro"]["cidade"],
                          st.session_state["cadastro"]["telefone"],
                          st.session_state["cadastro"]["cpf"],
                          img_blob)  # Usar a imagem como BLOB
                
                cursor.execute(sql, values)
            
            conexao.commit()  # Confirmar a inserção no banco de dados
            cursor.close()
            conexao.close()
            
            st.success("Imagens cadastradas com sucesso!")
            st.rerun()
    st.button("Voltar", on_click=navigate, args=("home",))


def add_custom_css6():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)
# Função para inserir o termo de consentimento no banco de dados
def salvar_termo_consentimento(nome_autorizacao, imagem_termo):
    conexao = conectar_bd()
    if conexao:
        cursor = conexao.cursor()
        try:
            declaracao = """INSERT INTO PESSOA_TABELA_AUTORIZACAO (nome_autorizacao, imagem_termo)
                            VALUES (%s, %s)"""
            dados = (nome_autorizacao, imagem_termo)
            cursor.execute(declaracao, dados)
            conexao.commit()
            st.success("Termo de consentimento salvo no banco de dados com sucesso!")
        except mysql.connector.Error as err:
            st.error(f"Erro ao inserir dados: {err}")
        finally:
            cursor.close()
            conexao.close()

# Página de cadastro de termo de consentimento
def upload_consent_page():
    add_custom_css6()
    st.markdown("# CADASTRAR IMAGEM DE TERMO DE CONSENTIMENTO")
    image_name = st.text_input("Nome da imagem")
    uploaded_file = st.file_uploader("Faça upload")
    
    if st.button("Cadastrar Imagem"):
        if not image_name:
            st.error("Por favor, insira um nome para a imagem.")
        elif not uploaded_file:
            st.error("Por favor, faça o upload de uma imagem.")
        else:
            # Ler o arquivo carregado como binário
            img_bytes = uploaded_file.read()  # Lê a imagem em formato binário
            
            # Adiciona a imagem à sessão
            st.session_state["images_consent"].append({"name": image_name, "file": img_bytes})
            st.success("Imagem de termo de consentimento cadastrada com sucesso!")
            
            # Salva no banco de dados
            salvar_termo_consentimento(image_name, img_bytes)  # Salva a imagem e o nome no banco
    
    st.button("Voltar", on_click=navigate, args=("home",))


def delete_image(image_list, image_name):
    """
    Função responsável por deletar uma imagem da lista de imagens de referência.
    :param image_list: Lista de dicionários contendo as imagens.
    :param image_name: Nome da imagem a ser deletada.
    :return: True se a exclusão foi bem-sucedida, False caso contrário.
    """
    for img in image_list:
        if img["name"] == image_name:
            # Lógica para excluir a imagem. Exemplo: remove a imagem da lista.
            image_list.remove(img)
            return True  # Retorna True se a imagem foi removida com sucesso
    return False  # Retorna False se a imagem não foi encontrada

def add_custom_css7():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)
# Página de imagens cadastradas de referência
def registered_images_reference_page():
    add_custom_css7()
    st.markdown("# IMAGENS DE REFERÊNCIA CADASTRADAS")
    
    search_query = st.text_input("Pesquise aqui...")
    filtered_images = [img for img in st.session_state["images_reference"] if search_query.lower() in img["name"].lower()]
    
    if filtered_images:
        for img in filtered_images:
            st.image(img["file"], caption=img["name"])

            # Chave única para controle de confirmação de exclusão
            confirm_key = f"confirm_delete_{img['name']}"

            # Inicializa o estado da confirmação se não existir
            if confirm_key not in st.session_state:
                st.session_state[confirm_key] = False

            # Exibe botão para excluir
            if not st.session_state[confirm_key]:
                if st.button(f"Excluir {img['name']}", key=f"delete_{img['name']}"):
                    st.session_state[confirm_key] = True
            else:
                # Mensagem de confirmação
                st.warning(f"Tem certeza que deseja excluir a imagem '{img['name']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sim", key=f"confirm_{img['name']}"):
                        # Lógica de exclusão
                        if delete_image(st.session_state["images_reference"], img["name"]):
                            st.success(f"Imagem '{img['name']}' excluída com sucesso!")
                            st.session_state[confirm_key] = False  # Resetar o estado de confirmação
                            st.session_state["images_reference"].remove(img)  # Remover a imagem da lista
                            st.experimental_rerun()  # Recarregar a página para refletir as mudanças
                with col2:
                    if st.button("Não", key=f"cancel_{img['name']}"):
                        st.session_state[confirm_key] = False  # Resetar o estado de confirmação

    else:
        st.write("Nenhuma imagem de referência encontrada.")
    st.button("Voltar", on_click=navigate, args=("home",))


def add_custom_css8():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)
# Página de imagens cadastradas de termo de consentimento
def registered_images_consent_page():
    add_custom_css7()
    st.markdown("# IMAGENS DE TERMO DE CONSENTIMENTO CADASTRADAS")
    
    search_query = st.text_input("Pesquise aqui...")
    filtered_images = [img for img in st.session_state["images_consent"] if search_query.lower() in img["name"].lower()]
    
    if filtered_images:
        for img in filtered_images:
            st.image(img["file"], caption=img["name"])
            
            if f"confirm_delete_{img['name']}" not in st.session_state:
                st.session_state[f"confirm_delete_{img['name']}"] = False

            if not st.session_state[f"confirm_delete_{img['name']}"]:
                if st.button(f"Excluir {img['name']}", key=f"delete_{img['name']}"):
                    st.session_state[f"confirm_delete_{img['name']}"] = True
            else:
                st.warning(f"Tem certeza que deseja excluir o termo de consentimento '{img['name']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sim", key=f"confirm_{img['name']}"):
                        if delete_image(st.session_state["images_consent"], img["name"]):
                            st.success(f"Termo de consentimento '{img['name']}' excluído com sucesso!")
                            st.session_state[f"confirm_delete_{img['name']}"] = False
                            st.rerun()
                with col2:
                    if st.button("Não", key=f"cancel_{img['name']}"):
                        st.session_state[f"confirm_delete_{img['name']}"] = False
    else:
        st.write("Nenhum termo de consentimento encontrado.")
    st.button("Voltar", on_click=navigate, args=("home",))


def add_custom_css9():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)

# Página para upload e verificação de imagem
def blob_to_numpy(blob):
    # Converte BLOB em um array NumPy
    # O BLOB deve ser um objeto de bytes
    nparr = np.frombuffer(blob, np.uint8)
    # Decodifica a imagem usando OpenCV
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def upload_verification_page():
    add_custom_css9()
    st.markdown("# ADICIONAR IMAGEM PARA VERIFICAÇÃO")
    uploaded_file = st.file_uploader("Faça upload da imagem para verificação")
    
    if uploaded_file:
        verification_img = load_image(uploaded_file)
        st.image(verification_img, caption="Imagem para verificação")
        
        st.markdown("## Escolher Imagem de Referência")
        reference_options = [img["name"] for img in st.session_state["images_reference"]]
        selected_reference = st.selectbox("Selecione uma referência", reference_options)

        if st.button("Verificar"):
            reference_blob = next(img["file"] for img in st.session_state["images_reference"] if img["name"] == selected_reference)
            reference_img = blob_to_numpy(reference_blob)  # Convertendo BLOB para array NumPy
            similarity = orb_sim(verification_img, reference_img)
            
            if similarity is None:
                st.error("Não foi possível calcular a similaridade. Tente outra imagem.")
            else:
                st.write(f"Similaridade calculada: {similarity:.2f}")

                # Adiciona a lógica para calcular os valores para o gráfico
                labels = ['Similaridade', 'Diferença']
                values = [similarity * 100, 100 - (similarity * 100)]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
                st.plotly_chart(fig)

    st.button("Voltar", on_click=navigate, args=("home",))

def add_custom_css10():
    st.markdown("""
<style>
           body, html, [data-testid="stAppViewContainer"] {
    background: #050027;
}
        </style>
    """, unsafe_allow_html=True)

# Função para exibir o perfil do usuário
def user_profile_page():
    add_custom_css10()  
    st.markdown("# PERFIL DO USUÁRIO")

    # Verifica se os dados do usuário estão na sessão
    if "cadastro" in st.session_state and st.session_state["cadastro"].get("completed"):
        # Conectar ao banco de dados para recuperar os dados do usuário
        conexao = conectar_bd()
        if conexao:
            cursor = conexao.cursor()
            st.write()
            try:
                # Captura o código do usuário
                codigo_usuario = st.session_state["cadastro"].get("codigo_usuario")

                # Verifica se o código do usuário existe na sessão
                if codigo_usuario is None:
                    st.warning("O código do usuário não foi encontrado na sessão. Por favor, tente cadastrar novamente.")
                    return

                # Substitua 'usuario' pelo nome correto da tabela
                cursor.execute("SELECT nome_instituicao, rua, bairro, numero_edificio_, cep, cidade, telefone FROM usuario WHERE codigo_usuario = %s", (codigo_usuario,))
                user_data = cursor.fetchone()
                
                if user_data:
                    # Atribui os dados a variáveis
                    nome_instituicao, rua, bairro, numero_edificio_, cep, cidade, telefone = user_data
                    # Exibe os dados
                    st.write(f"**Nome da instituição**: {nome_instituicao}")
                    st.write(f"**Rua**: {rua}")
                    st.write(f"**Bairro**: {bairro}")
                    st.write(f"**Número**: {numero_edificio_}")
                    st.write(f"**CEP**: {cep}")
                    st.write(f"**Cidade**: {cidade}")
                    st.write(f"**Telefone**: {telefone}")
                else:
                    st.warning("Nenhum dado cadastrado encontrado para o código de usuário fornecido.")
            except mysql.connector.Error as err:
                st.error(f"Erro ao recuperar dados: {err}")
            finally:
                cursor.close()
                conexao.close()
    else:
        st.warning("Nenhum dado cadastrado encontrado. Por favor, faça o cadastro primeiro.")

    st.button("Voltar", on_click=navigate, args=("home",))


# Controle de navegação
if st.session_state["page"] == "welcome":
    welcome_page()
elif st.session_state["page"] == "register":
    register_page()
elif st.session_state["page"] == "login":
    login_page()
elif st.session_state["page"] == "home":
    home_page()
elif st.session_state["page"] == "upload_reference":
    upload_reference_page()
elif st.session_state["page"] == "upload_consent":
    upload_consent_page()
elif st.session_state["page"] == "upload_verification":
    upload_verification_page()
elif st.session_state["page"] == "registered_images_reference":
    registered_images_reference_page()
elif st.session_state["page"] == "registered_images_consent":
    registered_images_consent_page()
elif st.session_state["page"] == "user_profile":
    user_profile_page()
