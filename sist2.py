import locale
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime,timedelta
import time
from PIL import Image
import base64
from io import BytesIO

# Configuração da página com título e favicon
st.set_page_config(
    page_title="Sistema de Controle",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Função para converter a imagem em base64
def image_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Definindo uma função para a tela de carregamento
def show_loading_screen():
    # Carregar a imagem
    logo = Image.open("planilha/logo.png")  # Verifique o caminho da sua logo
    logo_base64 = image_to_base64(logo)  # Converte a imagem para base64

   # Mostrar a tela de carregamento com a imagem centralizada
    st.markdown(
        f"""
        <style>
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
            margin: 0;  /* Remove margens */
            padding: 0; /* Remove espaçamentos */
        }}
        img {{
            max-width: 100%; /* Garante que a imagem não exceda a largura da tela */
            height: auto; /* Mantém a proporção da imagem */
        }}
        </style>
        <div class="loading">
            <img src="data:image/png;base64,{logo_base64}" width="800" style="margin-top: 5px;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Controla se o sistema foi inicializado
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Se o sistema não foi inicializado, exibe a tela de carregamento
if not st.session_state.initialized:
    # Cria um espaço reservado para a tela de carregamento
    loading_placeholder = st.empty()
    with loading_placeholder:
        show_loading_screen()
    
    # Simula o tempo de carregamento dos dados
    time.sleep(3)  # Simule o carregamento de dados
    
    # Marca o sistema como inicializado
    st.session_state.initialized = True
    
    # Limpa a tela de carregamento
    loading_placeholder.empty()  # Remove a tela de carregamento

# Estilos customizados do Streamlit
st.markdown(
    """
    <style>
        .main {
            background-color: rgba(0, 0, 0, 0.2);
        }
        .sidebar .sidebar-content {
            background-color: rgba(0, 0, 0, 0.2);
        }
        .blinking-yellow {
            animation: blinker 1s linear infinite;
            color: yellow;
            background-color: rgba(255, 255, 0, 0.1);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        .blinking-red {
            animation: blinker 1s linear infinite;
            color: red;
            background-color: rgba(255, 0, 0, 0.1);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        .stApp {
        background: url("") no-repeat center center fixed;
        background-size: cover;
        opacity: 80%
        }
        @keyframes blinker {
            80% { opacity: 0; }
        }
        
    </style>
    """,
    unsafe_allow_html=True
)

# Ocultar colunas desnecessárias
colunas_para_ocultar = ['Emp', 'Código', 'Razão', 'UF', 'Tp.Venda', 'F.Pagto', 'Vendedor', '% Comissão', 'Operador', '% Comissão.1', '% ICMS', '% IPI', 'Vl.Desc.', 'Atrasado']


# Carregar os dados e ocultar colunas desnecessárias
@st.cache_data
def load_data(file_path='planilha/PEDIDOS_VOLPE8.XLSX'):
    try:
        df = pd.read_excel(file_path)
        return df.drop(columns=colunas_para_ocultar, errors='ignore')
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

df = load_data()

# Contando os modelos únicos
modelos_unicos = df['Modelo'].nunique()
df['Valor Unit.'] = pd.to_numeric(df['Valor Unit.'], errors='coerce')
df['Qtd.'] = pd.to_numeric(df['Qtd.'], errors='coerce')

# Substituir NaN por 0, ou trate de outra forma, conforme a necessidade
df['Valor Unit.'].fillna(0, inplace=True)
df['Qtd.'].fillna(0, inplace=True)

# Agora é seguro multiplicar
df['Valor Total'] = df['Valor Unit.'] * df['Qtd.']

print(df[['Valor Unit.', 'Qtd.', 'Valor Total']])

df = df[df['UN'] != 'KG']

# Exemplo: Remover linhas com 'Fantasia' em uma lista específica
df = df[~df['Fantasia'].isin(['PRIME', 'AMD 5', 'AMD 10', 'FREXCO','SESC INTERLAGOS','RODRIGO MELO','FOXMIX','CCINTER ANTÔNIO', 'L A REFRIGERACAO','NACAO NATURAL'])]

# Verifique as colunas que você sabe que são de datas
colunas_de_data = ['Dt.pedido', 'Dt.fat.', 'Prev.entrega']

df['Status'] = 'Pendente'

# Calcular o total de pedidos únicos
total_pedidos = df['Ped. Cliente'].nunique()

# Exibir o total de pedidos como uma linha adicional
estatisticas_gerais = pd.DataFrame({
    'Estatística': ['Total de Pedidos'],
    'Valor': [total_pedidos]
})

    # Cria uma coluna auxiliar para indicar quais linhas foram atualizadas
df['Status_Atualizado'] = df['Fantasia'] == ' '

# Define a função `update_status` somente para pedidos não atualizados
now = datetime.now()
df['Dt.fat.'] = pd.to_datetime(df['Dt.fat.'], errors='coerce')
df['Prev.entrega'] = pd.to_datetime(df['Prev.entrega'], errors='coerce')

def format_currency(value, currency_symbol='R$'):
    # Formata o valor com separadores de milhar e duas casas decimais
    return f"{currency_symbol}{value:,.2f}"

def update_status(row):
    if row['Status_Atualizado']:
        return row['Status']  # Retorna o status já definido pela função anterior
    if pd.isnull(row['Dt.fat.']):
        return 'Atrasado' if row['Prev.entrega'] < now else 'Pendente'
    return 'Entregue'

# Atualiza status, respeitando as linhas que já foram atualizadas
df['Status'] = df.apply(update_status, axis=1)

# Remove a coluna auxiliar
df.drop(columns='Status_Atualizado', inplace=True)

# Contagem de pedidos pendentes e atrasados
pendente = (df['Status'] == 'Pendente').sum()
atrasado = (df['Status'] == 'Atrasado').sum()

# Seleção de perfil
perfil = st.sidebar.selectbox("Selecione o Perfil", ["Administrador", "Separação", "Compras", "Embalagem"])

# Converte colunas de data e calcula 'Valor Total'
df['Valor Total'] = df['Valor Unit.'] * df['Qtd.']
df['Valor Total'] = df['Valor Total'].apply(lambda x: f'R${x:,.2f}')

def calcular_pendentes_atrasados(df):
    pendentes = (df['Status'] == 'Pendente').sum()
    atrasados = (df['Status'] == 'Atrasado').sum()
    return pendentes, atrasados

def create_value_bar_chart2(df, Produto, Modelo):
    # Calcular a frequência de cada valor na coluna especificada
    contagem = df[Produto].value_counts().reset_index()
    contagem.columns = [Produto, 'Frequência']

    # Mesclar com o DataFrame original para incluir o Modelo no gráfico
    contagem = contagem.merge(df[[Produto, Modelo]], on=Produto, how='left').drop_duplicates()

    # Criar o gráfico de barras interativo com hover data
    bar_chart2 = px.bar(
        contagem, 
        x=Produto, 
        y='Frequência', 
        title='Total por Referência',
        labels={Produto: 'Código', 'Frequência': 'Quantidade'},
        color='Frequência', 
        color_continuous_scale='Viridis',
        hover_data={Produto: True, 'Frequência': True, Modelo: True}  # Incluir o Modelo no hover
    )

    # Customizações adicionais
    bar_chart2.update_layout(
        xaxis_title='Código do Produto',
        yaxis_title='Número de Pedidos',
        xaxis_tickangle=-45,
        bargap=0.2,  # Ajuste do espaçamento entre as barras
        xaxis=dict(
            range=[0, 30],  # Define o intervalo inicial exibido
            fixedrange=False  # Permite rolagem horizontal
        )
    )

    # Retornar o gráfico
    return bar_chart2

# Criação de gráficos
def create_percentage_chart(df):
    # Contando o total de pedidos por status
    total_pedidos = df['Status'].value_counts()
    
    # Calculando a porcentagem
    total = total_pedidos.sum()
    percentage = (total_pedidos / total) * 100
    
    percentage_summary = percentage.reset_index()
    percentage_summary.columns = ['Status', 'Percentual']
    
    # Gráfico de pizza para mostrar a porcentagem
    pie_chart = px.pie(percentage_summary, 
                       values='Percentual', 
                       names='Status', 
                       title='Porcentagem de Pedidos por Status')

    return pie_chart

def guia_dashboard():
    # Cabeçalho para Estatísticas Gerais
    st.markdown("<h3>Estatísticas Gerais <small style='font-size: 0.4em;'>(mês atual)</small></h3>", unsafe_allow_html=True)
    
    # Coloca as estatísticas na horizontal no topo da tela
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Pedidos", total_pedidos)
    with col2:
        st.metric("Total de Itens", len(df))
    with col3:
        st.metric("Total de Produtos Pendentes", pendente)
    with col4:
        st.metric("Total por Referência", modelos_unicos)
    
    # Espaçamento vertical entre as seções
    st.write(" ")
    
    # Configura duas linhas para os gráficos abaixo das estatísticas
    # Primeira linha de gráficos
    st.plotly_chart(create_percentage_chart(df), use_container_width=True)
    
    
    # Espaçamento vertical entre as linhas de gráficos
    st.write(" ")

     # Segunda linha de gráficos que ocupa toda a largura
    st.plotly_chart(create_value_bar_chart2(df, 'Produto', 'Modelo'), use_container_width=True)

    separacao_df, compras_df = mover_pedidos(df)

    st.markdown("<h3>Pedidos Pendentes<small style='font-size: 0.4em;'> (por setor)</small></h3>", unsafe_allow_html=True)

    # Coloca as estatísticas na horizontal no topo da tela
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Separação", len(separacao_df))  # Contagem de pedidos em separação
    with col2:
        st.metric("Compras", len(compras_df))      # Contagem de pedidos em compras
    with col3:
        st.metric("Embalagem", '?')                   # Você pode atualizar isso conforme necessário
    with col4:
        st.metric("Expedição", '?')                   # Você pode atualizar isso conforme necessário


def guia_carteira():
    st.title("Carteira")
    
    # Filtrando o DataFrame para ocultar linhas com UN igual a KG
    df_filtrado = df[df['UN'] != 'KG']
    
    cliente_selecionado = st.selectbox("Selecione o Cliente", ["Todos os Clientes"] + df_filtrado['Fantasia'].unique().tolist())
    pedidos_cliente = df_filtrado if cliente_selecionado == "Todos os Clientes" else df_filtrado[df_filtrado['Fantasia'] == cliente_selecionado]
    
    pedido_filtro = st.text_input("Filtrar por número de pedido:")
    status_filtro = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Atrasado", "Entregue"])
    
    if pedido_filtro:
        pedidos_cliente = pedidos_cliente[pedidos_cliente['Ped. Cliente'].astype(str).str.contains(pedido_filtro)]
    
    if status_filtro != "Todos":
        pedidos_cliente = pedidos_cliente[pedidos_cliente['Status'] == status_filtro]

    # Exibir número de linhas após a filtragem
    total_linhas_depois = pedidos_cliente.shape[0]
    st.write(f"Número de linhas: {total_linhas_depois}")
    
    st.dataframe(pedidos_cliente, use_container_width=True)

def guia_notificacoes():
    st.title("Notificações")
    st.write("Todas novidades do Sistema e Atualizações serão notificadas neste campo.")

def mover_pedidos(df):
    # Filtra os pedidos que têm '-' no Nr.pedido
    pedidos_com_hifen = df[df['Nr.pedido'].astype(str).str.contains('-')]
    pedidos_sem_hifen = df[~df['Nr.pedido'].astype(str).str.contains('-')]
    
    # Atualiza o DataFrame de separação e compras
    compras_df = pedidos_com_hifen[pedidos_com_hifen['Status'].isin(['Pendente'])]
    separacao_df = pedidos_sem_hifen[pedidos_sem_hifen['Status'] == 'Pendente']
    
    return separacao_df, compras_df

# Modificações na guia de Separação/Expedição
def guia_separacao():
    st.title("Separação")
    
    separacao_df, _ = mover_pedidos(df)
    separacao_df = separacao_df[(separacao_df['Status'] == 'Pendente') | (~separacao_df['Status'].str.contains('-'))]
    separacao_df = separacao_df.dropna(axis=1, how='all')
    # Adicionando a lógica para verificar se o pedido está atrasado
    today = datetime.now()

    # Verificar se a coluna 'Dt. pedido' existe antes de proceder
    if 'Dt.pedido' in separacao_df.columns:
        # Convertendo a coluna 'Dt. pedido' para datetime
        separacao_df['Dt.pedido'] = pd.to_datetime(separacao_df['Dt.pedido'], errors='coerce')
        
        # Verificando se a data do pedido é mais antiga que 2 dias a partir de hoje
        separacao_df['Atrasado'] = (today - separacao_df['Dt.pedido']) > timedelta(days=2)
        
        # Atualizando o status para 'Atrasado' se o pedido estiver atrasado e ainda 'Pendente'
        separacao_df.loc[(separacao_df['Atrasado']) & (separacao_df['Status'] == 'Pendente'), 'Status'] = 'Atrasado'
    else:
        st.warning("A coluna 'Dt.pedido' não foi encontrada no DataFrame.")

    pendentes_sep, atrasados_sep = calcular_pendentes_atrasados(separacao_df)
    if pendentes_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_sep} produto(s) pendente(s) no total!</div>', unsafe_allow_html=True)
    if atrasados_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_sep} produto(s) atrasado(s) no total!</div>', unsafe_allow_html=True)

    # Filtros
    cliente_selecionado = st.selectbox("Selecione o Cliente", ["Todos os Clientes"] + separacao_df['Fantasia'].unique().tolist())
    separacao_df = separacao_df if cliente_selecionado == "Todos os Clientes" else separacao_df[separacao_df['Fantasia'] == cliente_selecionado]

    pedido_filtro = st.text_input("Filtrar por número de pedido:")
    status_filtro = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Atrasado"])
    
    if pedido_filtro:
        separacao_df = separacao_df[separacao_df['Ped. Cliente'].astype(str).str.contains(pedido_filtro)]
    
    if status_filtro != "Todos":
        separacao_df = separacao_df[separacao_df['Status'] == status_filtro]

    # Exibir número de linhas após a filtragem
    total_linhas_depois = separacao_df.shape[0]
    st.write(f"Número de linhas: {total_linhas_depois}")

    # Exibe o DataFrame filtrado e o total específico
    st.dataframe(separacao_df, use_container_width=True)

# Modificações na guia de Compras
def guia_compras():
    st.title("Compras")
    
    # DataFrame geral para calcular pendentes e atrasados (antes dos filtros)
    _, compras_df_geral = mover_pedidos(df)
    compras_df_geral = compras_df_geral[(compras_df_geral['Status'] == 'Pendente') | (compras_df_geral['Status'].str.contains('-'))]
    
    # Calcular o total geral de pendentes e atrasados
    pendentes_compras_geral, atrasados_compras_geral = calcular_pendentes_atrasados(compras_df_geral)
    
    # Notificações baseadas no total geral
    if pendentes_compras_geral > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_compras_geral} produto(s) pendente(s) no total!</div>', unsafe_allow_html=True)
    if atrasados_compras_geral > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_compras_geral} produto(s) atrasado(s) no total!</div>', unsafe_allow_html=True)
    
    # Filtragem para exibição
    _, compras_df = mover_pedidos(df)
    compras_df = compras_df[(compras_df['Status'] == 'Pendente') | (compras_df['Status'].str.contains('-'))]
    compras_df = compras_df.dropna(axis=1, how='all')

    # Aplicação dos filtros ao DataFrame
    cliente_selecionado = st.selectbox("Selecione o Cliente", ["Todos os Clientes"] + compras_df['Fantasia'].unique().tolist())
    compras_df = compras_df if cliente_selecionado == "Todos os Clientes" else compras_df[compras_df['Fantasia'] == cliente_selecionado]

    pedido_filtro = st.text_input("Filtrar por número de pedido:")
    status_filtro = st.selectbox("Filtrar por Status", ["Todos", "Pendente", "Atrasado"])
    
    if pedido_filtro:
        compras_df = compras_df[compras_df['Ped. Cliente'].astype(str).str.contains(pedido_filtro)]
    
    if status_filtro != "Todos":
        compras_df = compras_df[compras_df['Status'] == status_filtro]

    total_linhas_depois = compras_df.shape[0]
    st.write(f"Número de linhas: {total_linhas_depois}")

    # Exibe o DataFrame filtrado e o total específico
    st.dataframe(compras_df, use_container_width=True)
    
def guia_embalagem():
    st.title("Embalagem")
    
# Interface por perfil - mantém a estrutura atual
if perfil == "Administrador":
    aba = st.sidebar.radio("Escolha uma aba", ["Dashboard", "Carteira", "Notificações"])
    if aba == "Dashboard":
        guia_dashboard()
    elif aba == "Carteira":
        guia_carteira()
    elif aba == "Notificações":
        guia_notificacoes()
    # Notificações de pendência e atraso
    if pendente > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendente} produto(s) pendente(s)!</div>', unsafe_allow_html=True)
    if atrasado > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasado} produto(s) atrasado(s)!</div>', unsafe_allow_html=True)

else:
    guia_notificacoes()
    if perfil == "Separação":
        guia_separacao()
    elif perfil == "Compras":
        guia_compras()

