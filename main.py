import streamlit as st
import pandas as pd
from datetime import datetime
import locale
import plotly.express as px
from io import BytesIO
import plotly.graph_objects as go
from streamlit.components.v1 import html
import plotly.graph_objects as go

st.set_page_config(
    page_title="Sistema de Controle",
    page_icon="planilha/mascote_instagram-removebg-preview.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'C')

@st.cache_data
def carregar_dados():
    df = pd.read_excel('planilha/controledosistema.xlsx')
    return df

df = carregar_dados()

if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

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

st.markdown("""
    <style>
    body {
        color: white; /* Cor do texto */
    }
    .stApp {
    }
    .styled-col {
        border: 2px solid #094780;
        background-color:rgba(9, 70, 128, 0.39);
        border-radius: 10px;
        padding: 5px; /* Reduzido para diminuir o espaço */
        margin: 5px; /* Reduzido para diminuir o espaço */
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 70px; /* Altura mínima para todas as colunas */
        font-size: 1em; /* Tamanho da fonte ajustado */
        box-shadow: inset -30px -30px 45px rgba(0, 0, 0, 0.2);
    }
    .metric-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    .metric-label {
        font-size: 1em; /* Tamanho da fonte ajustado */
        font-weight: bold;
        margin-bottom: 5px; /* Espaço entre o rótulo e o valor */
    }
    .metric-value {
        font-size: 2em; /* Tamanho da fonte ajustado */
        font-weight: bold;
    }
    .chart-container {
    background-color:242F4A;
    padding: 5px; /* Reduzido para diminuir o espaço */
    margin: 5px; /* Reduzido para diminuir o espaço */
    color: white;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 150px; /* Altura mínima para todas as colunas */
    font-size: 0.9em; /* Tamanho da fonte ajustado */
    box-shadow: inset -30px -30px 45px rgba(0, 0, 0, 0.2);
    }
    .date-filters {
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 1001;
        display: flex;
        flex-direction: column;
        gap: 5px;
        background-color: #094780;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

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

def formatar_data(data):
    return data.strftime("%d/%m/%Y")

def guia_carteira():
    st.title("Carteira")
    
    df_filtrado = carteira
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
        data_inicial_filter = pd.to_datetime(st.date_input("Data Inicial", value=pd.to_datetime('2025-01-01')))
    
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
    
    if not df_carteira_filtrado.empty:
        st.write("Total de Itens:", len(df_carteira_filtrado))
        st.dataframe(df_carteira_filtrado)
        valor_total = f"R$ {df_carteira_filtrado['Valor Total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"<span style='font-size: 20px;'><b>Valor Total:</b> {valor_total}</span>", unsafe_allow_html=True)
    else:
        st.warning("Nenhum item encontrado com os filtros aplicados.")  

    df_filtrado = df[colunas_desejadas]

    def gerar_excel(df):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório')
        buffer.seek(0)
        return buffer

    excel_file = gerar_excel(df_filtrado)

    st.download_button(
        label="Exportar Relatório",
        data=excel_file,
        file_name="relatorio_dataframe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def guia_dashboard():

    default_start_date = pd.to_datetime('2025-01-01')
    default_end_date = pd.to_datetime('today')

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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_range = st.date_input(
            "Selecione a data",
            value=(default_start_date, default_end_date),
            min_value=pd.to_datetime('2020-01-01'),
            max_value=pd.to_datetime('today')
        )

        if date_range[0] > date_range[1]:
            st.error("A data inicial não pode ser posterior à data final.")
        else:
            data_inicial_filter, data_final_filter = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

            df_filtrado = carteira[(carteira['Dt.pedido'] >= data_inicial_filter) & (carteira['Dt.pedido'] <= data_final_filter)]

            if data_inicial_filter.month == data_final_filter.month and data_inicial_filter.year == data_final_filter.year:
                mes_ano = data_inicial_filter.strftime('%m/%Y')
                periodo = f"{mes_ano}"
            else:
                mes_ano_inicial = data_inicial_filter.strftime('%m/%Y')
                mes_ano_final = data_final_filter.strftime('%m/%Y')
                periodo = f"{mes_ano_inicial} a {mes_ano_final}"

    df_filtrado = carteira[(carteira['Dt.pedido'] >= data_inicial_filter) & (carteira['Dt.pedido'] <= data_final_filter)]

    produto_frequencia = df_filtrado['Produto'].value_counts().reset_index()
    produto_frequencia.columns = ['Produto', 'Frequência']

    produto_info = df_filtrado[['Produto', 'Modelo']].drop_duplicates()

    produto_frequencia = produto_frequencia.merge(produto_info, on='Produto', how='left')

    total_pedidos = df_filtrado['Ped. Cliente'].nunique()
    pendente = len(df_filtrado[df_filtrado['Status'] == 'Pendente'])
    atrasado = len(df_filtrado[df_filtrado['Status'] == 'Atrasado'])
    modelos_unicos = df_filtrado['Modelo'].nunique()
    total_itensct = df_filtrado['Qtd.'].sum()

    valor_total_separacao = df_filtrado[df_filtrado['Setor'] == 'Separação']['Valor Total'].sum()
    valor_total_compras = df_filtrado[df_filtrado['Setor'] == 'Compras']['Valor Total'].sum()
    valor_total_embalagem = df_filtrado[df_filtrado['Setor'] == 'Embalagem']['Valor Total'].sum()
    valor_total_expedicao = df_filtrado[df_filtrado['Setor'] == 'Expedição']['Valor Total'].sum()

    valor_total_separacao_formatado = f"R${valor_total_separacao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_total_compras_formatado = f"R${valor_total_compras:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_total_embalagem_formatado = f"R${valor_total_embalagem:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    valor_total_expedicao_formatado = f"R${valor_total_expedicao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col_esquerda, col_direita = st.columns(2)

    with col_esquerda:
        st.markdown(f"""
            <div style='display: flex; align-items: center;'>
                <h1 style='margin-right: 5px; margin-bottom: 0;'>📊 Estatísticas Gerais</h1>
                <span style='font-size: 0.8em; color: gray; margin-bottom: 0;'>{periodo}</span>
            </div>
            """, unsafe_allow_html=True)

        sub_col1, sub_col2, sub_col3, sub_col4= st.columns([1,3,3,1])
        with sub_col2:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Total de Pedidos</div>
                        <div class='metric-value'>{total_pedidos}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        #with sub_col2:
        #    st.markdown(f"""
        #        <div class='styled-col'>
        #            <div class='metric-container'>
        #                <div class='metric-label'>Total de Itens</div>
        #                <div class='metric-value'>{len(df)}</div>
        #            </div>
        #        </div>
        #        """, unsafe_allow_html=True)
        with sub_col3:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Total de Pendências</div>
                        <div class='metric-value'>{pendente + atrasado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        sub_col1, sub_col2, sub_col3, sub_col4= st.columns([1,3,3,1])
        
        with sub_col2:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Total por Referência</div>
                        <div class='metric-value'>{modelos_unicos}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with sub_col3:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Total de Cartelas</div>
                        <div class='metric-value'>{total_itensct:.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<h1>🏢 Setores</h1>", unsafe_allow_html=True)

        sub_col1, sub_col2 = st.columns(2)        

        total_separacao = len(df_filtrado[df_filtrado['Setor'] == 'Separação'])
        total_compras = len(df_filtrado[df_filtrado['Setor'] == 'Compras'])
        total_embalagem = len(df_filtrado[df_filtrado['Setor'] == 'Embalagem'])
        total_expedicao = len(df_filtrado[df_filtrado['Setor'] == 'Expedição'])

        with sub_col1:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Separação</div>
                        <div class='metric-value'>{valor_total_separacao_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with sub_col2:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Compras</div>
                        <div class='metric-value'>{valor_total_compras_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        sub_col1, sub_col2 = st.columns(2)

        with sub_col1:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Embalagem</div>
                        <div class='metric-value'>{valor_total_embalagem_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with sub_col2:
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Expedição</div>
                        <div class='metric-value'>{valor_total_expedicao_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
    with col_direita:
        sub_col1, sub_col2= st.columns(2)
    
        with sub_col1:
            valor_total_entregues = df_filtrado[df_filtrado['Status'] == 'Entregue']['Valor Total'].sum()
            valor_total_entregues_formatado = f"R${valor_total_entregues:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f"""
                <div class='styled-col'>
                <div class='metric-container'>
                    <div class='metric-label'>Faturamento Total</div>
                    <div class='metric-value'>{valor_total_entregues_formatado}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with sub_col2:
            valor_total_pendencias = df_filtrado[df_filtrado['Status'] == 'Pendente']['Valor Total'].sum()
            valor_total_atrasados = df_filtrado[df_filtrado['Status'] == 'Atrasado']['Valor Total'].sum()
            valor_total_saldo = valor_total_pendencias + valor_total_atrasados
            valor_total_saldo_formatado = f"R${valor_total_saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f"""
                <div class='styled-col'>
                    <div class='metric-container'>
                        <div class='metric-label'>Valor Total de Saldo</div>
                        <div class='metric-value'>{valor_total_saldo_formatado}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
       
        carteira_entregue = carteira[carteira['Status'] == 'Entregue']

        carteira_entregue['Mes'] = carteira_entregue['Dt.pedido'].dt.to_period('M')

        valor_total_por_mes = carteira_entregue.groupby('Mes')['Valor Total'].sum().reset_index()

        valor_total_por_mes['Mes'] = valor_total_por_mes['Mes'].dt.strftime('%Y-%m')

        fig_linha = px.bar(
            valor_total_por_mes, 
            x='Mes',  
            y='Valor Total', 
            title='Faturamento Mensal',
            labels={'Mes': 'Mês', 'Valor Total': 'Valor Total'},
            color='Valor Total', 
            color_continuous_scale='Viridis',
            hover_data={'Mes': True, 'Valor Total': True}
        )  

        fig_linha.update_layout(
            xaxis_title='Mês',
            yaxis_title='Valor Total',
            xaxis_tickangle=0,  
            bargap=0.2,
            paper_bgcolor="rgba(0, 0, 0, 0)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            height=350,
            margin=dict(l=10, r=10, t=60, b=0),
        )

        st.plotly_chart(fig_linha, use_container_width=False)

        sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)

        with sub_col1:
            fig_indicador1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_separacao,
            title={'text': "Separação", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [None, 1000], 'visible': False},
                'bar': {'color': "rgb(9, 71, 128)"},
                'bgcolor': "white",
                'borderwidth': 1.5,
                'bordercolor': "skyblue",
                'steps': [
                    {'range': [0, 1000], 'color': 'lightgray'}
                ],
                }
            ))
            fig_indicador1.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=150 
            )
            st.plotly_chart(fig_indicador1, use_container_width=True)

        with sub_col2:
            fig_indicador2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_compras,
            title={'text': "Compras", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [None, 1000], 'visible': False},
                'bar': {'color': "rgb(9, 71, 128)"},
                'bgcolor': "white",
                'borderwidth': 1.5,
                'bordercolor': "skyblue",
                'steps': [
                    {'range': [0, 1000], 'color': 'lightgray'}
                ],
            }
        ))
            fig_indicador2.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=150 
            )
            st.plotly_chart(fig_indicador2, use_container_width=True)

        with sub_col3:
            fig_indicador3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_embalagem,
                title={'text': "Embalagem", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [None, 1000], 'visible': False},
                    'bar': {'color': "rgb(9, 71, 128)"},
                    'bgcolor': "white",
                    'borderwidth': 1.5,
                    'bordercolor': "skyblue",
                    'steps': [
                        {'range': [0, 1000], 'color': 'lightgray'}
                    ],
                }
            ))
            fig_indicador3.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=150 
            )
            st.plotly_chart(fig_indicador3, use_container_width=True)


        with sub_col4:
            fig_indicador4 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_expedicao,
                title={'text': "Expedição", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [None, 1000], 'visible': False},
                    'bar': {'color': "rgb(9, 71, 128)"},
                    'bgcolor': "white",
                    'borderwidth': 1.5,
                    'bordercolor': "skyblue",
                    'steps': [
                        {'range': [0, 1000], 'color': 'lightgray'}
                    ],
                }
            ))
            fig_indicador4.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=150 
            )
            st.plotly_chart(fig_indicador4, use_container_width=True)
    
        
perfil_opcao = ("Administrador ⚙️")

if perfil_opcao == "Administrador ⚙️":
    admin_opcao = st.sidebar.radio("Opções do Administrador", ("Dashboard", "Notificações"))
    
    if admin_opcao == "Dashboard":
        guia_dashboard()
        