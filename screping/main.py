import os
import sys
import datetime

from screping.checkpoint import load_checkpoint, save_checkpoint
from screping.scraper import scrape_month
from screping.bq_writer import insert_records

DEFAULT_STOP = {"tjsc": "2018-01", "tjsp": "2024-01", "tjrj": "2024-01"}


def main() -> None:
    tribunal = os.environ.get("TRIBUNAL", "tjsc")
    stop_month = os.environ.get("STOP_MONTH", DEFAULT_STOP.get(tribunal, "2018-01"))

    checkpoint = load_checkpoint(tribunal)
    next_month_str = checkpoint["next_month"]
    year, month = map(int, next_month_str.split("-"))
    stop_year, stop_month_n = map(int, stop_month.split("-"))

    if datetime.date(year, month, 1) < datetime.date(stop_year, stop_month_n, 1):
        print(f"Coleta completa para {tribunal} — atingiu {stop_month}.")
        return

    failed_pages: list = checkpoint.get("failed_pages", [])
    print(f"Raspando {tribunal} {next_month_str}...")
    records = scrape_month(year, month, failed_pages=failed_pages, tribunal=tribunal)
    print(f"{len(records)} registros coletados.")

    if records:
        project_id = os.environ["GCP_PROJECT_ID"]
        dataset_id = os.environ["BQ_DATASET_ID"]
        table_id = os.environ.get("BQ_TABLE_ID", "processos_raw")

        print(f"Inserindo no BigQuery {project_id}.{dataset_id}.{table_id}...")
        errors = insert_records(records, project_id, dataset_id, table_id)
        if errors > 0:
            print(f"ERRO: {errors} registros não foram inseridos.", file=sys.stderr)
            sys.exit(1)

    next_month = month - 1 if month > 1 else 12
    next_year = year if month > 1 else year - 1

    completed_months = checkpoint.get("completed_months", [])
    completed_months.append(next_month_str)
    checkpoint["completed_months"] = completed_months
    checkpoint["next_month"] = f"{next_year}-{next_month:02d}"
    checkpoint["failed_pages"] = failed_pages

    save_checkpoint(tribunal, checkpoint)
    print(f"Checkpoint atualizado. Próximo mês: {checkpoint['next_month']}")


if __name__ == "__main__":
    main()
