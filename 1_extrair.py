"""
Script para baixar o arquivo do portal da transparência via Google Drive,
extrair e carregar os dados brutos nas tabelas RAW do banco de dados de forma em blocos.
"""

import os
import zipfile
import pandas as pd
import gdown
from psycopg2 import Error

import banco
from config import (
    PASTA_DADOS,
    DRIVE_FILE_ID,
    ARQUIVOS,
    TAMANHO_BLOCO,
    CSV_SEPARADOR,
    CSV_ENCODING
)

def baixar_e_extrair():
    """Baixa o arquivo .zip do Google Drive e extrai os CSVs."""
    if not PASTA_DADOS.exists():
        PASTA_DADOS.mkdir(parents=True)
    
    caminho_zip = PASTA_DADOS / "dados.zip"
    
    # Faz o download apenas se o arquivo ainda nao existir
    if not caminho_zip.exists():
        print("Baixando arquivo do Google Drive...")
        url = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'
        try:
            gdown.download(url, str(caminho_zip), quiet=False)
        except Exception as e:
            raise RuntimeError(f"Erro ao baixar arquivo do Drive: {e}")
    
    print("Extraindo arquivo ZIP...")
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            zip_ref.extractall(PASTA_DADOS)
    except Exception as e:
         raise RuntimeError(f"Erro ao extrair o arquivo ZIP: {e}")

def carregar_dados_raw(conexao):
    """Le os CSVs em blocos e os insere nas respectivas tabelas da camada Raw."""
    for chave, info in ARQUIVOS.items():
        arquivo_csv = PASTA_DADOS / info["csv"]
        tabela_raw = info["tabela_raw"]
        
        # Idempotência: Limpar a tabela antes de inserir
        print(f"Limpando tabela {tabela_raw} (TRUNCATE)...")
        banco.executar(conexao, f"TRUNCATE TABLE {tabela_raw} CASCADE;")
        
        if not arquivo_csv.exists():
            print(f"Aviso: Arquivo {arquivo_csv.name} não encontrado. Pulando...")
            continue
        
        print(f"Iniciando carga de {arquivo_csv.name} para {tabela_raw}...")
        
        try:
            # Lendo o arquivo em blocos (chunks) para não estourar a memória
            chunks = pd.read_csv(
                arquivo_csv,
                sep=CSV_SEPARADOR,
                encoding=CSV_ENCODING,
                chunksize=TAMANHO_BLOCO,
                dtype=str # Tratando tudo como texto na RAW
            )
            
            for i, chunk in enumerate(chunks):
                # Substitui valores NaN do Pandas por None para inserir NULL no Banco
                chunk = chunk.where(pd.notnull(chunk), None)
                
                # Prepara os valores em lista de tuplas
                linhas = [tuple(x) for x in chunk.to_numpy()]
                
                # Monta a quantidade de %s de acordo com o número de colunas
                placeholders = ",".join(["%s"] * len(chunk.columns))
                sql_insert = f"INSERT INTO {tabela_raw} VALUES ({placeholders})"
                
                # Utiliza a função do banco.py para inserção em lote
                banco.inserir_em_lote(conexao, sql_insert, linhas)
                print(f"  -> Bloco {i+1} carregado ({len(linhas)} registros).")
                
        except Exception as e:
            print(f"Erro crítico ao processar o arquivo {arquivo_csv.name}: {e}")

def main():
    print("Iniciando Fase 1: Extração e Camada Raw...")
    try:
        baixar_e_extrair()
        
        print("Conectando ao banco de dados PostgreSQL...")
        conexao = banco.conectar()
        
        carregar_dados_raw(conexao)
        
        conexao.close()
        print("Fase 1 concluída com sucesso! Dados carregados na camada Raw.")
        
    except Exception as erro:
        print(f"O pipeline falhou: {erro}")

if __name__ == "__main__":
    main()
