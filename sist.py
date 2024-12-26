import streamlit as st
import pandas as pd
from datetime import datetime
import locale
import plotly.express as px
import time
from PIL import Image
import base64
from io import BytesIO
import plotly.graph_objects as go

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
    .centered {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

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

separacao = separacao[(separacao['Ped. Cliente'] != 'TUMELERO') & (separacao['Ped. Cliente'] != 'ESTOQUE FOX') & (separacao['Ped. Cliente'] != 'TELHA 14.10.24') & (separacao['Ped. Cliente'] != 'ESTOQUE FOX') & (separacao['Ped. Cliente'] != 'TELHA 18.10.24') & (separacao['Ped. Cliente'] != 'FANAN/TERUYA') & (separacao['Ped. Cliente'] != 'HC FOX 11.11.24') & (separacao['Ped. Cliente'] != 'TUMELEIRO 2') & (separacao['Ped. Cliente'] != 'AMOSTRAS') & (separacao['Ped. Cliente'] != 'LOJAS 20.12.2024') & (separacao['Ped. Cliente'] != 'SALDO TELHANORTE')]
compras = compras[(compras['Ped. Cliente'] != 'TUMELERO') & (compras['Ped. Cliente'] != 'ESTOQUE FOX') & (compras['Ped. Cliente'] != 'TELHA 14.10.24') & (compras['Ped. Cliente'] != 'ESTOQUE FOX') & (compras['Ped. Cliente'] != 'TELHA 18.10.24') & (compras['Ped. Cliente'] != 'FANAN/TERUYA') & (compras['Ped. Cliente'] != 'HC FOX 11.11.24') & (compras['Ped. Cliente'] != 'TUMELEIRO 2') & (compras['Ped. Cliente'] != 'AMOSTRAS') & (compras['Ped. Cliente'] != 'LOJAS 20.12.2024') & (compras['Ped. Cliente'] != 'SALDO TELHANORTE')]
embalagem = embalagem[(embalagem['Ped. Cliente'] != 'TUMELERO') & (embalagem['Ped. Cliente'] != 'ESTOQUE FOX') & (embalagem['Ped. Cliente'] != 'TELHA 14.10.24') & (embalagem['Ped. Cliente'] != 'ESTOQUE FOX') & (embalagem['Ped. Cliente'] != 'TELHA 18.10.24') & (embalagem['Ped. Cliente'] != 'FANAN/TERUYA') & (embalagem['Ped. Cliente'] != 'HC FOX 11.11.24') & (embalagem['Ped. Cliente'] != 'TUMELEIRO 2') & (embalagem['Ped. Cliente'] != 'AMOSTRAS') & (embalagem['Ped. Cliente'] != 'LOJAS 20.12.2024') & (embalagem['Ped. Cliente'] != 'SALDO TELHANORTE')]
expedicao = expedicao[(expedicao['Ped. Cliente'] != 'TUMELERO') & (expedicao['Ped. Cliente'] != 'ESTOQUE FOX') & (expedicao['Ped. Cliente'] != 'TELHA 14.10.24') & (expedicao['Ped. Cliente'] != 'ESTOQUE FOX') & (expedicao['Ped. Cliente'] != 'TELHA 18.10.24') & (expedicao['Ped. Cliente'] != 'FANAN/TERUYA') & (expedicao['Ped. Cliente'] != 'HC FOX 11.11.24') & (expedicao['Ped. Cliente'] != 'TUMELEIRO 2') & (expedicao['Ped. Cliente'] != 'AMOSTRAS') & (expedicao['Ped. Cliente'] != 'LOJAS 20.12.2024') & (expedicao['Ped. Cliente'] != 'SALDO TELHANORTE')]
perfil3 = perfil3[(perfil3['Ped. Cliente'] != 'TUMELERO') & (perfil3['Ped. Cliente'] != 'ESTOQUE FOX') & (perfil3['Ped. Cliente'] != 'TELHA 14.10.24') & (perfil3['Ped. Cliente'] != 'ESTOQUE FOX') & (perfil3['Ped. Cliente'] != 'TELHA 18.10.24') & (perfil3['Ped. Cliente'] != 'FANAN/TERUYA') & (perfil3['Ped. Cliente'] != 'HC FOX 11.11.24') & (perfil3['Ped. Cliente'] != 'TUMELEIRO 2') & (perfil3['Ped. Cliente'] != 'AMOSTRAS') & (perfil3['Ped. Cliente'] != 'LOJAS 20.12.2024') & (perfil3['Ped. Cliente'] != 'SALDO TELHANORTE')]
carteira = carteira[(carteira['Ped. Cliente'] != 'TUMELERO') & (carteira['Ped. Cliente'] != 'ESTOQUE FOX') & (carteira['Ped. Cliente'] != 'TELHA 14.10.24') & (carteira['Ped. Cliente'] != 'ESTOQUE FOX') & (carteira['Ped. Cliente'] != 'TELHA 18.10.24') & (carteira['Ped. Cliente'] != 'FANAN/TERUYA') & (carteira['Ped. Cliente'] != 'HC FOX 11.11.24') & (carteira['Ped. Cliente'] != 'TUMELEIRO 2') & (carteira['Ped. Cliente'] != 'AMOSTRAS') & (carteira['Ped. Cliente'] != 'LOJAS 20.12.2024') & (carteira['Ped. Cliente'] != 'SALDO TELHANORTE')]

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

    # Filtrar DataFrame para manter apenas as colunas desejadas
    df_filtrado = df[colunas_desejadas]

    # Função para gerar o Excel
    def gerar_excel(df):
    # Salva o DataFrame em um buffer de memória (BytesIO)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)  # Volta o cursor para o início do buffer
        return buffer

    # Gerar o Excel assim que a página for carregada
    excel_file = gerar_excel(df_filtrado)

    # Botão para baixar o Excel
    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="relatorio_dataframe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def guia_dashboard():
    
    df_carteira = carteira

    col1, col2, col3, col4, col5= st.columns([5,1,1,3,3])
    
    with col1:
         st.markdown("<h3>📊 Estatísticas Gerais <small style='font-size: 0.4em;'></small></h3>", unsafe_allow_html=True)
    with col4:
        valor_total_entregues = df_carteira[df_carteira['Status'] == 'Entregue']['Valor Total'].sum()
        st.metric("Faturamento Total", 
                "R${:,.2f}".format(valor_total_entregues).replace(",", "X").replace(".", ",").replace("X", "."))
    with col5:
        valor_total_pendencias = df_carteira[df_carteira['Status'] == 'Pendente']['Valor Total'].sum()
        st.metric("Valor Total de Saldo", 
                "R${:,.2f}".format(valor_total_pendencias).replace(",", "X").replace(".", ",").replace("X", "."))


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
    
    col_esquerda, col_direita = st.columns(2)

    with col_esquerda:
        sub_col1, sub_col2, sub_col3 = st.columns(3)
        with sub_col1:
            st.metric("Total de Pedidos", total_pedidos)
        with sub_col2:
            st.metric("Total de Itens", len(df))
        with sub_col3:
            st.metric("Total de Pendências", pendente)

        sub_col1, sub_col2, sub_col3, sub_col4, sub_col5 = st.columns([1,3,3,1,1])
        
        with sub_col2:
            st.metric("Total por Referência", modelos_unicos)
        with sub_col3:
            st.metric("Total de Cartelas", "{:.0f}".format(total_itensct))
        
        st.markdown("<h3>🏢 Setores</h3>", unsafe_allow_html=True)

        sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)        

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

        with sub_col2:
            st.metric("Separação", total_separacao)
            st.markdown(f"<span style='font-size: 0.8em; margin-top: -10px; display:inline-block;'>P {pendencia_separacao} | A {atraso_separacao}</span>", unsafe_allow_html=True)

        with sub_col3:
            st.metric("Compras", total_compras)
            st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_compras} | A {atraso_compras}</span>", unsafe_allow_html=True)

        sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)

        with sub_col2:
            st.metric("Embalagem", total_embalagem)
            st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_embalagem} | A {atraso_embalagem}</span>", unsafe_allow_html=True)

        with sub_col3:
            st.metric("Expedição", total_expedicao)
            st.markdown(f"<span style='font-size: 0.8em;'>P {pendencia_expedicao} | A {atraso_expedicao}</span>", unsafe_allow_html=True)


    with col_direita:
        
        valor_total_por_status = df_carteira.groupby('Status')['Valor Total'].sum().reset_index()
        fig_barras = px.bar(valor_total_por_status, x='Status', y='Valor Total', title="Valor Total por Status")
        st.plotly_chart(fig_barras, use_container_width=True)

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

    # Filtrar DataFrame para manter apenas as colunas desejadas
    pf1_filtrado = perfil1_filtrado[colunas_desejadas]

    # Função para gerar o Excel
    def gerar_excel(df):
    # Salva o DataFrame em um buffer de memória (BytesIO)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)  # Volta o cursor para o início do buffer
        return buffer

    # Gerar o Excel assim que a página for carregada
    excel_file = gerar_excel(pf1_filtrado)

    # Botão para baixar o Excel
    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="separacao.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

    # Filtrar DataFrame para manter apenas as colunas desejadas
    cp_filtrado = compras_filtrado[colunas_desejadas]

    # Função para gerar o Excel
    def gerar_excel(df):
    # Salva o DataFrame em um buffer de memória (BytesIO)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)  # Volta o cursor para o início do buffer
        return buffer

    # Gerar o Excel assim que a página for carregada
    excel_file = gerar_excel(cp_filtrado)

    # Botão para baixar o Excel
    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="itens_compras.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

    # Filtrar DataFrame para manter apenas as colunas desejadas
    emb_filtrado = embalagem_filtrado[colunas_desejadas]

    # Função para gerar o Excel
    def gerar_excel(df):
    # Salva o DataFrame em um buffer de memória (BytesIO)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)  # Volta o cursor para o início do buffer
        return buffer

    # Gerar o Excel assim que a página for carregada
    excel_file = gerar_excel(emb_filtrado)

    # Botão para baixar o Excel
    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="itens_embalagem.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

    # Filtrar DataFrame para manter apenas as colunas desejadas
    exp_filtrado = expedicao_filtrado[colunas_desejadas]

    # Função para gerar o Excel
    def gerar_excel(df):
    # Salva o DataFrame em um buffer de memória (BytesIO)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)  # Volta o cursor para o início do buffer
        return buffer

    # Gerar o Excel assim que a página for carregada
    excel_file = gerar_excel(exp_filtrado)

    # Botão para baixar o Excel
    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="itens_expedicao.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

