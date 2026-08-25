
#SPRINT 1: IMPORTAÇÃO E EXPLORAÇÃO INICIAL

import numpy as np
import pandas as pd
import re
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
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
nulos = df_limpo.isnull().sum() 
print(f"Número de valores nulos/ausentes por coluna:\n{nulos}")

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


# 1. Tabela Estatística Descritiva da Coluna CL_FHL

serie_filhos = df_limpo['CL_FHL']

status_filhos ={
  "Contagem de filhos": serie_filhos.value_counts(),
  "Média": serie_filhos.mean(),   
  "Mediana": serie_filhos.median(),
  "Desvio Padrão": serie_filhos.std(),    
  "Mínimo": serie_filhos.min(),
  "Máximo": serie_filhos.max(),
  "1º Quartil": serie_filhos.quantile(0.25),
  "3º Quartil": serie_filhos.quantile(0.75),
}

df_stats = pd.DataFrame(
    list(status_filhos.items()), columns=['Parâmetro Estatístico', 'Valor'])

print("\nTabela Estatística Descritiva da Coluna 'CL_FHL' (Número de Filhos)")
print(df_stats.to_string(index=False))


#2. Criação da Faixa Familiar (Perfil de Consumo) com base na quantidade de filhos
df_limpo['PERFIL_FAMILIA'] = df_limpo['CL_FHL'].apply(
    lambda x: 'Sem Filhos' if x == 0 else ('Com Filhos' if x > 0 else 'Não Informado') 
)

#3. Cruzamento: Categorias Mais Consumidas por Perfil Familiar 
if 'RP_CAT' in df_limpo.columns:
    consumo_perfil = pd.crosstab(
      df_limpo['PR_CAT'],
      df_limpo['PERFIL_FAMILIA'],
      normalize='columns')* 100
    print('\n % de Consumo por Categoria e Perfil Familiar:')
    print(consumo_perfil.round(2))
    
# Agrupamento por gênero: Total de Compras e Média de Filhos por Gênero (Groupby)
if "CL_GENERO" in df_limpo.columns and "CO_ID" in df_limpo.columns:
    agrup_genero = df_limpo.groupby("CL_GENERO").agg(
        Total_Transacoes=("CO_ID", "count"),
        Media_Filhos=("CL_FHL", "mean"),
    ).reset_index()
    print("\nAgrupamento por Gênero: Total de Compras e Média de Filhos")
    print(agrup_genero.to_string(index=False))

## 5. Visualização Gráfica

## 1. Distribuição de clientes por número de filhos
fig = plt.figure(figsize=(14, 7), dpi=100)
gs = gridspec.GridSpec(2, 2, width_ratios=[1.8, 1], height_ratios=[1, 1])

serie = df_limpo['CL_FHL']
ax_bar = fig.add_subplot(gs[:, 0])

contagem = serie.value_counts().sort_index()
cores = ['#8cb8d6', '#a58aa5', '#a1d49b', '#b58273', '#e89898']

barras = ax_bar.bar(contagem.index.astype(str), contagem.values, color=cores, edgecolor='gray', width=0.7)

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

ax_bar.set_title("DISTRIBUIÇÃO DE CLIENTES POR NÚMERO DE FILHOS ('CL_FHL')",
    fontsize=12,
    fontweight='bold',
)
ax_bar.set_xlabel('NÚMERO DE FILHOS', 
    fontsize=11)
ax_bar.set_ylabel('NÚMERO DE CLIENTES', 
    fontsize=11)
ax_bar.grid(True, 
    linestyle='-', 
    alpha=0.6)
fig.tight_layout()
fig.savefig("distribuicao_clientes_filhos.png", dpi=150)


# Gráfico 2: Top Categorias por Perfil Familiar
if 'PR_CAT' in df_limpo.columns:
    top_cats = df_limpo['PR_CAT'].value_counts().head(6).index
    df_top_cats = df_limpo[df_limpo['PR_CAT'].isin(top_cats)]
    
    tabela_plot = pd.crosstab(df_top_cats['PR_CAT'], df_top_cats['PERFIL_FAMILIA'])
    
    fig2, ax2 = plt.subplots(figsize=(10, 5), dpi=100)
    tabela_plot.plot(kind='bar', ax=ax2, colormap='viridis', edgecolor='black', width=0.7)
    ax2.set_title("TOP CATEGORIAS DE PRODUTOS POR PERFIL FAMILIAR", fontsize=11, fontweight='bold')
    ax2.set_xlabel("Categoria de Produto")
    ax2.set_ylabel("Quantidade de Transações")
    ax2.legend(title="Perfil Familiar")
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    plt.xticks(rotation=45, ha='right')
    fig2.tight_layout()
    fig2.savefig("consumo_categoria_perfil.png", dpi=150)
    
    

# Gráfico 3: Comparativo Média e mediana 

media = serie.mean()
mediana = serie.median()

fig3, ax3 = plt.subplots(figsize=(8, 5), dpi=100)
metricas = ['Média', 'Mediana']
valores = [serie_filhos.mean(), serie_filhos.median()]
cores = ['#2b5c8f', '#e26d5c']
barras3 = ax3.bar(metricas, valores, color=cores, width=0.4, edgecolor='black')

# Exibir os valores numéricos em cima de cada barra
for barra in barras3:
  altura = barra.get_height()
  ax3.annotate(
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
ax3.set_title("Comparativo: Média vs Mediana (Coluna 'CL_FHL')",
    fontsize=13,
    fontweight='bold',
)
ax3.set_ylabel('Valor', fontsize=11)
ax3.set_ylim(0, max(valores) * 1.3)  # Espaço para o rótulo
ax3.grid(axis='y', linestyle='--', alpha=0.7)

# Salvar na pasta 'Graficos'
fig3.savefig("comparativo_media_mediana.png", dpi=150)


plt.show()