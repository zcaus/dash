import pandas as pd

# Carregar as duas planilhas em DataFrames
planilha1 = pd.read_excel("planilha/PEDIDOS_VOLPE8.XLSX", sheet_name="Planilha1")  # Altere para o nome correto
planilha2 = pd.read_excel("planilha/ABASTECIDOS.XLSX", sheet_name="Planilha2")  # Altere para o nome correto

# Mesclar as planilhas com base em duas colunas comuns
colunas_comuns = ["Ped. Cliente", "Modelo", "Produto"]  # Nomes das colunas que são iguais em ambas as planilhas
planilha_mesclada = pd.merge(planilha1, planilha2, on=colunas_comuns, how="outer", suffixes=('_planilha1', '_planilha2'))

# Salvar a planilha mesclada em formato Excel
with pd.ExcelWriter("planilha/pp.xlsx", engine='openpyxl') as writer:
    planilha_mesclada.to_excel(writer, index=False, sheet_name='Planilha1')

print("Planilha mesclada criada com sucesso em formato XLSX.")
