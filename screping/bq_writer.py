import hashlib
import time
from google.cloud import bigquery


def insert_records(records: list[dict], project_id: str, dataset_id: str, table_id: str) -> int:
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    total_errors = 0

    for i in range(0, len(records), 256):
        chunk = records[i : i + 256]
        rows = []
        for r in chunk:
            row = dict(r)
            row["id"] = hashlib.sha256(
                f"{r['processo']}|{r['data_julgamento']}".encode()
            ).hexdigest()
            rows.append(row)

        for attempt in range(3):
            errors = client.insert_rows_json(table_ref, rows)
            if not errors:
                break
            if attempt < 2:
                time.sleep(5)
        else:
            total_errors += len(errors)

    return total_errors
