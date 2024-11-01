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

# ---------------------------------------#
# **Função para converter PNG em Base64**#
# ---------------------------------------#

def image_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# ------------------------------------#
# **Função para tela de carregamento**#
# ------------------------------------#

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

    # Adicionando o efeito de piscar para as notificações
    st.markdown("""
        <style>
       .blinking {{
            animation: blinker 1s linear infinite!important;
            color: yellow!important;
            font-weight: bold!important;
        }}
        @keyframes blinker {{
            50% {{
                opacity: 0;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

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
df = pd.read_excel('planilha/pp.xlsx')

# Garantir que a coluna 'Nr.pedido' seja do tipo string
df['Nr.pedido'] = df['Nr.pedido'].astype(str)

# Criar DataFrames para cada perfil
separacao = df[~df['Nr.pedido'].str.contains('-')]  # Sem '-'
perfil2 = df[df['Nr.pedido'].str.contains('-')]   # Com '-'

# Criar perfil3 com linhas do perfil2 que não possuem nada na coluna 'Origem'
perfil3 = perfil2[perfil2['Origem'].isna() | (perfil2['Origem'] == '')]  # 'Origem' vazia ou NaN

# Remover do perfil2 as linhas que estão no perfil3
perfil2 = perfil2[~perfil2.index.isin(perfil3.index)]

def definir_data_e_status(dataframe):

    # Converter colunas para datetime
    dataframe['Dt.fat.'] = pd.to_datetime(dataframe['Dt.fat.'], errors='coerce')
    dataframe['Prev.entrega'] = pd.to_datetime(dataframe['Prev.entrega'], errors='coerce')

    # Definir Status
    dataframe['Status'] = 'Pendente'
    dataframe.loc[dataframe['Dt.fat.'].notna(), 'Status'] = 'Entregue'
    dataframe.loc[(dataframe['Prev.entrega'] < datetime.now()) & (dataframe['Dt.fat.'].isna()), 'Status'] = 'Atrasado'
    
    return dataframe

carteira = df

df_filtrado = df[(df['Nr.pedido']!= 'nan') & (df['Nr.pedido']!= '')]

def is_atrasado_pedido(df):
    return (df['Dt.pedido'] + pd.Timedelta(days=1)) < datetime.now()

# Definir as colunas a serem filtradas
colunas_desejadas = [
    'Nr.pedido', 'Ped. Cliente', 'Dt.pedido', 'Dt.fat.', 
    'Prev.entrega', 'Fantasia', 'Produto', 'Modelo', 
    'Qtd.', 'Valor Unit.', 'Valor Total', 'Qtd.a produzir', 
    'Qtd. Produzida', 'Qtd.a liberar'
]

#********************************CAMPO DE FILTROS DOS DATAFRAMES************************************

# Filtrar colunas para cada perfil
separacao = separacao[colunas_desejadas]
perfil2 = perfil2[colunas_desejadas]
compras = perfil2[(perfil2['Qtd. Produzida'] == 0) & (perfil2['Qtd.a liberar'] == 0)][colunas_desejadas]
embalagem = perfil2[(perfil2['Qtd. Produzida'] == 0) & (perfil2['Qtd.a liberar'] > 0)][colunas_desejadas]
expedicao = perfil2[(perfil2['Qtd. Produzida'] > 0) & (perfil2['Qtd.a liberar'] > 0)][colunas_desejadas]
perfil3 = perfil3[colunas_desejadas]
carteira = carteira[colunas_desejadas]

separacao = separacao.dropna(subset=['Ped. Cliente'])
perfil2 = perfil2.dropna(subset=['Ped. Cliente'])
compras = compras.dropna(subset=['Ped. Cliente'])
embalagem = embalagem.dropna(subset=['Ped. Cliente'])
expedicao = expedicao.dropna(subset=['Ped. Cliente'])
perfil3 = perfil3.dropna(subset=['Ped. Cliente'])
carteira = carteira.dropna(subset=['Ped. Cliente'])

# Chame a função para cada DataFrame
separacao = definir_data_e_status(separacao)
perfil2 = definir_data_e_status(perfil2)
compras = definir_data_e_status(compras)
embalagem = definir_data_e_status(embalagem)
expedicao = definir_data_e_status(expedicao)
perfil3 = definir_data_e_status(perfil3)
carteira = definir_data_e_status(carteira)

# Ocultar linhas com "TUMELERO" na coluna Ped.Cliente
separacao = separacao[separacao['Ped. Cliente']!= 'TUMELERO']
compras = compras[compras['Ped. Cliente']!= 'TUMELERO']
embalagem = embalagem[embalagem['Ped. Cliente']!= 'TUMELERO']
expedicao = expedicao[expedicao['Ped. Cliente']!= 'TUMELERO']
perfil3 = perfil3[perfil3['Ped. Cliente']!= 'TUMELERO']
carteira = carteira[carteira['Ped. Cliente']!= 'TUMELERO']

separacao = separacao[separacao['Ped. Cliente']!= 'ESTOQUE FOX']
compras = compras[compras['Ped. Cliente']!= 'ESTOQUE FOX']
embalagem = embalagem[embalagem['Ped. Cliente']!= 'ESTOQUE FOX']
expedicao = expedicao[expedicao['Ped. Cliente']!= 'ESTOQUE FOX']
perfil3 = perfil3[perfil3['Ped. Cliente']!= 'ESTOQUE FOX']
carteira = carteira[carteira['Ped. Cliente']!= 'ESTOQUE FOX']

separacao = separacao[separacao['Status']!= 'Entregue']
compras = compras[compras['Status']!= 'Entregue']
embalagem = embalagem[embalagem['Status']!= 'Entregue']
expedicao = expedicao[expedicao['Status']!= 'Entregue']
perfil3 = perfil3[perfil3['Status']!= 'Entregue']

# Estatísticas Gerais para o Dashboard
# Estatísticas Gerais para o Dashboard
total_pedidos = carteira['Ped. Cliente'].nunique()  # Pedidos únicos por pedido e cliente
pendente = len(carteira[carteira['Status'] == 'Pendente'])
modelos_unicos = carteira['Modelo'].nunique()    # Total de modelos únicos
total_itensct = carteira['Qtd.'].sum()

#********************************INICIO DAS FUNÇÕES POR GUIAS************************************

def guia_carteira():
    st.title("Carteira")
    
    df_carteira = carteira
    df_carteira = definir_data_e_status(df_carteira)  # <--- Adicione essa linha

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Selecione o Cliente", options=["Todos"] + list(df_carteira['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(df_carteira['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    # **Aplicar Filtros**
    df_carteira_filtrado = df_carteira.copy()  # Evita modificar o original
    if fantasia_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Status'] == status_filter]
    
    # **Exibir DataFrame Filtrado (se aplicável)**
    if not df_carteira_filtrado.empty:
        st.write("Total de Itens:", len(df_carteira_filtrado))
        st.dataframe(df_carteira_filtrado)
        valor_total = f"R$ {df_carteira_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)
    else:
        st.warning("Nenhum item encontrado com os filtros aplicados.")

def guia_dashboard():
    # Cabeçalho para Estatísticas Gerais
    st.markdown("<h3>Estatísticas Gerais <small style='font-size: 0.4em;'>(mês atual)</small></h3>", unsafe_allow_html=True)
    
      # **Concatenar todos os DataFrames (para uso nos gráficos)**
    df_carteira = carteira

    produto_frequencia = df_carteira['Produto'].value_counts().reset_index()
    produto_frequencia.columns = ['Produto', 'Frequência']

    # Criar um DataFrame com informações adicionais para o hover
    produto_info = df_carteira[['Produto', 'Modelo']].drop_duplicates()  # Remove duplicatas

    # Merge para incluir informações adicionais no gráfico
    produto_frequencia = produto_frequencia.merge(produto_info, on='Produto', how='left')

    # Gráfico de Barras
    fig_barras_produtos = px.bar(
        produto_frequencia, 
        x='Produto',  
        y='Frequência', 
        title='Total por Produto',
        labels={'Produto': 'Produto', 'Frequência': 'Quantidade'},
        color='Frequência', 
        color_continuous_scale='Viridis',
        hover_data={'Produto': True, 'Frequência': True, 'Modelo': True}  # Incluir o Modelo no hover
    )

    # Customizações adicionais
    fig_barras_produtos.update_layout(
        xaxis_title='Código do Produto',
        yaxis_title='Número de Pedidos',
        xaxis_tickangle=-45,  
        bargap=0.2,  
        xaxis=dict(
            range=[0, 30],  
            fixedrange=False  
        )
    )

    # Coloca as estatísticas na horizontal no topo da tela
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
    
    # Layout para os gráficos (lado a lado ou um em cima do outro, escolha um)
    # **Lado a Lado**
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # **Gráfico de Pizza: Pedidos por Status (%)**
        status_counts = df_carteira['Status'].value_counts()
        fig_pizza = px.pie(values=status_counts.values, names=status_counts.index, title="Pedidos por Status (%)")
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col_graph2:
        # **Gráfico de Barras: Valor Total por Status**
        valor_total_por_status = df_carteira.groupby('Status')['Valor Total'].sum().reset_index()
        fig_barras = px.bar(valor_total_por_status, x='Status', y='Valor Total', title="Valor Total por Status")
        st.plotly_chart(fig_barras, use_container_width=True)

    # Espaçamento vertical entre as linhas de gráficos
    st.write(" ")

     # Segunda linha de gráficos que ocupa toda a largura
    st.plotly_chart(fig_barras_produtos, use_container_width=True)


# Configurar a barra lateral com opção de Administrador
perfil_opcao = st.sidebar.selectbox("Selecione o perfil", 
                     ("Administrador ⚙️", "Separação 💻", "Compras 🛒", "Embalagem 📦", "Expedição 🚚", "Não gerado OE ❌"))

# Estrutura da página Administrador
if perfil_opcao == "Administrador ⚙️":
    admin_opcao = st.sidebar.radio("Opções do Administrador", ("Dashboard", "Carteira", "Notificações"))
    
    if admin_opcao == "Dashboard":
        guia_dashboard()  # Chama a função do Dashboard
    elif admin_opcao == "Carteira":
        guia_carteira()  # Placeholder para o conteúdo da Carteira
    elif admin_opcao == "Notificações":
        st.write("Conteúdo das Notificações")  # Placeholder para o conteúdo das Notificações
        
def calcular_pendentes_atrasados(df):
    pendentes = (df['Status'] == 'Pendente').sum()
    atrasados = (df['Status'] == 'Atrasado').sum()
    return pendentes, atrasados

def guia_separacao():
    st.title("Separação")
    
    perfil1_filtrado = separacao.copy()  
    perfil1_filtrado = definir_data_e_status(perfil1_filtrado)  # <--- Adicione essa linha

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(separacao['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(separacao['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    # **Aplicar Filtros ao separacao**
    perfil1_filtrado = separacao.copy()  # Evita modificar o original
    if fantasia_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Status'] == status_filter]
    
    # **Exibir DataFrame Filtrado**
    st.write("Total de Itens:", len(perfil1_filtrado))
    st.dataframe(perfil1_filtrado)

    valor_total = f"R$ {separacao['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_sep, atrasados_sep_prev_entrega = calcular_pendentes_atrasados(separacao)  # Notificação de atrasado com base na Prev.Entrega
    atrasados_sep_pedido = separacao[is_atrasado_pedido(separacao)].shape[0]  # Nova lógica de atrasado com base na Dt.Pedido + 1 dia
    
    if pendentes_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_sep} produtos pendentes no total!</div>', unsafe_allow_html=True)
    if atrasados_sep_prev_entrega > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_sep_prev_entrega} produtos atrasados no total! (por data)</div>', unsafe_allow_html=True)
    if atrasados_sep_pedido > 0:
        st.sidebar.markdown(f'<div class="blinking-red">URGENTE: Você precisa separar ou emitir OP de {atrasados_sep_pedido} produtos! </div>', unsafe_allow_html=True)


# Chamada da função guia_separacao
if perfil_opcao == "Separação 💻":
    guia_separacao()

def guia_compras():
    st.title("Compras")
    
    compras_filtrado = compras.copy()  
    compras_filtrado = definir_data_e_status(compras_filtrado)

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(compras['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(compras['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    # **Aplicar Filtros ao Compras**
    compras_filtrado = compras.copy()  # Evita modificar o original
    if fantasia_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Status'] == status_filter]
    
    # **Exibir DataFrame Filtrado**
    st.write("Total de Itens:", len(compras_filtrado))
    st.dataframe(compras_filtrado)

    valor_total = f"R$ {compras['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3)
    if pendentes_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_oee} produtos pendentes no total!</div>', unsafe_allow_html=True)
    if atrasados_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_oee} produtos atrasados no total!</div>', unsafe_allow_html=True)

if perfil_opcao == "Compras 🛒":
    guia_compras()

def guia_embalagem():
    st.title("Embalagem")
    
    embalagem_filtrado = embalagem.copy()  
    embalagem_filtrado = definir_data_e_status(embalagem_filtrado)  # <--- Adicione essa linha

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(embalagem['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(embalagem['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    # **Aplicar Filtros ao Embalagem**
    embalagem_filtrado = embalagem.copy()  # Evita modificar o original
    if fantasia_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Status'] == status_filter]
    
    # **Exibir DataFrame Filtrado**
    st.write("Total de Itens:", len(embalagem_filtrado))
    st.dataframe(embalagem_filtrado)

    valor_total = f"R$ {embalagem['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_emb, atrasados_emb_prev_entrega = calcular_pendentes_atrasados(embalagem)  # Notificação de atrasado com base na Prev.Entrega
    atrasados_emb_pedido = embalagem[is_atrasado_pedido(embalagem)].shape[0]  # Nova lógica de atrasado com base na Dt.Pedido + 1 dia
    
    if pendentes_emb > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_emb} produtos pendentes no total!</div>', unsafe_allow_html=True)
    if atrasados_emb_prev_entrega > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_emb_prev_entrega} produtos atrasados no total! (por data)</div>', unsafe_allow_html=True)
    if atrasados_emb_pedido > 0:
        st.sidebar.markdown(f'<div class="blinking-red">URGENTE: Você precisa embalar {atrasados_emb_pedido} produtos! </div>', unsafe_allow_html=True)


if perfil_opcao == "Embalagem 📦":
    guia_embalagem()

def guia_expedicao():
    st.title("Expedição")
    
    expedicao_filtrado = expedicao.copy()  
    expedicao_filtrado = definir_data_e_status(expedicao_filtrado)  # <--- Adicione essa linha

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Fantasia", options=["Todos"] + list(expedicao['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Ped. Cliente", options=["Todos"] + list(expedicao['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    # **Aplicar Filtros ao Expedição**
    expedicao_filtrado = expedicao.copy()  # Evita modificar o original
    if fantasia_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Status'] == status_filter]
    
    # **Exibir DataFrame Filtrado**
    st.write("Total de Itens:", len(expedicao_filtrado))
    st.dataframe(expedicao_filtrado)

    valor_total = f"R$ {expedicao['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_exp, atrasados_exp = calcular_pendentes_atrasados(expedicao)
    if pendentes_exp > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_exp} produtos pendentes no total!</div>', unsafe_allow_html=True)
    if atrasados_exp > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_exp} produtos atrasados no total!</div>', unsafe_allow_html=True)

if perfil_opcao == "Expedição 🚚":
    guia_expedicao()

def guia_OE():
    st.title("Não gerado OE")

    # **Exibir DataFrame**
    st.write("Total de Itens:", len(perfil3))
    st.dataframe(perfil3)

    valor_total = f"R$ {perfil3['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)
	
    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3)
    if pendentes_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_oee} produtos pendentes no total!</div>', unsafe_allow_html=True)
    if atrasados_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_oee} produtos atrasados no total!</div>', unsafe_allow_html=True)

if perfil_opcao == "Não gerado OE ❌":
    guia_OE()
