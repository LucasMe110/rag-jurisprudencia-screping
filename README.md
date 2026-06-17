# Scraper Multi-Tribunal — Coleta Histórica em Lotes Noturnos

Scraper de jurisprudência do eproc para coleta histórica em lotes noturnos via GitHub Actions.

Tribunais suportados (mesma implementação eproc, rota `acao=jurisprudencia@jurisprudencia`):

| Tribunal | Base eproc | Piso (`STOP_MONTH` default) |
|----------|------------|------------------------------|
| `tjsc` | `eproc1g.tjsc.jus.br` | `2018-01` (mês atual → 2018) |
| `tjsp` | `eproc1g.tjsp.jus.br` | `2024-01` (últimos 2 anos) |
| `tjrj` | `eproc1g.tjrj.jus.br` | `2024-01` |

O workflow noturno roda `tjsc` e `tjsp` em matriz (`max-parallel: 1`, sequencial para não conflitar no mesmo `checkpoint.json`). Cada registro carrega o campo `tribunal`.

## Como funciona

O pipeline é dividido em **duas etapas independentes**:

### Etapa 1 — Coleta (automática, noturna)
O workflow `nightly-scraper` executa diariamente às 3h BRT (6h UTC). A cada execução:

1. Lê `checkpoint.json` (indexado por tribunal) para saber qual mês processar (começa no mês atual, vai para o passado)
2. Raspa todas as páginas do tribunal (env `TRIBUNAL`) para aquele mês via POST paginado
3. Insere os registros **brutos** (sem embedding, com o campo `tribunal`) na tabela `processos_raw` no BigQuery
4. Atualiza e commita `checkpoint.json` com o mês anterior

> **Pré-requisito de schema (uma vez, manual):** antes da primeira coleta com o campo `tribunal`,
> a tabela `processos_raw` precisa da coluna `tribunal`. Veja [docs/migracao-tribunal.md](docs/migracao-tribunal.md)
> para o `ALTER TABLE` / `UPDATE` — execute **manualmente** no BigQuery.

### Etapa 2 — Geração de embeddings (manual, via Colab)
Após acumular dados em `processos_raw`, execute o `reindex.py` do projeto principal para gerar os embeddings e popular a tabela de busca:

```bash
# No projeto principal (Rag_Jurisprudencia), com GPU no Colab ou máquina local:
python scripts/reindex.py --source processos_raw --dest processos_v2
```

O `reindex.py` usa LEFT JOIN para processar apenas registros ainda sem embedding — pode ser executado quantas vezes quiser, sempre continuando de onde parou.

**Por que separar?** Gerar embeddings com `multilingual-e5-base` em CPU (GitHub Actions) leva horas. No Colab com GPU, o mesmo volume leva minutos.

## Progresso

O `checkpoint.json` commitado no repo registra o estado atual, indexado por tribunal:

```json
{
  "tjsc": {
    "next_month": "2026-05",
    "completed_months": ["2026-06", "2026-05"],
    "failed_pages": []
  },
  "tjsp": {
    "next_month": "2026-05",
    "completed_months": ["2026-06"],
    "failed_pages": []
  }
}
```

## Configuração

### Pré-requisitos no BigQuery

Crie as duas tabelas no seu projeto GCP antes de rodar:

- `processos_raw` — dados brutos sem embedding (schema: `id, processo, orgao_julgador, data_julgamento, data_publicacao, relator, decisao`)
- `processos_v2` — tabela final com embeddings (criada pelo `reindex.py`)

### GitHub Secrets

| Secret | Descrição |
|--------|-----------|
| `GCP_SA_KEY` | Conteúdo JSON completo da chave do Service Account |
| `BQ_DATASET_ID` | Nome do dataset BigQuery |
| `BQ_TABLE_ID` | Nome da tabela de destino (ex: `processos_raw`) |

### GitHub Variables

| Variable | Descrição |
|----------|-----------|
| `GCP_PROJECT_ID` | ID do projeto GCP |

### Criando o Service Account

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. **IAM & Admin → Service Accounts → Create Service Account**
3. Atribua o papel **BigQuery Data Editor** (`roles/bigquery.dataEditor`)
4. **Keys → Add Key → Create new key → JSON** — faça download
5. No repo: **Settings → Secrets and variables → Actions → New secret**
6. Crie `GCP_SA_KEY` com o conteúdo completo do JSON

## Execução local

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/sa-key.json
export GCP_PROJECT_ID=seu-projeto
export BQ_DATASET_ID=seu-dataset
export BQ_TABLE_ID=processos_raw
export TRIBUNAL=tjsp           # tjsc (default) | tjsp | tjrj
# export STOP_MONTH=2024-01    # opcional — sobrescreve o piso default do tribunal
python screping/main.py
```

A variável `TRIBUNAL` (default `tjsc`) escolhe qual tribunal coletar; `STOP_MONTH` (opcional)
sobrescreve o mês-piso default (`tjsc`→`2018-01`, `tjsp`/`tjrj`→`2024-01`).

## Testes

```bash
pytest tests/ -v
```
