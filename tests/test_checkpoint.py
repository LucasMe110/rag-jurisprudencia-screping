import json
import pytest
from pathlib import Path
from screping.checkpoint import load_checkpoint, save_checkpoint


def test_load_checkpoint_missing_file(tmp_path):
    cp = load_checkpoint(tmp_path / "checkpoint.json")
    assert cp["next_month"] == "2018-01"
    assert cp["completed_months"] == []
    assert cp["failed_pages"] == []


def test_load_checkpoint_existing_file(tmp_path):
    data = {
        "next_month": "2020-06",
        "completed_months": ["2020-04", "2020-05"],
        "failed_pages": [],
    }
    cp_file = tmp_path / "checkpoint.json"
    cp_file.write_text(json.dumps(data))
    cp = load_checkpoint(cp_file)
    assert cp["next_month"] == "2020-06"
    assert cp["completed_months"] == ["2020-04", "2020-05"]
    assert cp["failed_pages"] == []


def test_save_checkpoint(tmp_path):
    data = {
        "next_month": "2019-03",
        "completed_months": ["2019-01", "2019-02"],
        "failed_pages": [],
    }
    cp_file = tmp_path / "checkpoint.json"
    save_checkpoint(data, cp_file)
    saved = json.loads(cp_file.read_text())
    assert saved == data


def test_save_and_load_roundtrip(tmp_path):
    data = {
        "next_month": "2021-12",
        "completed_months": ["2021-10", "2021-11"],
        "failed_pages": [{"month": "2021-10", "page": 5, "error": "timeout"}],
    }
    cp_file = tmp_path / "checkpoint.json"
    save_checkpoint(data, cp_file)
    loaded = load_checkpoint(cp_file)
    assert loaded == data
