# Projeto-Avaliativo-M1-Analise-de-Dados-com-Python-T1-
Kauan Raitz dos Anjos

## Qual o problema este projeto resolve?
Atualmente, o Portal da Transparência gera um grande volume de dados abertos sobre os gastos públicos, porém em formato bruto e desorganizado. Este projeto simula uma consultoria de dados contratada pelo governo para dar mais transparência aos gastos com viagens a serviço. O objetivo foi construir um pipeline de dados de ponta a ponta (ETL) que extrai esses dados, aplica tratamentos de limpeza e integridade, e os converte em métricas e visualizações claras para tomada de decisão.

## Técnicas e Tecnologias Utilizadas
O projeto adota a **Arquitetura Medallion** dividida em três camadas:
- **Camada Raw**: Cópia fiel dos dados brutos preservando o histórico.
- **Camada Silver**: Dados limpos, tipados e com integridade referencial (PK/FK).
- **Camada Gold**: Dados agregados para visualização e inteligência de negócio.

**Stack Tecnológica:**
- **Linguagens**: Python e SQL
- **Banco de Dados**: PostgreSQL
- **Bibliotecas Python**: `pandas` (manipulação de dados), `gdown` (extração em nuvem), `psycopg2` (conexão com o banco)
- **DataViz**: `matplotlib` e `seaborn` (Jupyter Notebook)
- **Controle de Versão**: Git e GitHub

## Como Executar o Projeto
1. Clone o repositório localmente.
2. Crie um arquivo `.env` baseado no `.env.example` e preencha com suas credenciais do PostgreSQL local.
3. Instale as dependências executando: `pip install -r requirements.txt`.
4. Execute o script `0_criar_banco.sql` no seu banco PostgreSQL para criar as 8 tabelas com as devidas constraints.
5. Rode o script de extração: `python 1_extrair.py`. Ele fará o download e carregará os arquivos na camada Raw em blocos (chunks).
6. Rode o script de transformação: `python 2_transformar.py`. Ele fará a tipagem, calculará as colunas necessárias e populará a camada Silver.
7. Abra o arquivo `3_analise.ipynb` no Jupyter Notebook (ou VS Code) para gerar a camada Gold agregada, responder às perguntas de negócio e visualizar os gráficos.

## Conclusões e Insights
A partir da análise dos dados na camada Gold, foi possível identificar:
- Concentração de gastos: A maior parte do orçamento de viagens está concentrada em poucos órgãos superiores.
- Custo x Destino: Os destinos que apresentam o maior custo médio por viagem indicam locais que exigem maior monitoramento e planejamento prévio de verba.
- Eficiência de Pagamento: A agregação da tabela de pagamentos evidenciou quais meios concentram os maiores tickets médios.
- Logística: A análise dos trechos e UFs de destino revela a malha logística mais utilizada pelo serviço público, ajudando na negociação futura de contratos de transporte.

## Melhorias Futuras
- **Orquestração**: Adicionar uma ferramenta como Apache Airflow para automatizar a execução do pipeline de ponta a ponta em horários programados.
- **Testes Automatizados**: Implementar `pytest` para garantir a qualidade das transformações de dados.
- **Conteinerização**: Usar Docker para criar um ambiente isolado para a aplicação e o banco de dados.
