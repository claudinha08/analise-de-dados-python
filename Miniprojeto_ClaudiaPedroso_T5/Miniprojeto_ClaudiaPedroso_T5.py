import numpy as np
import pandas as pd
import csv
import matplotlib as plt

#importando o arquivo CSV
df_vendas = pd.read_csv("BaseVarejo/BaseVarejo.csv")

# Exibição dos parâmetros básicos solicitados
print(f"Número de registros (linhas) : {df_vendas.shape[0]}")
print(f"Número de colunas            : {df_vendas.shape[1]}")
print("Colunas e Tipos de Dados Originais:")
print(df_vendas.dtypes)
print("Primeiras 5 linhas do dataset:")
print(df_vendas.head())


