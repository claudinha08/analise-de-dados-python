import numpy as np
import pandas as pd
import csv
import matplotlib as plt
from IPython.display import display

#importando o arquivo CSV
arquivo = "BaseVarejo/BaseVarejo.csv"
df_vendas = pd.read_csv(arquivo, sep=';')

# Exibição dos dados básicos (nº de registro, linhas, colunas e tipos de dados) 
print(f"Número de registros: {len(df_vendas)}")
print(f"Número de linhas e colunas: {df_vendas.shape}")
print("\n Colunas e Tipos de Dados:")
print(df_vendas.dtypes)
