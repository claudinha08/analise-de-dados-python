import os
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Analytics Varejo | Dashboard Executivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# LOCALIZAÇÃO DINÂMICA DO ARQUIVO CSV
# ==============================================================================
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))

# Tenta encontrar o arquivo tanto na mesma pasta quanto em subpastas
caminhos_possiveis = [
    os.path.join(DIRETORIO_SCRIPT, "BaseVarejo", "BaseVarejo.csv"),
    os.path.join(DIRETORIO_SCRIPT, "BaseVarejo.csv"),
    os.path.join(DIRETORIO_SCRIPT, "..", "BaseVarejo", "BaseVarejo.csv"),
    os.path.join(DIRETORIO_SCRIPT, "..", "BaseVarejo.csv"),
]

CAMINHO_FINAL = None
for c in caminhos_possiveis:
    if os.path.exists(c):
        CAMINHO_FINAL = c
        break
    
# ==============================================================================
# RESOLUÇÃO DO CAMINHO DO CSV USANDO PATHLIB
# ==============================================================================
PASTA_ATUAL = Path(__file__).resolve().parent

caminhos_possiveis = [
    PASTA_ATUAL / "BaseVarejo" / "BaseVarejo.csv",
    PASTA_ATUAL / "BaseVarejo.csv",
    PASTA_ATUAL.parent / "BaseVarejo" / "BaseVarejo.csv",
    PASTA_ATUAL.parent / "BaseVarejo.csv",
]

CAMINHO_FINAL = None
for caminho in caminhos_possiveis:
    if caminho.exists():
        CAMINHO_FINAL = caminho
        break
# ==============================================================================
# CARGA E TRATAMENTO DE DADOS (COM CACHE)
# ==============================================================================
@st.cache_data
def carregar_e_tratar_dados():
    # Carrega a base de dados com o caminho resolvido
    df = pd.read_csv(CAMINHO_FINAL, encoding="utf-8", sep=";")
    
    # 1. Remover colunas 'Unnamed'
    colunas_unnamed = [col for col in df.columns if "Unnamed" in col]
    df = df.drop(columns=colunas_unnamed)
    
    # 2. Deduplicação
    df = df.drop_duplicates()
    
    # 3. Tratamento de Datas
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
        
    # 4. Limpeza com Regex
    def limpar_texto(texto):
        if pd.isna(texto):
            return texto
        return re.sub(r"\s+", " ", str(texto).strip()).upper()

    def padronizar_gen(val):
        if pd.isna(val):
            return "NÃO INFORMADO"
        val_clean = str(val).strip().upper()
        if val_clean in ["M", "MASCULINO"]:
            return "MASCULINO"
        elif val_clean in ["F", "FEMININO"]:
            return "FEMININO"
        return val_clean

    for col in ["CL_SEG", "PR_CAT", "PR_NOME"]:
        if col in df.columns:
            df[col] = df[col].apply(limpar_texto)
            
    if "CL_GENERO" in df.columns:
        df["CL_GENERO"] = df["CL_GENERO"].apply(padronizar_gen)

    # 5. Tratamento de Filhos (CL_FHL)
    if "CL_FHL" in df.columns:
        mediana_filhos = df["CL_FHL"].median()
        df["CL_FHL"] = df["CL_FHL"].fillna(mediana_filhos)
        df["PERFIL_FAMILIA"] = df["CL_FHL"].apply(
            lambda x: "Sem Filhos" if x == 0 else ("1 a 2 Filhos" if x <= 2 else "3 ou Mais Filhos")
        )
        
    return df

df_raw = carregar_e_tratar_dados()

# ==============================================================================
# BARRA LATERAL: FILTROS INTERATIVOS
# ==============================================================================
st.sidebar.title("🎛️ Filtros de Análise")

# Filtro de Gênero
generos_disponiveis = sorted(df_raw["CL_GENERO"].unique().tolist()) if "CL_GENERO" in df_raw.columns else []
generos_selecionados = st.sidebar.multiselect(
    "Gênero do Cliente:",
    options=generos_disponiveis,
    default=generos_disponiveis
)

# Filtro de Perfil Familiar
perfis_disponiveis = sorted(df_raw["PERFIL_FAMILIA"].unique().tolist()) if "PERFIL_FAMILIA" in df_raw.columns else []
perfis_selecionados = st.sidebar.multiselect(
    "Perfil Familiar:",
    options=perfis_disponiveis,
    default=perfis_disponiveis
)

