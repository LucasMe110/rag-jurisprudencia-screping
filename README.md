# Scraper TJSC — Coleta Histórica em Lotes Noturnos

Scraper de jurisprudência do TJSC para coleta histórica (2018 → presente) em lotes mensais noturnos.
Cada execução processa 1 mês, gera embeddings com `intfloat/multilingual-e5-base` e insere diretamente no BigQuery `processos_v2`.

## Como funciona

O workflow `nightly-scraper` executa diariamente às 3h BRT (6h UTC). A cada execução:

1. Lê `checkpoint.json` para saber qual mês processar
2. Raspa todas as páginas do TJSC para aquele mês
3. Gera embeddings (768 dims) para cada decisão
4. Insere os registros no BigQuery `processos_v2`
5. Atualiza e commita `checkpoint.json` com o próximo mês

## Configuração do Repositório

### GitHub Secrets

| Secret | Descrição |
|--------|-----------|
| `GCP_SA_KEY` | Conteúdo JSON completo da chave do Service Account GCP |
| `BQ_DATASET_ID` | Nome do dataset BigQuery (ex: `juridico`) |
| `BQ_TABLE_ID` | Nome da tabela BigQuery (ex: `processos_v2`) |

### GitHub Variables

| Variable | Descrição |
|----------|-----------|
| `GCP_PROJECT_ID` | ID do projeto GCP (ex: `rag-juridico-492317`) |

> `GCP_PROJECT_ID` pode ser uma Variable (não Secret) pois não é sensível.

### Criando o Service Account

1. Acesse o [Google Cloud Console](https://console.cloud.google.com) e selecione o projeto
2. Navegue para **IAM & Admin → Service Accounts**
3. Clique em **Create Service Account**
4. Dê um nome (ex: `tjsc-scraper`) e clique em **Create and Continue**
5. Atribua o papel **BigQuery Data Editor** (`roles/bigquery.dataEditor`) e clique em **Continue → Done**
6. Na lista de Service Accounts, clique no SA recém-criado
7. Vá para a aba **Keys → Add Key → Create new key → JSON**
8. Faça download do arquivo JSON gerado
9. No repositório GitHub, vá para **Settings → Secrets and variables → Actions**
10. Crie o secret `GCP_SA_KEY` colando o conteúdo completo do JSON baixado

## Execução Local

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa-key.json
export GCP_PROJECT_ID=rag-juridico-492317
export BQ_DATASET_ID=juridico
export BQ_TABLE_ID=processos_v2
python screping/main.py
```

## Testes

```bash
pytest tests/ -v
```
