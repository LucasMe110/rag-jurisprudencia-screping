import datetime
import json
from pathlib import Path

CHECKPOINT_PATH = Path(__file__).parent.parent / "checkpoint.json"


def _current_month_str() -> str:
    today = datetime.date.today()
    return f"{today.year}-{today.month:02d}"


def _default() -> dict:
    return {
        "next_month": _current_month_str(),
        "completed_months": [],
        "failed_pages": [],
    }


def load_checkpoint(path: Path = CHECKPOINT_PATH) -> dict:
    if not Path(path).exists():
        return _default()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(data: dict, path: Path = CHECKPOINT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
