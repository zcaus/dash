import pandas as pd

# Carregar as duas planilhas em DataFrames
planilha1 = pd.read_excel("planilha/PEDIDOS_VOLPE8.XLSX", sheet_name="Planilha1")
planilha2 = pd.read_excel("planilha/ABASTECIDOS.XLSX", sheet_name="Planilha2")

# Filtrar linhas em planilha1 com Nr.pedido contendo hífen (-)
planilha1_com_hifen = planilha1[planilha1['Nr.pedido'].str.contains('-')]
planilha1_sem_hifen = planilha1[~planilha1['Nr.pedido'].str.contains('-')]

# Mesclar planilha1_com_hifen com planilha2 com base em colunas comuns
colunas_comuns = ["Ped. Cliente", "Modelo", "Produto"]  # Nomes das colunas que são iguais em ambas as planilhas
planilha_mesclada_com_hifen = pd.merge(planilha1_com_hifen, planilha2, on=colunas_comuns, how="outer", suffixes=('_planilha1', '_planilha2'))

# Concatenar planilha_mesclada_com_hifen com planilha1_sem_hifen
planilha_mesclada = pd.concat([planilha_mesclada_com_hifen, planilha1_sem_hifen]).reset_index(drop=True)

# Salvar a planilha mesclada em formato Excel
with pd.ExcelWriter("planilha/controledosistema.xlsx", engine='openpyxl', mode='w') as writer:
    planilha_mesclada.to_excel(writer, index=False, sheet_name='Planilha1')

print("Planilha mesclada criada com sucesso.")