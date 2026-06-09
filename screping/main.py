import os
import sys
import datetime

from screping.checkpoint import load_checkpoint, save_checkpoint
from screping.scraper import scrape_month
from screping.bq_writer import insert_records


def main() -> None:
    checkpoint = load_checkpoint()
    next_month_str = checkpoint["next_month"]
    year, month = map(int, next_month_str.split("-"))

    if datetime.date(year, month, 1) < datetime.date(2018, 1, 1):
        print("Coleta completa — chegamos em janeiro/2018.")
        return

    failed_pages: list = checkpoint.get("failed_pages", [])
    print(f"Raspando {next_month_str}...")
    records = scrape_month(year, month, failed_pages=failed_pages)
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

    save_checkpoint(checkpoint)
    print(f"Checkpoint atualizado. Próximo mês: {checkpoint['next_month']}")


if __name__ == "__main__":
    main()
