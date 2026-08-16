
#SPRINT 1: IMPORTAÇÃO E EXPLORAÇÃO INICIAL

import numpy as np
import pandas as pd
import re
import matplotlib as plt
from IPython.display import display
from datetime import datetime

#Importando o arquivo BaseVarejo.csv
df_vendas = pd.read_csv("BaseVarejo/BaseVarejo.csv", encoding='utf-8', sep=';')

# Exibição dos dados básicos (nº de registro, linhas, colunas e tipos de dados) 
print(f"Número de registros: {len(df_vendas)}")
print(f"Número de linhas e colunas: {df_vendas.shape}")

print("\nPrimeiras 5 linhas:")
display(df_vendas.head())
display(df_vendas.tail())
df_vendas.info()

### SPRINT 2: DIAGNÓSTICO E FUNÇÕES DE LIMPEZA

### Inconsistências de dados

# 1.Limpeza das colunas vazias (encontradas 4 colunas com o nome Unnamed)
df_limpo = df_vendas.drop(columns=[col for col in df_vendas.columns if 'Unnamed' in col])
print(f"Colunas vazias ('Unnamed') eliminadas: {len(df_limpo.columns) - len(df_vendas.columns)}")

display(df_limpo.tail())

#2. Procurar valores nulos/ausentes
nulos =df_limpo.isnull().sum() 
print(f"Número de valores nulos/ausentes por coluna:\n{nulos}")



### SPRINT 3: LIMPEZA E TRATAMENTO DOS DADOS

# 1. Identificando duplicidades
print(f"Número de registros duplicados: {df_limpo.duplicated().sum()}")


# 2. Detectando Outliers na coluna CL_FHL (nº de filhos) usando o método IQR
Q1 = df_limpo['CL_FHL'].quantile(0.25)
Q3 = df_limpo['CL_FHL'].quantile(0.75)
IQR = Q3 - Q1
limite_superior = Q3 + 1.5 * IQR
print(f"Limite superior: {limite_superior}")


# 3. Funções com Expressões Regulares para Sanitarização
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

# 1. Eliminar duplicatas relevantes
df_limpo = df_limpo.drop_duplicates()
print(f"Registros duplicados eliminados. Linhas restantes: {len(df_limpo)}")
display(df_limpo.shape)

# 2. Verificando valores ausentes na coluna CL_FHL (nº de filhos)
display(df_limpo['CL_FHL'].describe(), df_limpo['CL_FHL'].value_counts())
ausentes_filhos =df_limpo['CL_FHL'].isna().sum()
print(f"Número de valores ausentes na coluna CL_FHL: {ausentes_filhos}")

# 3. Detectando Outliers na coluna CL_FHL (nº de filhos) usando o método IQR
Q1 = df_limpo['CL_FHL'].quantile(0.25)
Q3 = df_limpo['CL_FHL'].quantile(0.75)
IQR = Q3 - Q1

limite_superior = Q3 + 1.5 * IQR
print(f"Limite superior: {limite_superior}")

#contar registro acima do limite superior
limite_superior_contagem = df_limpo[df_limpo['CL_FHL']> limite_superior]
print(f"Total de registro acima do limite: {len(limite_superior_contagem)}")

#4. Converter DATA para o tipo datetime com correção de erros
df_limpo['DATA'] = pd.to_datetime(df_limpo['DATA'], format='%d/%m/%Y', errors='coerce')

#3. Lipeza de texto com Regex nas colunas categorias e nome
for col in ["CL_SEG", "PR_CAT", "PR_NOME"]:
    df_limpo[col] = df_limpo[col].apply(limpar_texto_regex)

df_limpo["CL_GENERO"] = df_limpo["CL_GENERO"].apply(padronizar_genero)


### Estatística Descritiva para coluna de filhos (CL_FHL)

#CL_FHL (coluna nº de filhos) 

status_filhos = df_limpo['CL_FHL']

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

print("\nAgrupamento 1: Padrão de Compras por Gênero (groupby)")
print(agrup_genero.to_string(index=False))

## Gráfico de barras para distribuição de clientes por número de filhos

import matplotlib.gridspec as gridspec ##procurei por itens de layout para gráfico e usei esse para melhorar a aparencia do gráfico

fig = plt.figure(figsize=(14, 7), dpi=100)
gs = gridspec.GridSpec(2, 2, width_ratios=[1.8, 1], height_ratios=[1, 1])

serie = df_limpo['CL_FHL']
ax_bar = fig.add_subplot(gs[:, 0])

contagem = serie.value_counts().sort_index()
cores = ['#8cb8d6', '#a58aa5', '#a1d49b', '#b58273', '#e89898']

barras = ax_bar.bar(
    contagem.index.astype(str),
    contagem.values,
    color=cores,
    edgecolor='gray',
    width=0.7,
)

# Rótulos de dados sobre as barras
for bar in barras:
  altura = bar.get_height()
  ax_bar.annotate(
      f'{int(altura):,}',
      xy=(bar.get_x() + bar.get_width() / 2, altura),
      xytext=(0, 4),
      textcoords='offset points',
      ha='center',
      va='bottom',
      fontsize=10,
  )

ax_bar.set_title(
    "DISTRIBUIÇÃO DE CLIENTES POR NÚMERO DE FILHOS ('CL_FHL')",
    fontsize=12,
    fontweight='bold',
)
ax_bar.set_xlabel('NÚMERO DE FILHOS', fontsize=11)
ax_bar.set_ylabel('NÚMERO DE CLIENTES', fontsize=11)
ax_bar.grid(True, linestyle='-', alpha=0.6)

fig.savefig("distribuicao_clientes_filhos.png", dpi=150)

## Média e mediana da distruiçao de quantidade de filhos

##calculos
media = serie.mean()
mediana = serie.median()

##configuração gráfica

fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

metricas = ['Média', 'Mediana']
valores = [media, mediana]
cores = ['#2b5c8f', '#e26d5c']

barras = ax.bar(metricas, valores, color=cores, width=0.4, edgecolor='black')

# Exibir os valores numéricos em cima de cada barra
for barra in barras:
  altura = barra.get_height()
  ax.annotate(
      f'{altura:.2f}',
      xy=(barra.get_x() + barra.get_width() / 2, altura),
      xytext=(0, 5),
      textcoords='offset points',
      ha='center',
      va='bottom',
      fontsize=12,
      fontweight='bold',
  )

# Ajustes visuais
ax.set_title(
    "Comparativo: Média vs Mediana (Coluna 'CL_FHL')",
    fontsize=13,
    fontweight='bold',
)
ax.set_ylabel('Valor', fontsize=11)
ax.set_ylim(0, max(valores) * 1.3)  # Espaço para o rótulo
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 4. Salvar na pasta 'Graficos'
fig.savefig("distribuicao_qtd_filhos.png", dpi=150)


plt.show()