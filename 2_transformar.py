"""
Transforma os dados da camada Raw, aplica tipagem (DECIMAL, DATE), 
calcula colunas e carrega na camada Silver mantendo integridade referencial.
"""

import pandas as pd
import numpy as np
import banco

def limpar_moeda(serie):
    """
    Substitui a virgula do padrao brasileiro por ponto e converte para float.
    Valores ausentes/invalidos viram NaN (nao 0), para nao mascarar dados
    faltantes nas somas e medias. Quem precisar tratar ausente como 0 (ex.:
    colunas somadas em valor_total) faz isso explicitamente com .fillna(0).
    """
    serie_limpa = (
        serie.astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .replace({'nan': None, 'None': None, '': None})
    )
    return pd.to_numeric(serie_limpa, errors='coerce')

def limpar_data(serie):
    """Converte string no formato DD/MM/AAAA para objeto Date (YYYY-MM-DD)."""
    return pd.to_datetime(serie, format='%d/%m/%Y', errors='coerce')

def processar_viagem(conexao):
    print("Transformando raw_viagem para silver_viagem...")
    df = pd.read_sql("SELECT * FROM raw_viagem", conexao)
    
    # Renomear para corresponder ao Dicionario de Dados da camada Silver
    df = df.rename(columns={'id_processo_viagem': 'id_viagem'})
    
    colunas_silver = [
        'id_viagem', 'num_proposta', 'situacao', 'viagem_urgente', 'cod_orgao_superior',
        'nome_orgao_superior', 'nome_viajante', 'cargo', 'data_inicio', 'data_fim',
        'destinos', 'motivo', 'valor_diarias', 'valor_passagens', 'valor_devolucao',
        'valor_outros_gastos'
    ]
    df = df[colunas_silver].copy()
    
    # Conversões e Tipagem
    df['data_inicio'] = limpar_data(df['data_inicio'])
    df['data_fim'] = limpar_data(df['data_fim'])
    
    moedas = ['valor_diarias', 'valor_passagens', 'valor_devolucao', 'valor_outros_gastos']
    for col in moedas:
        df[col] = limpar_moeda(df[col])
    
    # Colunas Calculadas da Regra de Negocio
    # Regra: valor_total trata componente ausente como 0 (nao propaga NaN),
    # mas as colunas originais (valor_diarias, valor_passagens, etc.) mantem
    # o NULL real quando o dado nao veio informado no CSV.
    componentes_soma = df[['valor_diarias', 'valor_passagens', 'valor_outros_gastos']].fillna(0).sum(axis=1)
    df['valor_total'] = componentes_soma - df['valor_devolucao'].fillna(0)
    df['duracao_dias'] = (df['data_fim'] - df['data_inicio']).dt.days

    # Integridade da PK: id_viagem nao pode se repetir na Silver.
    duplicados = df.duplicated(subset=['id_viagem']).sum()
    if duplicados > 0:
        print(f"  Aviso: {duplicados} registro(s) com id_viagem duplicado removido(s) (mantido o primeiro).")
        df = df.drop_duplicates(subset=['id_viagem'], keep='first')

    # Converter dados nulos do Pandas para nulos nativos do Banco de Dados
    df = df.replace({np.nan: None})
    
    # Idempotencia
    banco.executar(conexao, "TRUNCATE TABLE silver_viagem CASCADE;")
    
    # Insercao
    linhas = [tuple(x) for x in df.to_numpy()]
    placeholders = ",".join(["%s"] * len(df.columns))
    sql = f"INSERT INTO silver_viagem VALUES ({placeholders})"
    banco.inserir_em_lote(conexao, sql, linhas)
    print(f"  -> {len(linhas)} registros limpos inseridos.")

