"""
1_extrair.py
------------
Pipeline de Extração e Camada Raw:
1. Baixa o .zip com os dados de 2025 do Google Drive 
2. Descompacta os 4 CSVs na pasta 'data/'.
3. Trunca as tabelas Raw (garantindo idempotência sem duplicar dados).
4. Lê os CSVs em blocos (chunks) e faz a carga bruta nas tabelas raw_* via inserir_em_lote.
"""

import os
import zipfile
import requests
import pandas as pd
import io

from banco import conectar
from config import (ARQUIVOS, CSV_ENCODING, CSV_SEPARADOR, DRIVE_FILE_ID, PASTA_DADOS, TAMANHO_BLOCO)

#---------------------------------------------------------------
#Dowload do .zip do Google Drive e descompacta os CSVs em data/
#---------------------------------------------------------------

def baixar_dados():
    
    ##Baixa o .zip do Drive e descompacta os CSVs em data/ (só se ainda não existirem)
    try:
         nomes = [dados["csv"] for dados in ARQUIVOS.values()]
         if all((PASTA_DADOS / nome).exists() for nome in nomes):
            print("Os 4 CSVs já estão em data/. Não é preciso baixar de novo.")
            return

         if DRIVE_FILE_ID.startswith("1R6re1574aCeqNfwJXQ_T7BwHCEsPfgvc"):
            raise RuntimeError("Cole o ID do arquivo do Drive na variável DRIVE_FILE_ID do config.py.")

         PASTA_DADOS.mkdir(exist_ok=True)
         caminho_zip = PASTA_DADOS / "viagens.zip"
         url = f"https://drive.usercontent.google.com/download?id={DRIVE_FILE_ID}&export=download&confirm=t"

         print("Baixando o zip do Google Drive...")
         resposta = requests.get(url, stream=True, timeout=60)
         resposta.raise_for_status()
    
         with open(caminho_zip, "wb") as arquivo:
            for pedaco in resposta.iter_content(chunk_size=1024 * 1024):
                arquivo.write(pedaco)

         if not zipfile.is_zipfile(caminho_zip):
            raise RuntimeError(
                "O arquivo baixado não é um .zip. Confira se o link do Drive está compartilhado "
                "como 'Qualquer pessoa com o link'."
            )

            with zipfile.ZipFile(caminho_zip) as pacote:
                pacote.extractall(PASTA_DADOS)

            # Se o zip trouxe uma subpasta, traz os CSVs para dentro de data/
            for pasta, _, arquivos in os.walk(PASTA_DADOS):
              for nome in arquivos:
                 if nome.endswith(".csv") and pasta != str(PASTA_DADOS):
                      os.replace(os.path.join(pasta, nome), PASTA_DADOS / nome)

            print("CSVs prontos em data/.")
        
    except requests.exceptions.RequestException as erro_rede:
        print(f"ERRO de rede ao baixar os dados: {erro_rede}")
        raise
    except zipfile.BadZipFile as erro_zip:
        print(f"ERRO de integridade no arquivo compactado: {erro_zip}")
        raise
    except Exception as erro:
        print(f"ERRO inesperado na fase de obtenção dos dados: {type(erro).__name__}: {erro}")
        raise

#--------------------
#Carga na camada Raw
#--------------------

