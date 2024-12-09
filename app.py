import streamlit as st
import pandas as pd
from datetime import datetime

# Função para carregar os dados
@st.cache_data
def carregar_dados(caminho):
    dados = pd.read_excel(caminho, usecols=[
        'Ped. Cliente', 'Dt.pedido', 'Fantasia', 'Produto', 'Modelo', 
        'Qtd.', 'Valor Unit.', 'Valor Total', 'Qtd.a produzir', 
        'Qtd. Produzida', 'Qtd.a liberar', 'Prev.entrega', 'Dt.fat.', 'Nr.pedido'
    ])
    
    dados['Dt.pedido'] = pd.to_datetime(dados['Dt.pedido'], errors='coerce')
    
    # Remover linhas onde 'Nr.pedido' está vazio ou NaN
    dados = dados[dados['Nr.pedido'].notna() & (dados['Nr.pedido'] != '')]
    
    # Remover linhas onde 'Ped. Cliente' seja igual a 'TUMELERO'
    dados = dados[dados['Ped. Cliente'] != 'TUMELERO']
    
    return dados

# Função para classificar setores automaticamente
def classificar_setor_automatico(pedido, pedidos_df):
    pedido_id = str(pedido['Nr.pedido']).split('-')[0]  # Extrai a parte do pedido sem sufixo
    possui_sufixo = '-' in str(pedido['Nr.pedido'])  # Verifica se o pedido tem sufixo

    # Se "Qtd. Produzida" for preenchida, vai para Expedição
    if pd.notnull(pedido['Qtd. Produzida']) and pedido['Qtd. Produzida'] > 0:
        return "Expedição"

    if possui_sufixo:  # Pedido com sufixo
        # Se "Qtd. a produzir" estiver vazia, vai para "Sem O.E."
        if pd.isnull(pedido['Qtd.a produzir']) or pedido['Qtd.a produzir'] == 0:
            return "Sem O.E."
        # Caso contrário, pode ir para Produção ou Compras
        if pedido['Qtd.a liberar'] > 0:
            return "Embalagem"
        else:
            return "Compras"
    
    else:  # Pedido sem sufixo
        # Verifica se existe algum pedido com o mesmo número sem sufixo, mas com sufixo (ex: "1234" e "1234-1")
        if (pedidos_df['Nr.pedido'].str.startswith(pedido_id) & pedidos_df['Nr.pedido'].str.contains('-')).any():
            return "Expedição"  # Pedido sem sufixo vai para Expedição se houver um pedido com sufixo
        else:
            return "Separação"  # Caso contrário, vai para Separação

# Função para identificar e criar novos pedidos com base na diferença de Qtd.a produzir e Qtd.a liberar
def criar_novos_pedidos_com_diferenca(df):
    novos_pedidos = []  # Lista para armazenar os novos pedidos
    for index, pedido in df.iterrows():
        # Verifica se a quantidade a produzir é maior que a quantidade a liberar
        if pd.notnull(pedido['Qtd.a produzir']) and pd.notnull(pedido['Qtd.a liberar']):
            if pedido['Qtd.a produzir'] > pedido['Qtd.a liberar']:
                quantidade_diferenca = pedido['Qtd.a produzir'] - pedido['Qtd.a liberar']
                
                # Cria uma nova linha com a quantidade de diferença e manda para Compras
                novo_pedido = pedido.copy()  # Copia o pedido original
                novo_pedido['Qtd.'] = quantidade_diferenca  # Ajusta a quantidade para a nova linha
                novo_pedido['Qtd.a produzir'] = quantidade_diferenca  # Preenche a quantidade a produzir com o valor da diferença
                novo_pedido['Setor'] = 'Compras'  # Coloca na guia de Compras
                novos_pedidos.append(novo_pedido)  # Adiciona à lista de novos pedidos

                # Atualiza a linha original para Expedição
                df.at[index, 'Qtd.'] = pedido['Qtd.a liberar']  # Ajusta a quantidade original
                df.at[index, 'Setor'] = 'Expedição'  # Coloca na guia de Expedição

    # Concatena os novos pedidos com o DataFrame original
    return pd.concat([df, pd.DataFrame(novos_pedidos)], ignore_index=True)

# Função para definir a data e o status
def definir_data_e_status(dataframe):
    # Converter colunas para datetime
    dataframe['Dt.fat.'] = pd.to_datetime(dataframe['Dt.fat.'], errors='coerce')
    dataframe['Prev.entrega'] = pd.to_datetime(dataframe['Prev.entrega'], errors='coerce')

    # Definir Status: Pendente por padrão
    dataframe['Status'] = 'Pendente'

    # Alterar Status para "Entregue" quando Dt.fat. não for nulo
    dataframe.loc[dataframe['Dt.fat.'].notna(), 'Status'] = 'Entregue'
     
    return dataframe

# Carregar os dados
caminho_planilha = "planilha/controledosistema2.xlsx"
df = carregar_dados(caminho_planilha)

# Identificar e criar novos pedidos para a diferença de quantidade
df = criar_novos_pedidos_com_diferenca(df)

# Classificar setores
df['Setor'] = df.apply(lambda pedido: classificar_setor_automatico(pedido, df), axis=1)

# Aplicar a função para definir o Status
df = definir_data_e_status(df)

# Filtrar pedidos com status "Pendente"
df_nao_faturados = df[df['Status'] == "Pendente"]

# Exibição em guias
abas = st.tabs(["Administrador", "Separação", "Compras", "Embalagem", "Expedição", "Sem O.E."])

with abas[0]:
    st.subheader("Todos os Pedidos (Administrador)")
    st.dataframe(df)  # Exibe todos os pedidos, incluindo entregues

with abas[1]:
    st.subheader("Pedidos na Separação")
    st.dataframe(df_nao_faturados[df_nao_faturados['Setor'] == "Separação"])

with abas[2]:
    st.subheader("Pedidos para Compras")
    st.dataframe(df_nao_faturados[df_nao_faturados['Setor'] == "Compras"])

with abas[3]:
    st.subheader("Pedidos em Embalagem")
    st.dataframe(df_nao_faturados[df_nao_faturados['Setor'] == "Embalagem"])

with abas[4]:
    st.subheader("Pedidos na Expedição")
    expedição_pedidos = df_nao_faturados[df_nao_faturados['Setor'] == "Expedição"]
    if expedição_pedidos.empty:
        st.write("Não há pedidos na Expedição.")
    else:
        st.dataframe(expedição_pedidos)

with abas[5]:
    st.subheader("Pedidos Sem O.E.")
    sem_oe_pedidos = df_nao_faturados[df_nao_faturados['Setor'] == "Sem O.E."]
    if sem_oe_pedidos.empty:
        st.write("Não há pedidos sem O.E.")
    else:
        st.dataframe(sem_oe_pedidos)
