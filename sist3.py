import streamlit as st
import pandas as pd
from datetime import datetime
import locale
import plotly.express as px
import time
from PIL import Image
import base64
from io import BytesIO

st.set_page_config(
    page_title="Sistema de Controle",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')

def image_to_base64(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

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

if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    loading_placeholder = st.empty()
    with loading_placeholder:
        show_loading_screen()
    
    time.sleep(1)
    
    st.session_state.initialized = True
    
    loading_placeholder.empty()

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

@st.cache_data
def carregar_dados():
    df = pd.read_excel('planilha/controledosistema.xlsx')
    return df

df = carregar_dados()

# Carregar dados somente se ainda não estiverem no session_state
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# Usar st.session_state.dados ao invés de carregar dados repetidamente
dados = st.session_state.dados

df['Nr.pedido'] = df['Nr.pedido'].astype(str)

separacao = df[~df['Nr.pedido'].str.contains('-')]
perfil2 = df[df['Nr.pedido'].str.contains('-')]

perfil3 = perfil2[perfil2['Origem'].isna() | (perfil2['Origem'] == '')]

perfil2 = perfil2[~perfil2.index.isin(perfil3.index)]

def definir_data_e_status(dataframe):

    dataframe['Dt.fat.'] = pd.to_datetime(dataframe['Dt.fat.'], errors='coerce')
    dataframe['Prev.entrega'] = pd.to_datetime(dataframe['Prev.entrega'], errors='coerce')

    dataframe['Status'] = 'Pendente'
    dataframe.loc[dataframe['Dt.fat.'].notna(), 'Status'] = 'Entregue'
    dataframe.loc[(dataframe['Prev.entrega'] < datetime.now()) & (dataframe['Dt.fat.'].isna()), 'Status'] = 'Atrasado'
    
    return dataframe

carteira = df

def is_atrasado_pedido(df):
    return (df['Dt.pedido'] + pd.Timedelta(days=1)) < datetime.now()

colunas_desejadas = [
     'Setor', 'Ped. Cliente', 'Dt.pedido', 'Fantasia', 'Produto', 'Modelo', 
    'Qtd.', 'Valor Unit.', 'Valor Total', 'Qtd.a produzir', 
    'Qtd. Produzida', 'Qtd.a liberar','Prev.entrega','Dt.fat.' , 'Nr.pedido'
]

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

separacao = definir_data_e_status(separacao)
perfil2 = definir_data_e_status(perfil2)
compras = definir_data_e_status(compras)
embalagem = definir_data_e_status(embalagem)
expedicao = definir_data_e_status(expedicao)
perfil3 = definir_data_e_status(perfil3)
carteira = definir_data_e_status(carteira)

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

separacao = separacao[separacao['Nr.pedido']!= 'nan']
perfil2 = perfil2[perfil2['Nr.pedido']!= 'nan']
compras = compras[compras['Nr.pedido']!= 'nan']
embalagem = embalagem[embalagem['Nr.pedido']!= 'nan']
expedicao = expedicao[expedicao['Nr.pedido']!= 'nan']
perfil3 = perfil3[perfil3['Nr.pedido']!= 'nan']
carteira = carteira[carteira['Nr.pedido']!= 'nan']

separacao = separacao[separacao['Status']!= 'Entregue']
compras = compras[compras['Status']!= 'Entregue']
embalagem = embalagem[embalagem['Status']!= 'Entregue']
expedicao = expedicao[expedicao['Status']!= 'Entregue']
perfil3 = perfil3[perfil3['Status']!= 'Entregue']

total_pedidos = carteira['Ped. Cliente'].nunique()
pendente = len(carteira[carteira['Status'] == 'Pendente'])
modelos_unicos = carteira['Modelo'].nunique()
total_itensct = carteira['Qtd.'].sum()

def formatar_data(data):
    return data.strftime("%d/%m/%Y")

def guia_carteira():
    st.title("Carteira")
    
    df_carteira = carteira
    df_carteira = definir_data_e_status(df_carteira)

    col_filter1, col_filter2, col_filter3, col_filter4, col_date_filter1, col_date_filter2 = st.columns(6)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Selecione o Cliente", options=["Todos"] + list(df_carteira['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(df_carteira['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])
    
    with col_filter4:
        setor_filter = st.selectbox("Filtrar por Setor", options=["Todos"] + [s for s in df_carteira['Setor'].unique() if not pd.isnull(s) and s!= 'Entregue'])

    with col_date_filter1:
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2024-10-01')))
    
    with col_date_filter2:
        data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))

    df_carteira_filtrado = df_carteira.copy()
    if fantasia_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        df_carteira_filtrado = df_carteira_filtrado[df_carteira_filtrado['Status'] == status_filter]
    if setor_filter!= "Todos":
        df_carteira_filtrado= df_carteira_filtrado[df_carteira_filtrado['Setor'] == setor_filter] 
    df_carteira_filtrado = df_carteira_filtrado[(df_carteira_filtrado['Dt.pedido'] >= data_inicial_filter) & (df_carteira_filtrado['Dt.pedido'] <= data_final_filter)]
    
    if not df_carteira_filtrado.empty:
        st.write("Total de Itens:", len(df_carteira_filtrado))
        st.dataframe(df_carteira_filtrado)
        valor_total = f"R$ {df_carteira_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)
    else:
        st.warning("Nenhum item encontrado com os filtros aplicados.")  

