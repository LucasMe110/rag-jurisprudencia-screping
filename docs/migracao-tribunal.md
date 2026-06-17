# Migração de schema — coluna `tribunal` em `processos_raw`

O scraper agora grava o campo `tribunal` em cada linha de `processos_raw`
(US-104). O streaming insert do BigQuery (`insert_rows_json`) **exige que a
coluna já exista** na tabela antes da inserção — caso contrário as linhas são
rejeitadas.

## ⚠️ Passo MANUAL — pré-requisito da primeira coleta TJSP

Os comandos abaixo são de **schema/dados** e devem ser executados **uma única
vez, manualmente**, por um operador humano, **antes** de rodar o scraper para
qualquer tribunal novo (TJSP/TJRJ).

> **O Ralph (agente autônomo) NÃO deve executar estes comandos** — são
> operações destrutivas/de schema no BigQuery e estão fora do escopo da
> automação. Rode você mesmo, com credenciais adequadas.

### 1. Adicionar a coluna

```sql
ALTER TABLE `processos_raw`
ADD COLUMN tribunal STRING;
```

### 2. Backfill dos registros TJSC existentes

Todos os registros coletados antes desta migração são do TJSC. Marque-os:

```sql
UPDATE `processos_raw`
SET tribunal = 'tjsc'
WHERE tribunal IS NULL;
```

Substitua `processos_raw` pelo nome totalmente qualificado da tabela
(`projeto.dataset.processos_raw`) conforme o ambiente.

## Por que o ID não muda

O `id` continua sendo `SHA-256("{processo}|{data_julgamento}")`. O número CNJ do
processo já discrimina o tribunal de origem (`.8.26.` = SP, `.8.24.` = SC,
`.8.19.` = RJ), então não há risco de colisão de IDs entre tribunais.
