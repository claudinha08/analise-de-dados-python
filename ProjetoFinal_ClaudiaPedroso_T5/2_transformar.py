"""
2_transformar.py
----------------
Pipeline de Transformação e Carga da Camada Silver:
- Mapeamento estrito e ordenado das colunas (Raw -> Silver).
- Tipagem rigorosa (DECIMAL, DATE, INT).
- Métricas calculadas na Silver (valor_total e duracao_dias).
- Carga em blocos com limpeza idempotente e transação protegida.
"""


import warnings
import pandas as pd
from psycopg2.extras import execute_values

from banco import conectar
from config import TAMANHO_BLOCO

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")


# ---------------------------------------------------------------------------
# Funções de limpeza e conversão de tipos
# ---------------------------------------------------------------------------
def limpar_texto(coluna):
    """Remove espaços e converte strings vazias/inválidas em None (NULL)."""
    coluna = coluna.astype(str).str.strip()
    return coluna.where(~coluna.isin(["", "None", "nan", "NULL", "-"]), None)


def texto_para_decimal(coluna):
    """Converte '1.272,97' para 1272.97. Campos nulos ou inválidos viram None."""
    coluna = (
        coluna.astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(coluna, errors="coerce")


def texto_para_data(coluna):
    """Converte 'DD/MM/AAAA' para data. Formatos inválidos viram NaT/None."""
    coluna = coluna.astype(str).str.strip()
    coluna = coluna.where(~coluna.isin(["", "None", "nan", "NULL", "-"]), None)
    return pd.to_datetime(coluna, format="%d/%m/%Y", errors="coerce")


# ---------------------------------------------------------------------------
# Configuração Unificada das Tabelas
# ---------------------------------------------------------------------------
TABELAS = [
    {
        "raw": "raw_viagem",
        "silver": "silver_viagem",
        "colunas": [
            "id_viagem", "num_proposta", "situacao", "viagem_urgente",
            "cod_orgao_superior", "nome_orgao_superior", "nome_viajante", "cargo",
            "data_inicio", "data_fim", "destinos", "motivo",
            "valor_diarias", "valor_passagens", "valor_devolucao", "valor_outros_gastos"
        ],
        "textos": [
            "id_viagem", "num_proposta", "situacao", "viagem_urgente",
            "cod_orgao_superior", "nome_orgao_superior", "nome_viajante", "cargo",
            "destinos", "motivo"
        ],
        "valores": ["valor_diarias", "valor_passagens", "valor_devolucao", "valor_outros_gastos"],
        "datas": ["data_inicio", "data_fim"],
        "inteiros": [],
    },
    {
        "raw": "raw_pagamento",
        "silver": "silver_pagamento",
        "colunas": [
            "id_viagem", "num_proposta", "nome_orgao_superior",
            "nome_ug_pagadora", "tipo_pagamento", "valor"
        ],
        "textos": [
            "id_viagem", "num_proposta", "nome_orgao_superior",
            "nome_ug_pagadora", "tipo_pagamento"
        ],
        "valores": ["valor"],
        "datas": [],
        "inteiros": [],
    },
    {
        "raw": "raw_passagem",
        "silver": "silver_passagem",
        "colunas": [
            "id_viagem", "meio_transporte",
            "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
            "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida",
            "valor_passagem", "taxa_servico", "data_emissao"
        ],
        "textos": [
            "id_viagem", "meio_transporte",
            "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
            "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida"
        ],
        "valores": ["valor_passagem", "taxa_servico"],
        "datas": ["data_emissao"],
        "inteiros": [],
    },
    {
        "raw": "raw_trecho",
        "silver": "silver_trecho",
        "colunas": [
            "id_viagem", "sequencia_trecho",
            "origem_data", "origem_uf", "origem_cidade",
            "destino_data", "destino_uf", "destino_cidade",
            "meio_transporte", "numero_diarias"
        ],
        "textos": [
            "id_viagem", "origem_uf", "origem_cidade",
            "destino_uf", "destino_cidade", "meio_transporte"
        ],
        "valores": ["numero_diarias"],
        "datas": ["origem_data", "destino_data"],
        "inteiros": ["sequencia_trecho"],
    },
]


def transformar(bloco, tabela):
    """Aplica conversões mantendo alinhamento estrito."""
    for col in tabela["textos"]:
        if col in bloco.columns:
            bloco[col] = limpar_texto(bloco[col])
            
    for col in tabela["valores"]:
        if col in bloco.columns:
            bloco[col] = texto_para_decimal(bloco[col])
            
    for col in tabela["datas"]:
        if col in bloco.columns:
            bloco[col] = texto_para_data(bloco[col])
            
    for col in tabela["inteiros"]:
        if col in bloco.columns:
            bloco[col] = pd.to_numeric(bloco[col], errors="coerce").fillna(0).astype(int)

    # Métricas calculadas para silver_viagem
    if tabela["silver"] == "silver_viagem":
        bloco["valor_total"] = (
            bloco["valor_diarias"].fillna(0)
            + bloco["valor_passagens"].fillna(0)
            + bloco["valor_outros_gastos"].fillna(0)
            - bloco["valor_devolucao"].fillna(0)
        ).round(2)
        dias = (bloco["data_fim"] - bloco["data_inicio"]).dt.days + 1
        bloco["duracao_dias"] = dias.where(dias.notna(), None)

    return bloco.astype(object).where(pd.notna(bloco), None)


def carregar_silver(conexao, tabela):
    """Lê da Raw e insere na Silver em lotes."""
    colunas_sql = ", ".join(tabela["colunas"])
    sql_select = f"SELECT {colunas_sql} FROM {tabela['raw']}"

    blocos = pd.read_sql(sql_select, conexao, chunksize=TAMANHO_BLOCO)
    cursor = conexao.cursor()
    total = 0

    for bloco in blocos:
        bloco = transformar(bloco, tabela)

        colunas_destino = list(bloco.columns)
        linhas = list(bloco.itertuples(index=False, name=None))

        sql_insert = f"INSERT INTO {tabela['silver']} ({', '.join(colunas_destino)}) VALUES %s"
        execute_values(cursor, sql_insert, linhas)

        total += len(linhas)
        print(f"   {total:,} linhas gravadas em {tabela['silver']}")

    cursor.close()
    return total


def conferir(conexao):
    """Valida paridade e integridade entre Raw e Silver."""
    cursor = conexao.cursor()

    def um_valor(sql):
        cursor.execute(sql)
        res = cursor.fetchone()
        return res[0] if res else 0

    conferencias = []
    for tabela in TABELAS:
        conferencias.append((
            f"linhas {tabela['raw']} x {tabela['silver']}",
            um_valor(f"SELECT COUNT(*) FROM {tabela['raw']}"),
            um_valor(f"SELECT COUNT(*) FROM {tabela['silver']}"),
        ))

    # Validação de datas de emissão
    conferencias.append((
        "datas de emissão vazia/inválida (Raw) x NULL (Silver)",
        um_valor("SELECT COUNT(*) FROM raw_passagem WHERE TRIM(COALESCE(data_emissao, '')) IN ('', '-', 'None', 'nan') OR data_emissao IS NULL"),
        um_valor("SELECT COUNT(*) FROM silver_passagem WHERE data_emissao IS NULL"),
    ))

    # Validação da soma monetária (tratando vírgula como ponto decimal no SQL da Raw)
    conferencias.append((
        "soma dos pagamentos Raw x Silver",
        um_valor("""
            SELECT ROUND(SUM(
                REPLACE(REPLACE(TRIM(COALESCE(valor, '0')), '.', ''), ',', '.')::NUMERIC
            ), 2)
            FROM raw_pagamento
            WHERE TRIM(COALESCE(valor, '')) NOT IN ('', '-', 'None', 'nan');
        """),
        um_valor("SELECT ROUND(SUM(valor), 2) FROM silver_pagamento;"),
    ))

    print("\nConferência Raw x Silver:")
    for descricao, origem, destino in conferencias:
        situacao = "OK" if origem == destino else "DIFERENTE!"
        print(f"   {descricao:<52} {origem} x {destino}  {situacao}")

    cursor.close()


# ---------------------------------------------------------------------------
# Execução Principal
# ---------------------------------------------------------------------------
conexao = None
try:
    conexao = conectar()
    cursor = conexao.cursor()

    print("Limpando tabelas Silver (TRUNCATE CASCADE)...")
    cursor.execute(
        "TRUNCATE silver_viagem, silver_pagamento, silver_passagem, silver_trecho RESTART IDENTITY CASCADE;"
    )
    cursor.close()

    for tabela in TABELAS:
        print(f"\nTransformando {tabela['raw']} -> {tabela['silver']}...")
        carregar_silver(conexao, tabela)

    conexao.commit()
    conferir(conexao)
    print("\n✓ Camada Silver finalizada com 100% de paridade!")

except Exception as erro:
    if conexao:
        conexao.rollback()
    print(f"\nERRO na transformação: {type(erro).__name__}: {erro}")
finally:
    if conexao:
        conexao.close()