# Scraper TJSC — Instruções para Claude

## Visão Geral

Scraper de jurisprudência do TJSC para coleta histórica (2018 → presente) em lotes noturnos.
Destino final: BigQuery `processos_v2` (mesma tabela usada pelo app JurisprudêncIA em produção).

## Stack

| Componente | Tecnologia |
|---|---|
| Scraping | requests + BeautifulSoup4 |
| Embedding | `intfloat/multilingual-e5-base` (768 dims) via sentence-transformers |
| Destino | BigQuery — tabela `processos_v2` no projeto `rag-juridico-492317` |
| Checkpoint | `checkpoint.json` na raiz do repo |
| Agendamento | GitHub Actions cron `0 6 * * *` (3h BRT) |
| Auth GCP | Service Account Key JSON em GitHub Secret `GCP_SA_KEY` |

## Estrutura de Arquivos

```
screping/
├── main.py           # entry point — lê checkpoint, scrapa 1 mês, embeda, insere no BQ, atualiza checkpoint
├── scraper.py        # lógica de scraping do portal TJSC por faixa de data
├── embedder.py       # geração de embeddings com multilingual-e5-base
└── bq_writer.py      # inserção de registros no BigQuery processos_v2
checkpoint.json       # estado do progresso (gerado automaticamente)
requirements.txt
tests/
├── __init__.py
├── test_scraper.py
├── test_embedder.py
└── test_bq_writer.py
.github/
└── workflows/
    └── nightly-scraper.yml
```

## Schema BigQuery — processos_v2

```
id               STRING    — SHA-256 hex de (processo + data_julgamento)
processo         STRING    — número do processo (ex: 0001234-56.2018.8.24.0001)
orgao_julgador   STRING
data_julgamento  STRING
data_publicacao  STRING
relator          STRING
decisao          STRING    — texto completo da decisão/ementa
embedding        FLOAT64 REPEATED — vetor 768-dim, prefixo "passage: {decisao}"
```

## Formato do checkpoint.json

```json
{
  "next_month": "2018-01",
  "completed_months": ["2018-01", "2018-02"],
  "failed_pages": [
    {"month": "2018-01", "page": 42, "error": "timeout"}
  ]
}
```

- `next_month`: próximo mês a processar (YYYY-MM). Quando ultrapassa o mês atual, scraping está completo.
- `completed_months`: meses já inseridos no BQ com sucesso.
- `failed_pages`: páginas puladas após 3 tentativas (para análise posterior).

## Pipeline por Execução Noturna

```
Ler checkpoint.json
    │
    ▼
scrape_month(next_month)    ← POST paginado com dtDecisaoInicio/dtDecisaoFim
    │  retry 3x por página, skip com log se ainda falhar
    ▼
generate_embeddings(records) ← "passage: {decisao}" → vetor 768-dim
    │  batch_size=256
    ▼
insert_to_bigquery(records)  ← streaming insert em processos_v2
    │  chunks de 256 registros
    ▼
Atualizar checkpoint.json (next_month += 1 mês)
    │
    ▼
git commit + push checkpoint.json
```

## Embedding

Usar exatamente o mesmo modelo e prefixo que o app de produção usa em `reindex.py`:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-base")
texts = [f"passage: {r['decisao'] or ''}" for r in records]
vectors = model.encode(texts, batch_size=256, normalize_embeddings=True)
```

## Padrões de Código

- **TDD:** escrever testes antes do código de produção
- **Variáveis de ambiente:** `GCP_PROJECT_ID`, `BQ_DATASET_ID`, `BQ_TABLE_ID` (valor: `processos_v2`), `GOOGLE_APPLICATION_CREDENTIALS`
- **Geração de ID:** `hashlib.sha256(f"{processo}|{data_julgamento}".encode()).hexdigest()`
- **Inserção BQ:** `client.insert_rows_json(table, rows)` em chunks de 256, retry 3x
- **Sem hardcode de datas** — usar `datetime.date.today()` para saber quando parar

## Rodar Localmente

```bash
pip install -r requirements.txt
# Configurar .env ou variáveis de ambiente com credenciais GCP
python screping/main.py
```

## Testes

```bash
pytest tests/ -v
```

Todos os testes devem mockar chamadas externas (requests, BigQuery, SentenceTransformer).

## GCP — Projeto e Dataset

- Project: `rag-juridico-492317`
- Dataset: variável `BQ_DATASET_ID` (tipicamente `juridico`)
- Table: `processos_v2`
