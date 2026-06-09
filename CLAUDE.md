# Scraper TJSC — Instruções para Claude

## Visão Geral

Scraper de jurisprudência do TJSC para coleta histórica em lotes noturnos.
Processa do mês atual para o passado (até jan/2018), 1 mês por execução.

## Pipeline — Duas Etapas

```
ETAPA 1 — GitHub Actions (automático, noturno, gratuito)
    Scraping TJSC por faixa de data
          ↓
    Insere dados BRUTOS em processos_raw (sem embedding)
          ↓
    Commita checkpoint.json com mês anterior

ETAPA 2 — Colab/máquina local (manual, quando acumular dados)
    reindex.py --source processos_raw --dest processos_v2
    (lê registros sem embedding → gera embedding → grava em processos_v2)
```

**Por que separar?** O modelo `multilingual-e5-base` em CPU no GitHub Actions leva horas.
No Colab com GPU, o mesmo volume leva minutos.

## Stack

| Componente | Tecnologia |
|---|---|
| Scraping | requests + BeautifulSoup4 |
| Destino da coleta | BigQuery `processos_raw` — dados brutos, sem embedding |
| Destino da busca | BigQuery `processos_v2` — com embeddings, gerado via reindex.py |
| Checkpoint | `checkpoint.json` commitado no repo |
| Agendamento | GitHub Actions cron `0 6 * * *` (3h BRT) — repo público = gratuito |
| Auth GCP | Service Account Key JSON em GitHub Secret `GCP_SA_KEY` |

## Estrutura de Arquivos

```
screping/
├── main.py           # entry point — checkpoint → scrape → insert raw → update checkpoint
├── scraper.py        # scraping TJSC por faixa de data, retry 3x, PAGE_SIZE=100
├── checkpoint.py     # load/save checkpoint.json
├── bq_writer.py      # streaming insert no BigQuery (sem embedding)
└── embedder.py       # (não usado no pipeline atual — mantido para referência)
checkpoint.json       # gerado automaticamente pelo workflow
requirements.txt
tests/
├── test_scraper.py
├── test_checkpoint.py
├── test_bq_writer.py
└── test_embedder.py
.github/
└── workflows/
    └── nightly-scraper.yml
```

## Schema BigQuery

### processos_raw (destino do scraper)
```
id               STRING    — SHA-256 de "{processo}|{data_julgamento}"
processo         STRING
orgao_julgador   STRING
data_julgamento  STRING
data_publicacao  STRING
relator          STRING
decisao          STRING    — texto completo da decisão/ementa
```

### processos_v2 (destino do reindex.py — gerado separadamente)
```
(mesmos campos acima)
embedding        FLOAT64 REPEATED — vetor 768-dim gerado pelo reindex.py
```

## Formato do checkpoint.json

```json
{
  "next_month": "2026-05",
  "completed_months": ["2026-06", "2026-05"],
  "failed_pages": [
    {"month": "2026-06", "page": 12, "error": "timeout"}
  ]
}
```

- `next_month`: próximo mês a processar — começa no mês atual e vai para o passado
- `completed_months`: meses já inseridos em `processos_raw`
- `failed_pages`: páginas puladas após 3 tentativas (para análise posterior)
- Para reiniciar do zero: apagar `checkpoint.json` do repo

## Padrões de Código

- **TDD:** testes antes do código de produção
- **Variáveis de ambiente:** `GCP_PROJECT_ID`, `BQ_DATASET_ID`, `BQ_TABLE_ID`, `GOOGLE_APPLICATION_CREDENTIALS`
- **ID de registro:** `hashlib.sha256(f"{processo}|{data_julgamento}".encode()).hexdigest()`
- **Inserção BQ:** `client.insert_rows_json()` em chunks de 256, retry 3x
- **PAGE_SIZE=100** no scraper — reduz requests 10x (servidor TJSC ~29s/req do GitHub)

## Rodar Localmente

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/sa-key.json
export GCP_PROJECT_ID=seu-projeto
export BQ_DATASET_ID=seu-dataset
export BQ_TABLE_ID=processos_raw
python screping/main.py
```

## Testes

```bash
pytest tests/ -v
```
