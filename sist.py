import streamlit as st
import pandas as pd
from datetime import datetime
import locale
import plotly.express as px
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

# Configuração inicial do locale e da página
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')  # ou 'en_US.UTF-8' como fallback

# Função para converter PNG em Base64
def image_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Função para tela de carregamento
def show_loading_screen():
    logo = Image.open("planilha/logo.png")
    logo_base64 = image_to_base64(logo)
    st.markdown(
        f"""
        <style>
       .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
            margin: 0;
            padding: 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        </style>
        <div class="loading">
            <img src="data:image/png;base64,{logo_base64}" width="800" style="margin-top: 5px;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("""
        <style>
       .blinking {{
            animation: blinker 1s linear infinite;
            color: yellow;
            font-weight: bold;
        }}
        @keyframes blinker {{
            50% {{
                opacity: 0;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

# Função para carregar dados
@st.cache_data
def carregar_dados(caminho):
    df = pd.read_excel(caminho)
    df['Nr.pedido'] = df['Nr.pedido'].astype(str)
    return df

# Função para criar perfis
def criar_perfis(df):
    separacao = df[~df['Nr.pedido'].str.contains('-')]
    perfil2 = df[df['Nr.pedido'].str.contains('-')]
    perfil3 = perfil2[perfil2['Origem'].isna() | (perfil2['Origem'] == '')]
    perfil2 = perfil2[~perfil2.index.isin(perfil3.index)]
    return separacao, perfil2, perfil3

# Função para definir data e status
def definir_data_e_status(dataframe):
    dataframe['Dt.fat.'] = pd.to_datetime(dataframe['Dt.fat.'], errors='coerce')
    dataframe['Prev.entrega'] = pd.to_datetime(dataframe['Prev.entrega'], errors='coerce')
    dataframe['Status'] = 'Pendente'
    dataframe.loc[dataframe['Dt.fat.'].notna(), 'Status'] = 'Entregue'
    dataframe.loc[(dataframe['Prev.entrega'] < datetime.now()) & (dataframe['Dt.fat.'].isna()), 'Status'] = 'Atrasado'
    return dataframe

# Função para filtrar pedidos
def filtrar_pedidos(df):
    df = df[df['Ped. Cliente'] != 'TUMELERO']
    df = df[df['Ped. Cliente'] != 'ESTOQUE FOX']
    df = df[df['Nr.pedido'] != 'nan']
    df = df[df['Status'] != 'Entregue']
    return df

# Função para calcular pendentes e atrasados
def calcular_pendentes_atrasados(df):
    pendentes = (df['Status'] == 'Pendente').sum()
    atrasados = (df['Status'] == 'Atrasado').sum()
    return pendentes, atrasados

# Função para aplicar filtros
def aplicar_filtros(df, fantasia_filter, ped_cliente_filter, status_filter):
    df_filtrado = df.copy()
    if fantasia_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Status'] == status_filter]
    return df_filtrado

# Função para exibir dataframe
def exibir_dataframe(df_filtrado, valor_total):
    st.write("Total de Itens:", len(df_filtrado))
    st.dataframe(df_filtrado)
    valor_total_formatado = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total_formatado}</span>", unsafe_allow_html=True)

# Função para exibir notificações
def exibir_notificacoes(pendentes, atrasados, tipo):
    if pendentes > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados} produtos atrasados!</div>', unsafe_allow_html=True)
    if tipo == "Compras":
        st.sidebar.markdown(f'<div class="blinking-orange">URGENTE: Você precisa gerar OE de {atrasados} produtos!</div>', unsafe_allow_html=True)

# Função para guia de carteira
def guia_carteira(df_carteira):
    st.title("Carteira")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Selecione o Cliente", options=["Todos"] + list(df_carteira['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(df_carteira['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    df_carteira_filtrado = aplicar_filtros(df_carteira, fantasia_filter, ped_cliente_filter, status_filter)
    
    if not df_carteira_filtrado.empty:
        valor_total = df_carteira_filtrado['Valor Total'].sum()
        exibir_dataframe(df_carteira_filtrado, valor_total)
    else:
        st.warning("Nenhum item encontrado com os filtros aplicados.")

# Função para guia de dashboard
def guia_dashboard(df_carteira):
    st.markdown("<h3>📊 Estatísticas Gerais</h3>", unsafe_allow_html=True)
    
    produto_frequencia = df_carteira['Produto'].value_counts().reset_index()
    produto_frequencia.columns = ['Produto', 'Frequência']
    
    fig_barras_produtos = px.bar(
        produto_frequencia, 
        x='Produto',  
        y='Frequência', 
        title='Total por Produto',
        labels={'Produto': 'Produto', 'Frequência': 'Quantidade'},
        color='Frequência', 
        color_continuous_scale='Viridis',
    )
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total de Pedidos", total_pedidos)
    with col2:
        st.metric("Total de Itens", len(df))
    with col3:
        st.metric("Total de Pendências", pendente)
    with col4:
        st.metric("Total por Referência", modelos_unicos)
    with col5:
        st.metric("Total de Cartelas", "{:.0f}".format(total_itensct))

    st.markdown("<h3>🏢 Setores</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    pendencia_separacao = len(separacao[separacao['Status'] == 'Pendente'])
    pendencia_compras = len(compras[compras['Status'] == 'Pendente'])
    pendencia_embalagem = len(embalagem[embalagem['Status'] == 'Pendente'])
    pendencia_expedicao = len(expedicao[expedicao['Status'] == 'Pendente'])
    
    with col1:
        st.metric("Separação", pendencia_separacao)
    with col2:
        st.metric("Compras", pendencia_compras)
    with col3:
        st.metric("Embalagem", pendencia_embalagem)
    with col4:
        st.metric("Expedição", pendencia_expedicao)
    
    col_graph1, col_graph2 = st.columns(2)
    with col_graph1:
        status_counts = df_carteira['Status'].value_counts()
        fig_pizza = px.pie(values=status_counts.values, names=status_counts.index, title="Pedidos por Status (%)")
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col_graph2:
        valor_total_por_status = df_carteira.groupby('Status')['Valor Total'].sum().reset_index()
        fig_barras = px.bar(valor_total_por_status, x='Status', y='Valor Total', title="Valor Total por Status")
        st.plotly_chart(fig_barras, use_container_width=True)
    
    st.plotly_chart(fig_barras_produtos, use_container_width=True)

# Função para guia de separação
def guia_separacao(perfil1_filtrado):
    st.title("Separação")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(perfil1_filtrado['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(perfil1_filtrado['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    perfil1_filtrado = aplicar_filtros(perfil1_filtrado, fantasia_filter, ped_cliente_filter, status_filter)
    
    valor_total = perfil1_filtrado['Valor Total'].sum()
    exibir_dataframe(perfil1_filtrado, valor_total)
    
    pendentes_sep, atrasados_sep = calcular_pendentes_atrasados(perfil1_filtrado)
    exibir_notificacoes(pendentes_sep, atrasados_sep, "Separação")

# Função para guia de compras
def guia_compras(compras_filtrado):
    st.title("Compras")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(compras_filtrado['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(compras_filtrado['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    compras_filtrado = aplicar_filtros(compras_filtrado, fantasia_filter, ped_cliente_filter, status_filter)
    
    valor_total = compras_filtrado['Valor Total'].sum()
    exibir_dataframe(compras_filtrado, valor_total)
    
    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3)
    exibir_notificacoes(pendentes_oee, atrasados_oee, "Compras")

# Função para guia de embalagem
def guia_embalagem(embalagem_filtrado):
    st.title("Embalagem")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(embalagem_filtrado['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(embalagem_filtrado['Ped. Cliente'].unique()))
    
    with col_filter3:
            status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    embalagem_filtrado = aplicar_filtros(embalagem_filtrado, fantasia_filter, ped_cliente_filter, status_filter)
    
    valor_total = embalagem_filtrado['Valor Total'].sum()
    exibir_dataframe(embalagem_filtrado, valor_total)
    
    pendentes_emb, atrasados_emb = calcular_pendentes_atrasados(embalagem_filtrado)
    exibir_notificacoes(pendentes_emb, atrasados_emb, "Embalagem")

# Função para guia de expedição
def guia_expedicao(expedicao_filtrado):
    st.title("Expedição")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(expedicao_filtrado['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(expedicao_filtrado['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    expedicao_filtrado = aplicar_filtros(expedicao_filtrado, fantasia_filter, ped_cliente_filter, status_filter)
    
    valor_total = expedicao_filtrado['Valor Total'].sum()
    exibir_dataframe(expedicao_filtrado, valor_total)
    
    pendentes_exp, atrasados_exp = calcular_pendentes_atrasados(expedicao_filtrado)
    exibir_notificacoes(pendentes_exp, atrasados_exp, "Expedição")

# Função para guia de Não gerado OE
def guia_OE(perfil3_filtrado):
    st.title("Não gerado OE")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(perfil3_filtrado['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(perfil3_filtrado['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    perfil3_filtrado = aplicar_filtros(perfil3_filtrado, fantasia_filter, ped_cliente_filter, status_filter)
    
    valor_total = perfil3_filtrado['Valor Total'].sum()
    exibir_dataframe(perfil3_filtrado, valor_total)
    
    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3_filtrado)
    exibir_notificacoes(pendentes_oee, atrasados_oee, "Compras")

# Controla se o sistema foi inicializado
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

# Se o sistema não foi inicializado, exibe a tela de carregamento
if not st.session_state.initialized:
    # Cria um espaço reservado para a tela de carregamento
    loading_placeholder = st.empty()
    with loading_placeholder:
        show_loading_screen()
    
    # Simula o tempo de carregamento
    time.sleep(1)  # Simule o carregamento de dados
    
    # Marca o sistema como inicializado
    st.session_state.initialized = True
    
    # Limpa a tela de carregamento
    loading_placeholder.empty()  # Remove a tela de carregamento

# Estilos personalizados
st.markdown(
    """
    <style>
      .main {
            background-color: rgba(0, 0, 0, 0.2);
        }
      .sidebar.sidebar-content {
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
      .blinking-orange {
            animation: blinker 1s linear infinite;
            color: orange;
            background-color: rgba(255, 165, 0, 0.1);
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

# Carregar o arquivo Excel
df = carregar_dados('planilha/controledosistema.xlsx')

# Criar DataFrames para cada perfil
separacao, perfil2, perfil3 = criar_perfis(df)

# Definir as colunas a serem filtradas
colunas_desejadas = [
    'Nr.pedido', 'Ped. Cliente', 'Dt.pedido', 'Dt.fat.', 
    'Prev.entrega', 'Fantasia', 'Produto', 'Modelo', 
    'Qtd.', 'Valor Unit.', 'Valor Total', 'Qtd.a produzir', 
    'Qtd. Produzida', 'Qtd.a liberar'
]

# Filtrar colunas para cada perfil
separacao = separacao[colunas_desejadas]
perfil2 = perfil2[colunas_desejadas]
compras = perfil2[(perfil2['Qtd. Produzida'] == 0) & (perfil2['Qtd.a liberar'] == 0)][colunas_desejadas]
embalagem = perfil2[(perfil2['Qtd. Produzida'] == 0) & (perfil2['Qtd.a liberar'] > 0)][colunas_desejadas]
expedicao = perfil2[(perfil2['Qtd. Produzida'] > 0) & (perfil2['Qtd.a liberar'] > 0)][colunas_desejadas]
perfil3 = perfil3[colunas_desejadas]
carteira = df[colunas_desejadas]

# Definir data e status para cada perfil
separacao = definir_data_e_status(separacao)
perfil2 = definir_data_e_status(perfil2)
compras = definir_data_e_status(compras)
embalagem = definir_data_e_status(embalagem)
expedicao = definir_data_e_status(expedicao)
perfil3 = definir_data_e_status(perfil3)
carteira = definir_data_e_status(carteira)

# Remover linhas com "TUMELERO" e "ESTOQUE FOX" da coluna 'Ped. Cliente'
separacao = filtrar_pedidos(separacao)
perfil2 = filtrar_pedidos(perfil2)
compras = filtrar_pedidos(compras)
embalagem = filtrar_pedidos(embalagem)
expedicao = filtrar_pedidos(expedicao)
perfil3 = filtrar_pedidos(perfil3)
carteira = filtrar_pedidos(carteira)

# Estatísticas Gerais para o Dashboard
total_pedidos = carteira['Ped. Cliente'].nunique()
pendente = len(carteira[carteira['Status'] == 'Pendente'])
modelos_unicos = carteira['Modelo'].nunique()
total_itensct = carteira['Qtd.'].sum()

# Configurar a barra lateral com opção de perfil
perfil_opcao = st.sidebar.selectbox("Selecione o perfil", 
                     ("Administrador ⚙️", "Separação 💻", "Compras 🛒", "Embalagem 📦", "Expedição 🚚", "Não gerado OE ❌"))

# Estrutura da página Administrador
if perfil_opcao == "Administrador ⚙️":
    admin_opcao = st.sidebar.radio("Opções do Administrador", ("Dashboard", "Carteira", "Notificações"))
    
    if admin_opcao == "Dashboard":
        guia_dashboard(carteira)
    elif admin_opcao == "Carteira":
        guia_carteira(carteira)
    elif admin_opcao == "Notificações":
        st.write("Conteúdo das Notificações")  # Placeholder para o conteúdo das Notificações

# Estrutura da página Separação
elif perfil_opcao == "Separação 💻":
    guia_separacao(separacao)

# Estrutura da página Compras
elif perfil_opcao == "Compras 🛒":
    guia_compras(compras)

# Estrutura da página Embalagem
elif perfil_opcao == "Embalagem 📦":
    guia_embalagem(embalagem)

# Estrutura da página Expedição
elif perfil_opcao == "Expedição 🚚":
    guia_expedicao(expedicao)

# Estrutura da página Não gerado OE
elif perfil_opcao == "Não gerado OE ❌":
    guia_OE(perfil3)