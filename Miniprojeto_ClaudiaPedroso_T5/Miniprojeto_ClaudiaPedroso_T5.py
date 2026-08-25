
#SPRINT 1: IMPORTAÇÃO E EXPLORAÇÃO INICIAL

import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt
import matplolib.grid as gridspec
from datetime import datetime

#1. Importando o arquivo BaseVarejo.csv
df_vendas = pd.read_csv("BaseVarejo/BaseVarejo.csv", encoding='utf-8', sep=';')

#2. Exibição dos dados básicos (nº de registro, linhas, colunas e tipos de dados) 
print("=== SPRINT 1: DIAGNÓSTICO INICIAL ===")
print("Informações do DataFrame:")
print(f"Número de registros: {len(df_vendas)}")
print(f"Número de linhas e colunas: {df_vendas.shape}")

print("\nPrimeiras 5 linhas:")
print(df_vendas.head())

print("\nEstruturas e Tipos de Dados:")
df_vendas.info()


### SPRINT 2: DIAGNÓSTICO E FUNÇÕES DE LIMPEZA

print("\n=== SPRINT 2: DIAGNÓSTICO DE INCONSISTÊNCIAS ===")

# 1.Limpeza das colunas vazias (encontradas 4 colunas com o nome Unnamed)
df_limpo = df_vendas.drop(columns=[col for col in df_vendas.columns if 'Unnamed' in col])
print(f"Colunas vazias ('Unnamed') eliminadas: {len(df_limpo.columns) - len(df_vendas.columns)}")


#2. Mapeando valores nulos/ausentes
print(f"Número de valores nulos/ausentes por coluna:\n{nulos}")
nulos = df_limpo.isnull().sum() 

# 3. Funções com Expressões Regulares para Sanitarização
def limpar_texto_regex(texto):
  """Remove espaços extras/duplos via Regex e padroniza para maiúsculas."""
  if pd.isna(texto):
    return texto
  return re.sub(r"\s+", " ", str(texto).strip())
 

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

### SPRINT 3: LIMPEZA E TRATAMENTO DOS DADOS

print("\n=== SPRINT 3: TRATAMENTO E TRANSFORMAÇÃO ===")

# 1. Eliminação de duplicidades
qtds_duplicadas = df_limpo.duplicated().sum()
print(f"Número de registros duplicados: {qtds_duplicadas:,}")
df_limpo = df_limpo.drop_duplicates()
print(f"Linhas restantes após deduplicação: {len(df_limpo):,}")


# 2. Conversão da coluna DATA para datetime
if 'DATA' in df_limpo.columns:
    df_limpo['DATA'] = pd.to_datetime(df_limpo['DATA'], format='%d/%m/%Y', errors='coerce')
    print("Coluna 'DATA' convertida com sucesso para datetime.")


#3. Lipeza de texto com Regex nas colunas categorias e nome
for col in ["CL_SEG", "PR_CAT", "PR_NOME"]:
    if col in df_limpo.columns:
      df_limpo[col] = df_limpo[col].apply(limpar_texto_regex)
    
if "CL_GENERO" in df_limpo.columns:
    df_limpo["CL_GENERO"] = df_limpo["CL_GENERO"].apply(padronizar_genero)

# 4. Tratamento de nulos na coluna CL_FHL (Imputação pela Mediana)
if 'CL_FHL' in df_limpo.columns:
    ausentes_filhos = df_limpo['CL_FHL'].isna().sum()
    print(f"Valores ausentes em 'CL_FHL': {ausentes_filhos:,}")
    mediana_filhos = df_limpo['CL_FHL'].median()
    df_limpo['CL_FHL'] = df_limpo['CL_FHL'].fillna(mediana_filhos)
    print(f"Imputação realizada com a mediana: {mediana_filhos}")


# 5. Detectando Outliers na coluna CL_FHL (nº de filhos) usando o método IQR
Q1 = df_limpo['CL_FHL'].quantile(0.25)
Q3 = df_limpo['CL_FHL'].quantile(0.75)
IQR = Q3 - Q1
limite_superior = Q3 + 1.5 * IQR
total_outliers = (df_limpo['CL_FHL'] > limite_superior).sum()
print(f"Limite Superior (IQR): {limite_superior} | Total de Outliers: {total_outliers:,}")


#SPRINT 4: ANÁLISE ESTATÍSTICA, PERFIL DE CONSUMO E DATA VIZ

print("\n=== SPRINT 4: ESTATÍSTICA E PADRÕES DE CONSUMO ===")







### Estatística Descritiva para coluna de filhos (CL_FHL)

#CL_FHL (coluna nº de filhos) 

status_filhos = df_limpo['CL_FHL']

status_filhos ={
  "Contagem de filhos": filhos.value_counts(),
  "Média": status_filhos.mean(),   
  "Mediana": status_filhos.median(),
  "Desvio Padrão": status_filhos.std(),    
  "Mínimo": status_filhos.min(),
  "Máximo": status_filhos.max(),
  "1º Quartil": status_filhos.quantile(0.25),
  "3º Quartil": status_filhos.quantile(0.75),
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