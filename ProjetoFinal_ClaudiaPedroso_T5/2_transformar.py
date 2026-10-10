"""
2_transformar.py
----------------
Pipeline de Transformação e Carga da Camada Silver:
1. Limpa as tabelas Silver garantindo idempotência (em ordem reversa de FKs).
2. Transforma e tipa os dados da Raw para a Silver:
   - silver_viagem: conversão de datas (DD/MM/YYYY -> DATE), valores monetários
     (vírgula para ponto -> DECIMAL), cálculo de duracao_dias e valor_total.
   - silver_pagamento: tipagem de valores e vínculo por FK com silver_viagem.
   - silver_passagem: tipagem de tarifas/taxas e conversão da data de emissão.
   - silver_trecho: conversão de datas de trecho, sequencial e número de diárias.
3. Resiliente: executa em bloco de transação com rollback em caso de erro.
"""

import warnings
import pandas as pd
from psycopg2.extras import execute_values

from banco import conectar
from config import TAMANHO_BLOCO

# O Pandas avisa que prefere a biblioteca SQLAlchemy, mas funciona com psycopg2.
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")


# ---------------------------------------------------------------------------
# Funções de conversão (recebem uma coluna inteira do DataFrame)
# ---------------------------------------------------------------------------
def limpar_texto(coluna):
    """Tira os espaços das pontas. Texto vazio vira NaN (NULL no banco)."""
    coluna = coluna.str.strip()
    return coluna.where(coluna != "")


def texto_para_decimal(coluna):
    """'1.272,97' -> 1272.97. Remove ponto de milhar e troca vírgula por ponto."""
    coluna = (
        coluna.str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(coluna, errors="coerce")


def texto_para_data(coluna):
    """'17/09/2024' -> data. O format diz que vem dia/mês/ano. Texto vazio vira NaT."""
    return pd.to_datetime(coluna.str.strip(), format="%d/%m/%Y", errors="coerce")