def guia_dashboard():
    
    df_carteira = carteira

    col1, col2, col3, col4= st.columns([4,1,1,3])
    
    with col1:
        st.markdown("<h3>📊 Estatísticas Gerais <small style='font-size: 0.4em;'>atualizado dia 18/12 às 15:22</small></h3>", unsafe_allow_html=True)
    with col4:
        valor_total_entregues = df_carteira[df_carteira['Status'] == 'Entregue']['Valor Total'].sum()
        st.metric("Faturamento Total", 
                "R${:,.2f}".format(valor_total_entregues).replace(",", "X").replace(".", ",").replace("X", "."))

    produto_frequencia = df_carteira['Produto'].value_counts().reset_index()
    produto_frequencia.columns = ['Produto', 'Frequência']

    produto_info = df_carteira[['Produto', 'Modelo']].drop_duplicates()

    produto_frequencia = produto_frequencia.merge(produto_info, on='Produto', how='left')

    fig_barras_produtos = px.bar(
        produto_frequencia, 
        x='Produto',  
        y='Frequência', 
        title='Total por Produto',
        labels={'Produto': 'Produto', 'Frequência': 'Quantidade'},
        color='Frequência', 
        color_continuous_scale='Viridis',
        hover_data={'Produto': True, 'Frequência': True, 'Modelo': True}
    )
    
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

    atraso_separacao = len(separacao[separacao['Status'] == 'Atrasado'])
    atraso_compras = len(compras[compras['Status'] == 'Atrasado'])
    atraso_embalagem = len(embalagem[embalagem['Status'] == 'Atrasado'])
    atraso_expedicao = len(expedicao[expedicao['Status'] == 'Atrasado'])    
    
    total_separacao = len(separacao.index)
    total_compras = len(compras.index)
    total_embalagem = len(embalagem.index)
    total_expedicao = len(expedicao.index)

    with col1:
        st.metric("Separação", total_separacao)
        st.markdown(f"<span style='font-size: 0.8em; margin-top: -10px; display:inline-block;'>P {pendencia_separacao} | A {atraso_separacao}</span>", unsafe_allow_html=True)

    with col2:
        st.metric("Compras", total_compras)
        st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_compras} | A {atraso_compras}</span>", unsafe_allow_html=True)

    with col3:
        st.metric("Embalagem", total_embalagem)
        st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_embalagem} | A {atraso_embalagem}</span>", unsafe_allow_html=True)

    with col4:
        st.metric("Expedição", total_expedicao)
        st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_expedicao} | A {atraso_expedicao}</span>", unsafe_allow_html=True)

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

    
    st.write(" ")

    st.plotly_chart(fig_barras_produtos, use_container_width=True)


perfil_opcao = st.sidebar.selectbox("Selecione o perfil", 
                     ("Administrador ⚙️", "Separação 💻", "Compras 🛒", "Embalagem 📦", "Expedição 🚚", "Não gerado OE ❌"))

if perfil_opcao == "Administrador ⚙️":
    admin_opcao = st.sidebar.radio("Opções do Administrador", ("Dashboard", "Carteira", "Notificações"))
    
    if admin_opcao == "Dashboard":
        guia_dashboard()
    elif admin_opcao == "Carteira":
        guia_carteira()
    elif admin_opcao == "Notificações":
        st.write("Conteúdo das Notificações")
        
def calcular_pendentes_atrasados(df):
    pendentes = (df['Status'] == 'Pendente').sum()
    atrasados = (df['Status'] == 'Atrasado').sum()
    return pendentes, atrasados

def guia_separacao():
    st.title("Separação")
    
    perfil1_filtrado = separacao.copy()  
    perfil1_filtrado = definir_data_e_status(perfil1_filtrado)

    col_filter1, col_filter2, col_filter3, col_date_filter1, col_date_filter2 = st.columns(5)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(separacao['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(separacao['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])

    with col_date_filter1:
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2024-10-01')))
    
    with col_date_filter2:
        data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))

    perfil1_filtrado = separacao.copy()
    if fantasia_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        perfil1_filtrado = perfil1_filtrado[perfil1_filtrado['Status'] == status_filter]
    perfil1_filtrado = perfil1_filtrado[(perfil1_filtrado['Dt.pedido'] >= data_inicial_filter) & (perfil1_filtrado['Dt.pedido'] <= data_final_filter)]
    
    st.write("Total de Itens:", len(perfil1_filtrado))
    st.dataframe(perfil1_filtrado)

    valor_total = f"R$ {perfil1_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_sep, atrasados_sep_prev_entrega = calcular_pendentes_atrasados(separacao)
    atrasados_sep_pedido = separacao[is_atrasado_pedido(separacao)].shape[0]
    
    if pendentes_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_sep} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados_sep_prev_entrega > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_sep_prev_entrega} produtos atrasados!</div>', unsafe_allow_html=True)
    #if atrasados_sep_pedido > 0:
    #   st.sidebar.markdown(f'<div class="blinking-orange">URGENTE: Você precisa separar ou emitir OE de {atrasados_sep_pedido} produtos!</div>', unsafe_allow_html=True)