## Muito erro na leitura das colunas e dados, corrigindo para usar COPY do PostgreSQL
def obter_colunas_tabela(conexao, tabela):
    """Consulta as colunas existentes na tabela do PostgreSQL em ordem."""
    with conexao.cursor() as cur:
        cur.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
            """,
            (tabela.lower(),),
        )
        return [r[0] for r in cur.fetchall()]


def carregar_raw(conexao, nome_csv, tabela):
    
    caminho_csv = PASTA_DADOS / nome_csv
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {caminho_csv}")
    
    ##tentei com INSERT em lote, mas deu erro. 
    cursor = conexao.cursor()
    try:
        cursor.execute(f"TRUNCATE {tabela}")  # Idempotência

        caminho_csv = PASTA_DADOS / nome_csv
        colunas_banco = obter_colunas_tabela(conexao, tabela)

        # Lê apenas o cabeçalho para mapear as colunas
        df_head = pd.read_csv(
            caminho_csv,
            sep=CSV_SEPARADOR,
            encoding=CSV_ENCODING,
            nrows=0,
            )

         # Se a quantidade de colunas do CSV for exatamente igual à da tabela, usa COPY direto do arquivo
        if len(df_head.columns) == len(colunas_banco):
            colunas_str = ", ".join(colunas_banco)
            sql_copy = f"""
                COPY {tabela} ({colunas_str}) FROM STDIN WITH (
                    FORMAT CSV,
                    HEADER true,
                    DELIMITER '{CSV_SEPARADOR}',
                    QUOTE '"'
                )
            """
            with open(caminho_csv, "r", encoding=CSV_ENCODING, errors="replace") as f:
                cursor.copy_expert(sql_copy, f)

        else:
            # Se o CSV tem colunas a mais, lê em blocos e filtra apenas as colunas da tabela
                leitor = pd.read_csv(
                    caminho_csv,
                    sep=CSV_SEPARADOR,
                    encoding=CSV_ENCODING,
                    dtype=str,
                    keep_default_na=False,
                    chunksize=TAMANHO_BLOCO,
                )

                colunas_usar = df_head.columns[:len(colunas_banco)]
                colunas_str = ", ".join(colunas_banco)

                sql_copy = f"""
                    COPY {tabela} ({colunas_str}) FROM STDIN WITH (
                        FORMAT CSV,
                        HEADER false,
                        DELIMITER '{CSV_SEPARADOR}',
                        QUOTE '"'
                    )
                """

                for bloco in leitor:
                    bloco_filtrado = bloco[colunas_usar]
                    buffer = io.StringIO()
                    bloco_filtrado.to_csv(
                        buffer,
                        sep=CSV_SEPARADOR,
                        index=False,
                        header=False,
                        quoting=1,  # QUOTE_ALL para proteger quebras de texto
                    )
                    buffer.seek(0)
                    cursor.copy_expert(sql_copy, buffer)

        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        total = cursor.fetchone()[0]
        cursor.close()
        print(f"   {total:,} linhas carregadas via COPY")
        return total
    except Exception as erro:
        print(f"Falha durante o processamento da tabela {tabela}: {erro}")
        raise
    finally:
        cursor.close()

# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
dados_prontos = False
try:
    baixar_dados()
    dados_prontos = True
except Exception as erro:
    print(f"ERRO ao obter os dados: {type(erro).__name__}: {erro}")

if dados_prontos:
    conexao = None
    try:
        conexao = conectar()
        resumo = []
        for dados in ARQUIVOS.values():
            nome_csv = dados["csv"]
            tabela = dados["tabela_raw"]
            print(f"\nCarregando {nome_csv} em {tabela}...")
            total_csv = carregar_raw(conexao, nome_csv, tabela)
            conexao.commit()

            cursor = conexao.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            total_tabela = cursor.fetchone()[0]
            cursor.close()
            resumo.append((tabela, total_csv, total_tabela))

        print("\nConferência (linhas lidas do CSV x linhas na tabela Raw):")
        for tabela, total_csv, total_tabela in resumo:
            situacao = "OK" if total_csv == total_tabela else "DIFERENTE!"
            print(f"   {tabela:<15} {total_csv:>9} x {total_tabela:>9}  {situacao}")
    except Exception as erro:
        if conexao:
            conexao.rollback()  # desfaz a tabela que estava sendo carregada
        print(f"\nERRO na carga da camada Raw: {type(erro).__name__}: {erro}")
    finally:
        if conexao:
            conexao.close()
            