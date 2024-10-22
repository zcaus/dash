import locale
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

# Configuração da página com título e favicon
st.set_page_config(
    page_title="sistema de controle",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configuração inicial do locale e da página
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')  # ou 'en_US.UTF-8' como fallback

# Estilos customizados do streamlit
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
        .stapp {
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
colunas_para_ocultar = ['emp', 'código', 'razão', 'uf', 'tp.venda', 'f.pagto', 'vendedor', '% comissão', 
                        'operador', '% comissão.1', '% icms', '% ipi', 'vl.desc.', 'atrasado']

# Carregar os dados e ocultar colunas desnecessárias
@st.cache_data
def load_data(file_path='planilha/PEDIDOS_VOLPE8.XLSX'):
    try:
        df = pd.read_excel(file_path)
        return df.drop(columns=colunas_para_ocultar, errors='ignore')
    except Exception as e:  # Corrigido para usar Exception
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()  # Corrigido para DataFrame

df = load_data()

# Contando os modelos únicos
modelos_unicos = df['modelo'].nunique()
df['valor unit.'] = pd.to_numeric(df['valor unit.'], errors='coerce')
df['qtd.'] = pd.to_numeric(df['qtd.'], errors='coerce')

# Substituir NaN por 0
df['valor unit.'].fillna(0, inplace=True)
df['qtd.'].fillna(0, inplace=True)

# Agora é seguro multiplicar
df['valor total'] = df['valor unit.'] * df['qtd.']

# Remover linhas com 'un' igual a 'kg'
df = df[df['un'] != 'kg']

# Exemplo: remover linhas com 'fantasia' em uma lista específica
df = df[~df['fantasia'].isin(['prime', 'amd 5', 'amd 10', 'frexco', 'sesc interlagos', 'rodrigo melo', 
                              'foxmix', 'ccinter antônio', 'l a refrigeracao', 'nacao natural'])]

# Verifique as colunas que você sabe que são de datas
colunas_de_data = ['dt.pedido', 'dt.fat.', 'prev.entrega']
df['status'] = 'pendente'

# Calcular o total de pedidos únicos
total_pedidos = df['ped. cliente'].nunique()

# Exibir o total de pedidos como uma linha adicional
estatisticas_gerais = pd.DataFrame({
    'estatística': ['total de pedidos'],
    'valor': [total_pedidos]
})

# Cria uma coluna auxiliar para indicar quais linhas foram atualizadas
df['status_atualizado'] = df['fantasia'] == ' '

# Define a função `update_status`
now = datetime.now()
df['dt.fat.'] = pd.to_datetime(df['dt.fat.'], errors='coerce')
df['prev.entrega'] = pd.to_datetime(df['prev.entrega'], errors='coerce')

def update_status(row):
    if row['status_atualizado']:
        return row['status']
    if pd.isnull(row['dt.fat.']):
        return 'atrasado' if row['prev.entrega'] < now else 'pendente'
    return 'entregue'

# Atualiza status
df['status'] = df.apply(update_status, axis=1)

# Remove a coluna auxiliar
df.drop(columns='status_atualizado', inplace=True)

# Contagem de pedidos pendentes e atrasados
pendente = (df['status'] == 'pendente').sum()
atrasado = (df['status'] == 'atrasado').sum()

# Seleção de perfil
perfil = st.sidebar.selectbox("selecione o perfil", ["administrador", "separação", "compras", "embalagem"])

# Converte colunas de data e calcula 'valor total'
df['valor total'] = df['valor unit.'] * df['qtd.']
df['valor total'] = df['valor total'].apply(lambda x: locale.currency(x, grouping=True, symbol=None))

def calcular_pendentes_atrasados(df):
    pendentes = (df['status'] == 'pendente').sum()
    atrasados = (df['status'] == 'atrasado').sum()
    return pendentes, atrasados

def create_value_bar_chart2(df, produto, modelo):
    contagem = df[produto].value_counts().reset_index()
    contagem.columns = [produto, 'frequência']

    contagem = contagem.merge(df[[produto, modelo]], on=produto, how='left').drop_duplicates()

    bar_chart2 = px.bar(
        contagem, 
        x=produto, 
        y='frequência', 
        title='total por referência',
        labels={produto: 'código', 'frequência': 'quantidade'},
        color='frequência', 
        color_continuous_scale='viridis',
        hover_data={produto: True, 'frequência': True, modelo: True}
    )

    bar_chart2.update_layout(
        xaxis_title='código do produto',
        yaxis_title='número de pedidos',
        xaxis_tickangle=-45,
        bargap=0.2,
        xaxis=dict(range=[0, 30], fixedrange=False)
    )

    return bar_chart2

# Gráficos e funções
def create_percentage_chart(df):
    total_pedidos = df['status'].value_counts()
    total = total_pedidos.sum()
    percentage = (total_pedidos / total) * 100
    percentage_summary = percentage.reset_index()
    percentage_summary.columns = ['status', 'percentual']
    pie_chart = px.pie(percentage_summary, 
                       values='percentual', 
                       names='status', 
                       title='porcentagem de pedidos por status')
    return pie_chart

def create_value_bar_chart(df):
    df['valor total numérico'] = df['valor total'].apply(lambda x: locale.atof(x.strip()))

    df_filtrado = df[df['status'].isin(['pendente', 'atrasado', 'entregue'])]
    total_por_status = df_filtrado.groupby('status')['valor total numérico'].sum().reset_index()
    total_por_status.columns = ['status', 'valor total']

    bar_chart = px.bar(
        total_por_status, 
        x='status', 
        y='valor total', 
        text='valor total', 
        title='valor total por status',
        labels={'valor total': 'valor total (r$)', 'status': ''}
    )

    return bar_chart

def guia_dashboard():
    st.markdown("<h3>estatísticas gerais <small style='font-size: 0.4em;'>(mês atual)</small></h3>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("total de pedidos", total_pedidos)
    with col2:
        st.metric("total de itens", len(df))
    with col3:
        st.metric("total de produtos pendentes", pendente)
    with col4:
        st.metric("total por referência", modelos_unicos)

    st.write(" ")

    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.plotly_chart(create_percentage_chart(df), use_container_width=True)

    with col_grafico2:
        st.plotly_chart(create_value_bar_chart(df), use_container_width=True)

    st.write(" ")
    st.plotly_chart(create_value_bar_chart2(df, 'produto', 'modelo'), use_container_width=True)

    separacao_df, compras_df = mover_pedidos(df)

    st.markdown("<h3>pedidos pendentes<small style='font-size: 0.4em;'> (por setor)</small></h3>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("separação", len(separacao_df))
    with col2:
        st.metric("compras", len(compras_df))
    with col3:
        st.metric("embalagem", '?')  # Atualize isso conforme necessário
    with col4:
        st.metric("expedição", '?')  # Atualize isso conforme necessário

def guia_carteira():
    st.title("carteira")

    df_filtrado = df[df['un'] != 'kg']

    cliente_selecionado = st.selectbox("selecione o cliente", ["todos os clientes"] + df_filtrado['fantasia'].unique().tolist())
    pedidos_cliente = df_filtrado if cliente_selecionado == "todos os clientes" else df_filtrado[df_filtrado['fantasia'] == cliente_selecionado]

    pedido_filtro = st.text_input("filtrar por número de pedido:")
    status_filtro = st.selectbox("filtrar por status", ["todos", "pendente", "atrasado", "entregue"])

    if pedido_filtro:
        pedidos_cliente = pedidos_cliente[pedidos_cliente['ped. cliente'].astype(str).str.contains(pedido_filtro)]

    if status_filtro != "todos":
        pedidos_cliente = pedidos_cliente[pedidos_cliente['status'] == status_filtro]

    total_linhas_depois = pedidos_cliente.shape[0]
    st.write(f"número de linhas: {total_linhas_depois}")

    st.dataframe(pedidos_cliente, use_container_width=True)
    total_valor = (pedidos_cliente['valor unit.'] * pedidos_cliente['qtd.']).sum()
    st.metric("total (r$)", locale.currency(total_valor, grouping=True, symbol=None))

def guia_notificacoes():
    st.title("notificações")
    st.write("todas novidades do sistema e atualizações serão notificadas neste campo.")

def mover_pedidos(df):
    pedidos_com_hifen = df[df['nr.pedido'].astype(str).str.contains('-')]
    pedidos_sem_hifen = df[~df['nr.pedido'].astype(str).str.contains('-')]

    compras_df = pedidos_com_hifen[pedidos_com_hifen['status'].isin(['pendente'])]
    separacao_df = pedidos_sem_hifen[pedidos_sem_hifen['status'] == 'pendente']

    return separacao_df, compras_df

def guia_separacao():
    st.title("separação")

    separacao_df, _ = mover_pedidos(df)
    separacao_df = separacao_df[(separacao_df['status'] == 'pendente') | (~separacao_df['status'].str.contains('-'))]
    separacao_df = separacao_df.dropna(axis=1, how='all')

    today = datetime.now()

    if 'dt.pedido' in separacao_df.columns:
        separacao_df['dt.pedido'] = pd.to_datetime(separacao_df['dt.pedido'], errors='coerce')

        separacao_df['atrasado'] = (today - separacao_df['dt.pedido']) > timedelta(days=2)

        separacao_df.loc[(separacao_df['atrasado']) & (separacao_df['status'] == 'pendente'), 'status'] = 'atrasado'
    else:
        st.warning("a coluna 'dt.pedido' não foi encontrada no dataframe.")

    pendentes_sep, atrasados_sep = calcular_pendentes_atrasados(separacao_df)
    if pendentes_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">atenção: você possui {pendentes_sep} produto(s) pendente(s) no total!</div>', unsafe_allow_html=True)
    if atrasados_sep > 0:
        st.sidebar.markdown(f'<div class="blinking-red">atenção: você possui {atrasados_sep} produto(s) atrasado(s) no total!</div>', unsafe_allow_html=True)

    cliente_selecionado = st.selectbox("selecione o cliente", ["todos os clientes"] + separacao_df['fantasia'].unique().tolist())
    separacao_df = separacao_df if cliente_selecionado == "todos os clientes" else separacao_df[separacao_df['fantasia'] == cliente_selecionado]

    pedido_filtro = st.text_input("filtrar por número de pedido:")
    status_filtro = st.selectbox("filtrar por status", ["todos", "pendente", "atrasado"])

    if pedido_filtro:
        separacao_df = separacao_df[separacao_df['ped. cliente'].astype(str).str.contains(pedido_filtro)]

    if status_filtro != "todos":
        separacao_df = separacao_df[separacao_df['status'] == status_filtro]

    total_linhas_depois = separacao_df.shape[0]
    st.write(f"número de linhas: {total_linhas_depois}")

    st.dataframe(separacao_df, use_container_width=True)
    total_valor = (separacao_df['valor unit.'] * separacao_df['qtd.']).sum()
    st.metric("total (r$)", locale.currency(total_valor, grouping=True, symbol=None))

def guia_compras():
    st.title("compras")

    _, compras_df_geral = mover_pedidos(df)
    compras_df_geral = compras_df_geral[(compras_df_geral['status'] == 'pendente') | (compras_df_geral['status'].str.contains('-'))]

    pendentes_compras_geral, atrasados_compras_geral = calcular_pendentes_atrasados(compras_df_geral)

    if pendentes_compras_geral > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">atenção: você possui {pendentes_compras_geral} produto(s) pendente(s) no total!</div>', unsafe_allow_html=True)
    if atrasados_compras_geral > 0:
        st.sidebar.markdown(f'<div class="blinking-red">atenção: você possui {atrasados_compras_geral} produto(s) atrasado(s) no total!</div>', unsafe_allow_html=True)

    _, compras_df = mover_pedidos(df)
    compras_df = compras_df[(compras_df['status'] == 'pendente') | (compras_df['status'].str.contains('-'))]
    compras_df = compras_df.dropna(axis=1, how='all')

    cliente_selecionado = st.selectbox("selecione o cliente", ["todos os clientes"] + compras_df['fantasia'].unique().tolist())
    compras_df = compras_df if cliente_selecionado == "todos os clientes" else compras_df[compras_df['fantasia'] == cliente_selecionado]

    pedido_filtro = st.text_input("filtrar por número de pedido:")
    status_filtro = st.selectbox("filtrar por status", ["todos", "pendente", "atrasado"])

    if pedido_filtro:
        compras_df = compras_df[compras_df['ped. cliente'].astype(str).str.contains(pedido_filtro)]

    if status_filtro != "todos":
        compras_df = compras_df[compras_df['status'] == status_filtro]

    total_linhas_depois = compras_df.shape[0]
    st.write(f"número de linhas: {total_linhas_depois}")

    st.dataframe(compras_df, use_container_width=True)
    total_valor = (compras_df['valor unit.'] * compras_df['qtd.']).sum()
    st.metric("total (r$)", locale.currency(total_valor, grouping=True, symbol=None))

def guia_embalagem():
    st.title("embalagem")

# Interface por perfil
if perfil == "administrador":
    aba = st.sidebar.radio("escolha uma aba", ["dashboard", "carteira", "notificações"])
    if aba == "dashboard":
        guia_dashboard()
    elif aba == "carteira":
        guia_carteira()
    elif aba == "notificações":
        guia_notificacoes()
    if pendente > 0:
        st.sidebar.markdown(f'<div class="blinking-yellow">atenção: você possui {pendente} produto(s) pendente(s)!</div>', unsafe_allow_html=True)
    if atrasado > 0:
        st.sidebar.markdown(f'<div class="blinking-red">atenção: você possui {atrasado} produto(s) atrasado(s)!</div>', unsafe_allow_html=True)
else:
    guia_notificacoes()
    if perfil == "separação":
        guia_separacao()
    elif perfil == "compras":
        guia_compras()