if perfil_opcao == "Separação 💻":
    guia_separacao()

def guia_compras():
    st.title("Compras")
    
    compras_filtrado = compras.copy()  
    compras_filtrado = definir_data_e_status(compras_filtrado)

    col_filter1, col_filter2, col_filter3, col_date_filter1, col_date_filter2 = st.columns(5)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(compras['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(compras['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])

    with col_date_filter1:
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2024-10-01')))
    
    with col_date_filter2:
        data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))
    
    compras_filtrado = compras.copy()
    if fantasia_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        compras_filtrado = compras_filtrado[compras_filtrado['Status'] == status_filter]
    
    st.write("Total de Itens:", len(compras_filtrado))
    st.dataframe(compras_filtrado)

    valor_total = f"R$ {compras_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3)
    if pendentes_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_oee} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_oee} produtos atrasados!</div>', unsafe_allow_html=True)

if perfil_opcao == "Compras 🛒":
    guia_compras()

def guia_embalagem():
    st.title("Embalagem")
    
    embalagem_filtrado = embalagem.copy()  
    embalagem_filtrado = definir_data_e_status(embalagem_filtrado)

    col_filter1, col_filter2, col_filter3, col_date_filter1, col_date_filter2 = st.columns(5)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(embalagem['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(embalagem['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])

    with col_date_filter1:
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2024-10-01')))
    
    with col_date_filter2:
        data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))
    
    embalagem_filtrado = embalagem.copy()
    if fantasia_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        embalagem_filtrado = embalagem_filtrado[embalagem_filtrado['Status'] == status_filter]
    
    st.write("Total de Itens:", len(embalagem_filtrado))
    st.dataframe(embalagem_filtrado)

    valor_total = f"R$ {embalagem_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_emb, atrasados_emb_prev_entrega = calcular_pendentes_atrasados(embalagem)
    atrasados_emb_pedido = embalagem[is_atrasado_pedido(embalagem)].shape[0] 
    
    if pendentes_emb > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_emb} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados_emb_prev_entrega > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_emb_prev_entrega} produtos atrasados!</div>', unsafe_allow_html=True)
    #if atrasados_emb_pedido > 0:
    #   st.sidebar.markdown(f'<div class="blinking-orange">URGENTE: Você precisa embalar {atrasados_emb_pedido} produtos! </div>', unsafe_allow_html=True)


if perfil_opcao == "Embalagem 📦":
    guia_embalagem()

def guia_expedicao():
    st.title("Expedição")
    
    expedicao_filtrado = expedicao.copy()  
    expedicao_filtrado = definir_data_e_status(expedicao_filtrado) 

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    col_filter1, col_filter2, col_filter3, col_date_filter1, col_date_filter2 = st.columns(5)
    
    with col_filter1:
        fantasia_filter = st.selectbox("Filtrar por Cliente", options=["Todos"] + list(expedicao['Fantasia'].unique()))
    
    with col_filter2:
        ped_cliente_filter = st.selectbox("Filtrar por Pedido", options=["Todos"] + list(expedicao['Ped. Cliente'].unique()))
    
    with col_filter3:
        status_filter = st.selectbox("Filtrar por Status", options=["Todos", "Entregue", "Pendente", "Atrasado"])

    with col_date_filter1:
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2024-10-01')))
    
    with col_date_filter2:
        data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))

    expedicao_filtrado = expedicao.copy() 
    if fantasia_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Fantasia'] == fantasia_filter]
    if ped_cliente_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Ped. Cliente'] == ped_cliente_filter]
    if status_filter!= "Todos":
        expedicao_filtrado = expedicao_filtrado[expedicao_filtrado['Status'] == status_filter]

    st.write("Total de Itens:", len(expedicao_filtrado))
    st.dataframe(expedicao_filtrado)

    valor_total = f"R$ {expedicao_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

    pendentes_exp, atrasados_exp = calcular_pendentes_atrasados(expedicao)
    if pendentes_exp > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_exp} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados_exp > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_exp} produtos atrasados!</div>', unsafe_allow_html=True)

if perfil_opcao == "Expedição 🚚":
    guia_expedicao()

def guia_OE():
    st.title("Não gerado OE")

    st.write("Total de Itens:", len(perfil3))
    st.dataframe(perfil3)
    #valor_total = f"R$ {perfil3['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    #st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)
	
    pendentes_oee, atrasados_oee = calcular_pendentes_atrasados(perfil3)
    if pendentes_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">Atenção: Você possui {pendentes_oee} produtos pendentes!</div>', unsafe_allow_html=True)
    if atrasados_oee > 0:
        st.sidebar.markdown(f'<div class="blinking-red">Atenção: Você possui {atrasados_oee} produtos atrasados!</div>', unsafe_allow_html=True)

if perfil_opcao == "Não gerado OE ❌":
    guia_OE()