# Filtro de Categoria
if "PR_CAT" in df_raw.columns:
    categorias_disponiveis = sorted(df_raw["PR_CAT"].dropna().unique().tolist())
    categorias_selecionadas = st.sidebar.multiselect(
        "Categorias de Produtos:",
        options=categorias_disponiveis,
        default=categorias_disponiveis[:5] if len(categorias_disponiveis) >= 5 else categorias_disponiveis
    )
else:
    categorias_selecionadas = []

# Aplicação dos filtros
df_filtrado = df_raw.copy()
if generos_selecionados:
    df_filtrado = df_filtrado[df_filtrado["CL_GENERO"].isin(generos_selecionados)]
if perfis_selecionados:
    df_filtrado = df_filtrado[df_filtrado["PERFIL_FAMILIA"].isin(perfis_selecionados)]
if categorias_selecionadas and "PR_CAT" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["PR_CAT"].isin(categorias_selecionadas)]

# ==============================================================================
# CABEÇALHO & MÉTRICAS PRINCIPAIS (KPIS)
# ==============================================================================
st.title("🛍️ Painel Executivo de Vendas & Perfil de Consumo")
st.markdown("Diagnóstico de comportamento de compra, volumetria transacional e segmentação demográfica de clientes.")

col1, col2, col3, col4 = st.columns(4)

total_transacoes = len(df_filtrado)
media_filhos = df_filtrado["CL_FHL"].mean() if "CL_FHL" in df_filtrado.columns else 0
mediana_filhos = df_filtrado["CL_FHL"].median() if "CL_FHL" in df_filtrado.columns else 0
top_categoria = df_filtrado["PR_CAT"].mode()[0] if "PR_CAT" in df_filtrado.columns and not df_filtrado.empty else "N/A"

col1.metric("Total de Registros", f"{total_transacoes:,}")
col2.metric("Média de Filhos", f"{media_filhos:.2f}")
col3.metric("Mediana de Filhos", f"{mediana_filhos:.0f}")
col4.metric("Top Categoria", str(top_categoria))

st.divider()

# ==============================================================================
# ABAS VISUAIS
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["👥 Perfil Demográfico", "📦 Consumo & Categorias", "📋 Tabela de Dados"])

with tab1:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Distribuição por Número de Filhos")
        contagem_filhos = df_filtrado["CL_FHL"].value_counts().reset_index()
        contagem_filhos.columns = ["Numero_Filhos", "Total_Clientes"]
        contagem_filhos["Numero_Filhos"] = contagem_filhos["Numero_Filhos"].astype(str)
        
        fig_filhos = px.bar(
            contagem_filhos,
            x="Numero_Filhos",
            y="Total_Clientes",
            text="Total_Clientes",
            color="Numero_Filhos",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={"Numero_Filhos": "Qtd. Filhos", "Total_Clientes": "Clientes"}
        )
        fig_filhos.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_filhos.update_layout(showlegend=False, yaxis_title="Total de Clientes", height=400)
        st.plotly_chart(fig_filhos, use_container_width=True)

    with col_g2:
        st.subheader("Distribuição por Gênero")
        if "CL_GENERO" in df_filtrado.columns:
            fig_genero = px.pie(
                df_filtrado,
                names="CL_GENERO",
                hole=0.45,
                color_discrete_sequence=["#2b5c8f", "#e26d5c", "#8cb8d6"]
            )
            fig_genero.update_traces(textinfo="percent+label")
            fig_genero.update_layout(height=400)
            st.plotly_chart(fig_genero, use_container_width=True)

with tab2:
    st.subheader("Top Categorias de Produtos por Perfil Familiar")
    if "PR_CAT" in df_filtrado.columns:
        agrup_cat = df_filtrado.groupby(["PR_CAT", "PERFIL_FAMILIA"]).size().reset_index(name="Transacoes")
        fig_cat = px.bar(
            agrup_cat,
            x="PR_CAT",
            y="Transacoes",
            color="PERFIL_FAMILIA",
            barmode="group",
            color_discrete_sequence=px.colors.sequential.Viridis,
            labels={"PR_CAT": "Categoria", "Transacoes": "Quantidade de Vendas", "PERFIL_FAMILIA": "Perfil"}
        )
        fig_cat.update_layout(xaxis_tickangle=-30, height=450)
        st.plotly_chart(fig_cat, use_container_width=True)

with tab3:
    st.subheader("Amostra dos Dados Tratados")
    st.dataframe(df_filtrado.head(100), use_container_width=True)
    
    csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Dados Filtrados (CSV)",
        data=csv_data,
        file_name="varejo_filtrado.csv",
        mime="text/csv"
    )