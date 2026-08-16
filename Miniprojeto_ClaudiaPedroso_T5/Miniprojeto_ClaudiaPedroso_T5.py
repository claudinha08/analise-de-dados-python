
#SPRINT 1: IMPORTAÇÃO E EXPLORAÇÃO INICIAL

import numpy as np
import pandas as pd
import re
import matplotlib as plt
from IPython.display import display
from datetime import datetime

#Importando o arquivo BaseVarejo.csv
df_vendas = pd.read_csv("BaseVarejo/BaseVarejo.csv", sep=';')

# Exibição dos dados básicos (nº de registro, linhas, colunas e tipos de dados) 
print(f"Número de registros: {len(df_vendas)}")
print(f"Número de linhas e colunas: {df_vendas.shape}")

print("\nPrimeiras 5 linhas:")
print(df_vendas.head())

### SPRINT 2: DIAGNÓSTICO E FUNÇÕES DE LIMPEZA

# 1.Limpeza das colunas vazias (encontradas 4 colunas com o nome Unnamed)
df_limpo = df_vendas.drop(columns=[col for col in df_vendas.columns if 'Unnamed' in col])
print(f"Colunas vazias ('Unnamed') eliminadas: {len(df_limpo.columns) - len(df_vendas.columns)}")

display(df_limpo.info())

### Inconsistências de dados

#2. Procurar valores nulos 
nulos =df_limpo.isnull().sum() 
print(f"Número de valores nulos por coluna:\n{nulos}")


### SPRINT 3: LIMPEZA E TRATAMENTO DOS DADOS

#1. Identificando duplicidades
print(f"Número de registros duplicados: {df_limpo.duplicated().sum()}")
# Remoção de duplicatas exatas
df_limpo = df_limpo.drop_duplicates().reset_index(drop=True)


#2. Checagem das datas inválidas
colunas_data = [c for c in df_limpo.columns if "data" in c.lower() or "date" in c.lower()]
for col in colunas_data:
    df_limpo[col] = pd.to_datetime(df_limpo[col], errors="coerce", dayfirst=True)

# 5. Funções com Expressões Regulares para Sanitarização
def limpar_texto_regex(texto):
  """Remove espaços extras/duplos via Regex e padroniza para maiúsculas."""
  if pd.isna(texto):
    return texto
  texto_limpo = re.sub(r"\s+", " ", str(texto).strip())
  return texto_limpo.upper()


def padronizar_genero(val):
  """Padroniza entradas categóricas desordenadas de gênero."""
  if pd.isna(val):
    return "NÃO INFORMADO"
  val_clean = str(val).strip().upper()
  if val_clean in ["M", "MASCULINO"]:
    return "MASCULINO"
  elif val_clean in ["F", "FEMININO"]:
    return "FEMININO"
  return val_clean

### Tratamento de Nulos, Duplicatas e Ajuste de tipos

#1. Eliminar duplicatas relevantes
df_limpo = df_limpo.drop_duplicates()
print(f"Registros duplicados eliminados. Linhas restantes: {len(df_limpo)}")

#2. Converter DATA para o tipo datetime com correção de erros
df_limpo['DATA'] = pd.to_datetime(df_limpo['DATA'], format='%d/%m/%Y', errors='coerce')

#3. Lipeza de texto com Regex nas colunas categorias e nome
for col in ["CL_SEG", "PR_CAT", "PR_NOME"]:
    df_limpo[col] = df_limpo[col].apply(limpar_texto_regex)

df_limpo["CL_GENERO"] = df_limpo["CL_GENERO"].apply(padronizar_genero)


### Estatística Descritiva para coluna de filhos (CL_FHL)

# 1. Garantir que a coluna de filhos seja NUMÉRICA (int ou float)
df_limpo['CL_FHL'] = pd.to_numeric(df_limpo['CL_FHL'], errors='coerce')

#CL_FHL (coluna nº de filhos) - utilizarei a mediana para não sofrer com outliers
mediana_filhos = df_limpo['CL_FHL'].median()
print(f"Mediana do número de filhos: {mediana_filhos}")

filhos = df_limpo['CL_FHL']

status_filhos ={
  "Contagem de filhos": filhos.value_counts(),
  "Média": filhos.mean(),   
  "Mediana": filhos.median(),
  "Desvio Padrão": filhos.std(),    
  "Mínimo": filhos.min(),
  "Máximo": filhos.max(),
  "1º Quartil": filhos.quantile(0.25),
  "3º Quartil": filhos.quantile(0.75),
}

df_stats = pd.DataFrame(
    list(status_filhos.items()), columns=['Parâmetro Estatístico', 'Valor']
)
print(df_stats.to_string(index=False))

# Agrupamento 1: Total de Compras e Média de Filhos por Gênero (Groupby)
agrup_genero = (
    df_limpo.groupby("CL_GENERO")
    .agg(
        Total_Transacoes=("CO_ID", "count"),
        Media_Filhos=("CL_FHL", "mean"),
    )
    .reset_index()
)

print("\n--- Agrupamento 1: Padrão de Compras por Gênero (groupby) ---")
print(agrup_genero.to_string(index=False))