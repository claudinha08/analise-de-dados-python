"""
2_transformar.py
----------------
Pipeline de Transformação e Carga da Camada Silver:
1. Limpa as tabelas Silver garantindo idempotência (em ordem reversa com CASCADE).
2. Transforma e tipa os dados da Raw para a Silver.
3. Resiliente: executa em bloco de transação com rollback e conferência final.
"""

import warnings
import pandas as pd
from psycopg2.extras import execute_values

from banco import conectar
from config import TAMANHO_BLOCO

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")


# ---------------------------------------------------------------------------
# Funções de conversão
# ---------------------------------------------------------------------------
def limpar_texto(coluna):
    """Tira os espaços das pontas. Texto vazio vira None (NULL no banco)."""
    coluna = coluna.str.strip()
    return coluna.where(coluna != "", None)


def texto_para_decimal(coluna):
    """'1.272,97' -> 1272.97. Remove ponto de milhar e troca vírgula por ponto."""
    coluna = (
        coluna.str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(coluna, errors="coerce")


def texto_para_data(coluna):
    """Texto DD/MM/YYYY vira data. Texto vazio vira NaT."""
    return pd.to_datetime(coluna.str.strip(), format="%d/%m/%Y", errors="coerce")


# ---------------------------------------------------------------------------
# Configuração das tabelas
# ---------------------------------------------------------------------------
TABELAS = [
    {
        "raw": "raw_viagem",
        "silver": "silver_viagem",
        "textos": [
            "id_viagem", "num_proposta", "situacao", "viagem_urgente", "cod_orgao_superior",
            "nome_orgao_superior", "nome_viajante", "cargo", "destinos", "motivo"
        ],
        "valores": ["valor_diarias", "valor_passagens", "valor_devolucao", "valor_outros_gastos"],
        "datas": ["data_inicio", "data_fim"],
        "inteiros": [],
    },
    {
        "raw": "raw_pagamento",
        "silver": "silver_pagamento",
        "textos": [
            "id_viagem",
            "num_proposta",
            "cod_orgao_superior",
            "nome_orgao_superior",
            "cod_orgao_pagador",
            "nome_orgao_pagador",
            "cod_ug_pagadora",
            "nome_ug_pagadora",
            "tipo_pagamento",
        ],
        "valores": ["valor"],
        "datas": [],
        "inteiros": [],
    },
    {
        "raw": "raw_passagem",
        "silver": "silver_passagem",
        "textos": [
            "id_viagem", "meio_transporte", "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
            "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida"
        ],
        "valores": ["valor_passagem", "taxa_servico"],
        "datas": ["data_emissao"],
        "inteiros": [],
    },
    {
        "raw": "raw_trecho",
        "silver": "silver_trecho",
        "textos": ["id_viagem", "origem_uf", "origem_cidade", "destino_uf", "destino_cidade", "meio_transporte"],
        "valores": ["numero_diarias"],
        "datas": ["origem_data", "destino_data"],
        "inteiros": ["sequencia_trecho"],
    },
]


def transformar(bloco, tabela):
    """Converte um bloco da Raw. Na viagem, calcula valor_total e duracao_dias."""
    for coluna in tabela["textos"]:
        bloco[coluna] = limpar_texto(bloco[coluna])
    for coluna in tabela["valores"]:
        bloco[coluna] = texto_para_decimal(bloco[coluna])
    for coluna in tabela["datas"]:
        bloco[coluna] = texto_para_data(bloco[coluna])
    for coluna in tabela["inteiros"]:
        bloco[coluna] = pd.to_numeric(bloco[coluna], errors="coerce", downcast="integer")

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
    """Lê a Raw em blocos, transforma e grava na Silver garantindo mapeamento nominal das colunas."""
    colunas_origem = tabela["textos"] + tabela["valores"] + tabela["datas"] + tabela["inteiros"]
    sql_select = f"SELECT {', '.join(colunas_origem)} FROM {tabela['raw']}"
    
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
    """Compara Raw x Silver: contagem de registros, nulos e soma financeira."""
    cursor = conexao.cursor()

    def um_valor(sql):
        cursor.execute(sql)
        return cursor.fetchone()[0]

    conferencias = []
    for tabela in TABELAS:
        conferencias.append((
            f"linhas {tabela['raw']} x {tabela['silver']}",
            um_valor(f"SELECT COUNT(*) FROM {tabela['raw']}"),
            um_valor(f"SELECT COUNT(*) FROM {tabela['silver']}"),
        ))

    conferencias.append((
        "datas de emissão vazia (Raw) x NULL (Silver)",
        um_valor("SELECT COUNT(*) FROM raw_passagem WHERE data_emissao = '' OR data_emissao IS NULL"),
        um_valor("SELECT COUNT(*) FROM silver_passagem WHERE data_emissao IS NULL"),
    ))
    conferencias.append((
        "soma dos pagamentos Raw x Silver",
        um_valor("SELECT SUM(REPLACE(NULLIF(valor, ''), ',', '.')::NUMERIC) FROM raw_pagamento"),
        um_valor("SELECT SUM(valor) FROM silver_pagamento"),
    ))

    print("\nConferência Raw x Silver:")
    for descricao, origem, destino in conferencias:
        situacao = "OK" if origem == destino else "DIFERENTE!"
        print(f"   {descricao:<48} {origem} x {destino}  {situacao}")

    cursor.close()


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
conexao = None
try:
    conexao = conectar()
    cursor = conexao.cursor()

    # Esvazia a Silver garantindo idempotência
    cursor.execute(
        "TRUNCATE silver_viagem, silver_pagamento, silver_passagem, silver_trecho RESTART IDENTITY CASCADE;"
    )
    cursor.close()

    for tabela in TABELAS:
        print(f"\nTransformando {tabela['raw']} -> {tabela['silver']}...")
        carregar_silver(conexao, tabela)

    conexao.commit()
    conferir(conexao)
    print("\n✓ Camada Silver finalizada com sucesso!")
except Exception as erro:
    if conexao:
        conexao.rollback()
    print(f"\nERRO na transformação: {type(erro).__name__}: {erro}")
finally:
    if conexao:
        conexao.close()