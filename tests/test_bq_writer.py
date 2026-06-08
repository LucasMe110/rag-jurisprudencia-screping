import hashlib
from unittest.mock import patch, MagicMock
from screping.bq_writer import insert_records


def _record(processo="001", data_julgamento="01/01/2018", decisao="Provido."):
    return {
        "processo": processo,
        "orgao_julgador": "Câmara",
        "data_julgamento": data_julgamento,
        "data_publicacao": "15/01/2018",
        "relator": "Dr. Juiz",
        "decisao": decisao,
        "embedding": [0.1] * 768,
    }


def test_insert_records_generates_correct_id():
    records = [_record(processo="001", data_julgamento="01/01/2018")]
    expected_id = hashlib.sha256("001|01/01/2018".encode()).hexdigest()

    with patch("screping.bq_writer.bigquery.Client") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.insert_rows_json.return_value = []

        insert_records(records, "project", "dataset", "table")

        inserted = mock_client.insert_rows_json.call_args[0][1]
        assert inserted[0]["id"] == expected_id


def test_insert_records_chunks_by_256():
    records = [_record(processo=str(i)) for i in range(512)]

    with patch("screping.bq_writer.bigquery.Client") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.insert_rows_json.return_value = []

        insert_records(records, "project", "dataset", "table")

        assert mock_client.insert_rows_json.call_count == 2


def test_insert_records_returns_zero_on_success():
    records = [_record()]

    with patch("screping.bq_writer.bigquery.Client") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.insert_rows_json.return_value = []

        errors = insert_records(records, "project", "dataset", "table")

        assert errors == 0


def test_insert_records_retries_on_error():
    records = [_record()]
    error_response = [{"index": 0, "errors": [{"reason": "timeout"}]}]

    with patch("screping.bq_writer.bigquery.Client") as MockClient, \
         patch("time.sleep") as mock_sleep:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.insert_rows_json.side_effect = [error_response, error_response, []]

        errors = insert_records(records, "project", "dataset", "table")

        assert errors == 0
        assert mock_client.insert_rows_json.call_count == 3
        assert mock_sleep.call_count == 2


def test_insert_records_counts_errors_after_3_failed_attempts():
    records = [_record()]
    error_response = [{"index": 0, "errors": [{"reason": "notFound"}]}]

    with patch("screping.bq_writer.bigquery.Client") as MockClient, \
         patch("time.sleep"):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.insert_rows_json.return_value = error_response

        errors = insert_records(records, "project", "dataset", "table")

        assert errors > 0
