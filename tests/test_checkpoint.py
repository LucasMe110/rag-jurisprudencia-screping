import json
import datetime
from screping.checkpoint import load_checkpoint, save_checkpoint


def _current_month_str() -> str:
    today = datetime.date.today()
    return f"{today.year}-{today.month:02d}"


def test_load_checkpoint_missing_file_returns_default(tmp_path):
    cp = load_checkpoint("tjsp", tmp_path / "checkpoint.json")
    assert cp["next_month"] == _current_month_str()
    assert cp["completed_months"] == []
    assert cp["failed_pages"] == []


def test_load_checkpoint_tribunal_not_present_returns_default(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    cp_file.write_text(
        json.dumps(
            {"tjsc": {"next_month": "2020-06", "completed_months": [], "failed_pages": []}}
        )
    )
    cp = load_checkpoint("tjsp", cp_file)
    assert cp["next_month"] == _current_month_str()
    assert cp["completed_months"] == []
    assert cp["failed_pages"] == []


def test_load_checkpoint_existing_tribunal(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    cp_file.write_text(
        json.dumps(
            {
                "tjsc": {
                    "next_month": "2020-06",
                    "completed_months": ["2020-04", "2020-05"],
                    "failed_pages": [],
                },
                "tjsp": {
                    "next_month": "2024-05",
                    "completed_months": [],
                    "failed_pages": [],
                },
            }
        )
    )
    cp = load_checkpoint("tjsc", cp_file)
    assert cp["next_month"] == "2020-06"
    assert cp["completed_months"] == ["2020-04", "2020-05"]


def test_save_checkpoint_does_not_erase_other_tribunal(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    save_checkpoint(
        "tjsc",
        {"next_month": "2020-06", "completed_months": [], "failed_pages": []},
        cp_file,
    )
    save_checkpoint(
        "tjsp",
        {"next_month": "2024-05", "completed_months": [], "failed_pages": []},
        cp_file,
    )
    data = json.loads(cp_file.read_text())
    assert "tjsc" in data
    assert "tjsp" in data
    assert data["tjsc"]["next_month"] == "2020-06"
    assert data["tjsp"]["next_month"] == "2024-05"


def test_save_checkpoint_updates_only_one_tribunal(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    save_checkpoint(
        "tjsc",
        {"next_month": "2020-06", "completed_months": [], "failed_pages": []},
        cp_file,
    )
    save_checkpoint(
        "tjsc",
        {"next_month": "2020-05", "completed_months": ["2020-06"], "failed_pages": []},
        cp_file,
    )
    data = json.loads(cp_file.read_text())
    assert data["tjsc"]["next_month"] == "2020-05"
    assert data["tjsc"]["completed_months"] == ["2020-06"]


def test_migration_flat_format_treated_as_tjsc(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    cp_file.write_text(
        json.dumps(
            {
                "next_month": "2019-03",
                "completed_months": ["2019-01", "2019-02"],
                "failed_pages": [],
            }
        )
    )
    cp = load_checkpoint("tjsc", cp_file)
    assert cp["next_month"] == "2019-03"
    assert cp["completed_months"] == ["2019-01", "2019-02"]


def test_save_and_load_roundtrip(tmp_path):
    cp_file = tmp_path / "checkpoint.json"
    data = {
        "next_month": "2024-04",
        "completed_months": ["2024-05"],
        "failed_pages": [{"month": "2024-05", "page": 5, "error": "timeout"}],
    }
    save_checkpoint("tjsp", data, cp_file)
    loaded = load_checkpoint("tjsp", cp_file)
    assert loaded == data