def processar_pagamento(conexao):
    print("Transformando raw_pagamento para silver_pagamento...")
    df = pd.read_sql("SELECT * FROM raw_pagamento", conexao)
    df = df.rename(columns={'id_processo_viagem': 'id_viagem'}) 
    
    colunas = ['id_viagem', 'num_proposta', 'nome_orgao_pagador', 'nome_ug_pagadora', 'tipo_pagamento', 'valor']
    df = df[colunas].copy()
    
    df['valor'] = limpar_moeda(df['valor'])
    df = df.replace({np.nan: None})
    
    banco.executar(conexao, "TRUNCATE TABLE silver_pagamento CASCADE;")
    
    linhas = [tuple(x) for x in df.to_numpy()]
    colunas_str = ", ".join(colunas)
    placeholders = ",".join(["%s"] * len(colunas))
    # Nao inserido o id_pagamento pois na tabela ele é AUTO_INCREMENT/SERIAL
    sql = f"INSERT INTO silver_pagamento ({colunas_str}) VALUES ({placeholders})"
    banco.inserir_em_lote(conexao, sql, linhas)

def processar_passagem(conexao):
    print("Transformando raw_passagem para silver_passagem...")
    df = pd.read_sql("SELECT * FROM raw_passagem", conexao)
    df = df.rename(columns={'id_processo_viagem': 'id_viagem'})
    
    colunas = [
        'id_viagem', 'meio_transporte', 'pais_origem_ida', 'uf_origem_ida', 'cidade_origem_ida',
        'pais_destino_ida', 'uf_destino_ida', 'cidade_destino_ida', 'valor_passagem', 'taxa_servico', 'data_emissao'
    ]
    df = df[colunas].copy()
    
    df['valor_passagem'] = limpar_moeda(df['valor_passagem'])
    df['taxa_servico'] = limpar_moeda(df['taxa_servico'])
    df['data_emissao'] = limpar_data(df['data_emissao'])
    
    df = df.replace({np.nan: None})
    banco.executar(conexao, "TRUNCATE TABLE silver_passagem CASCADE;")
    
    linhas = [tuple(x) for x in df.to_numpy()]
    colunas_str = ", ".join(colunas)
    placeholders = ",".join(["%s"] * len(colunas))
    sql = f"INSERT INTO silver_passagem ({colunas_str}) VALUES ({placeholders})"
    banco.inserir_em_lote(conexao, sql, linhas)

def processar_trecho(conexao):
    print("Transformando raw_trecho para silver_trecho...")
    df = pd.read_sql("SELECT * FROM raw_trecho", conexao)
    df = df.rename(columns={'id_processo_viagem': 'id_viagem'})
    
    colunas = [
        'id_viagem', 'sequencia_trecho', 'origem_data', 'origem_uf', 'origem_cidade',
        'destino_data', 'destino_uf', 'destino_cidade', 'meio_transporte', 'numero_diarias'
    ]
    df = df[colunas].copy()
    
    df['origem_data'] = limpar_data(df['origem_data'])
    df['destino_data'] = limpar_data(df['destino_data'])
    df['numero_diarias'] = limpar_moeda(df['numero_diarias'])
    df['sequencia_trecho'] = pd.to_numeric(df['sequencia_trecho'], errors='coerce')

    # Integridade da UNIQUE (id_viagem, sequencia_trecho)
    duplicados = df.duplicated(subset=['id_viagem', 'sequencia_trecho']).sum()
    if duplicados > 0:
        print(f"  Aviso: {duplicados} trecho(s) duplicado(s) por (id_viagem, sequencia_trecho) removido(s).")
        df = df.drop_duplicates(subset=['id_viagem', 'sequencia_trecho'], keep='first')

    df = df.replace({np.nan: None})
    banco.executar(conexao, "TRUNCATE TABLE silver_trecho CASCADE;")
    
    linhas = [tuple(x) for x in df.to_numpy()]
    colunas_str = ", ".join(colunas)
    placeholders = ",".join(["%s"] * len(colunas))
    sql = f"INSERT INTO silver_trecho ({colunas_str}) VALUES ({placeholders})"
    banco.inserir_em_lote(conexao, sql, linhas)

def main():
    print("Iniciando Fase 2: Transformação (Raw -> Silver)...")
    conexao = banco.conectar()
    try:
        # A ordem de insercao abaixo é OBRIGATORIA devido as Foreign Keys
        processar_viagem(conexao)
        processar_pagamento(conexao)
        processar_passagem(conexao)
        processar_trecho(conexao)
        
        print("Fase 2 concluída com sucesso! Camada Silver atualizada e limpa.")
    except Exception as e:
        print(f"Erro na fase de transformação: {e}")
    finally:
        conexao.close()

if __name__ == "__main__":
    main()
    
