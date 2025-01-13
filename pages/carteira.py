import pandas as pd
import streamlit as st
import locale
from datetime import datetime

st.set_page_config(
    page_title="Sistema de Controle",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

@st.cache_data
def carregar_dados():
    df = pd.read_excel('planilha/controledosistema.xlsx')
    return df

df = carregar_dados()

if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

dados = st.session_state.dados

carteira = df

colunas_desejadas = [
     'Setor', 'Ped. Cliente', 'Dt.pedido', 'Fantasia', 'Produto', 'Modelo', 
    'Qtd.', 'Valor Unit.', 'Valor Total', 'Qtd.a produzir', 
    'Qtd. Produzida', 'Qtd.a liberar','Prev.entrega','Dt.fat.' , 'Nr.pedido'
]

df = df[colunas_desejadas]

exclusoes = [
    'TUMELERO', 'ESTOQUE FOX', 'TELHA 14.10.24', 'TELHA 18.10.24', 
    'FANAN/TERUYA', 'HC FOX 11.11.24', 'TUMELEIRO 2', 
    'AMOSTRAS', 'LOJAS 20.12.2024', 'SALDO TELHANORTE'
]

df = df[~df['Ped. Cliente'].isin(exclusoes)]

col1, col2 ,col3, col4, col5, col6, col7 = st.columns(7)

with col1:
        st.page_link("main.py", label="Dashboard", icon="📊")
with col2:
        st.page_link("pages/carteira.py", label="Carteira", icon="📇")
with col3:
        st.page_link("pages/separacao.py", label="Separação", icon="💻")
with col4:
        st.page_link("pages/compras.py", label="Compras", icon="🛒")
with col5:
        st.page_link("pages/embalagem.py", label="Embalagem", icon="📦")
with col6:
        st.page_link("pages/expedicao.py", label="Expedição", icon="🚚")
with col7:
        st.page_link("pages/semOE.py", label="Sem OE", icon="❌")

st.title('Carteira')

col1, col2, col3, col_date_filter1, col_date_filter2 = st.columns(5)

with col1:
    fantasias = df['Fantasia'].unique()
    fantasias = ['Todos'] + list(fantasias)
    fantasia_selecionada = st.selectbox('Selecione o Cliente', fantasias)

with col2:
    pedidos = df['Ped. Cliente'].unique()
    pedidos = ['Todos'] + list(pedidos)
    pedido_selecionado = st.selectbox('Filtrar por Pedido', pedidos)

with col3:
    setores = df['Setor'].unique()
    setores = ['Todos'] + list(setores)
    setor_selecionado = st.selectbox('Filtrar por Setor', setores)

with col_date_filter1:
    data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2025-01-01')))

with col_date_filter2:
    data_final_filter = pd.to_datetime(st.date_input("Data Final", value=pd.to_datetime('today')))

df_filtrado = df

if fantasia_selecionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Fantasia'] == fantasia_selecionada]

# Filtrar com base no pedido selecionado
if pedido_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Ped. Cliente'] == pedido_selecionado]

# Filtrar com base no setor selecionado
if setor_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Setor'] == setor_selecionado]

df_filtrado = df_filtrado[(df_filtrado['Dt.pedido'] >= data_inicial_filter) & (df_filtrado['Dt.pedido'] <= data_final_filter)]

valor_total = locale.format_string("%.2f", df_filtrado['Valor Total'].sum(), grouping=True)
valor_total = f"R$ {df_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.write("Total de Itens:", len(df_filtrado))
st.dataframe(df_filtrado)

# Exibir o valor total como métrica
st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)

