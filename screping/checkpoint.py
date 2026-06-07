import json
from pathlib import Path

CHECKPOINT_PATH = Path(__file__).parent.parent / "checkpoint.json"

_DEFAULT: dict = {
    "next_month": "2018-01",
    "completed_months": [],
    "failed_pages": [],
}


def load_checkpoint(path: Path = CHECKPOINT_PATH) -> dict:
    if not Path(path).exists():
        return dict(_DEFAULT) | {"completed_months": [], "failed_pages": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(data: dict, path: Path = CHECKPOINT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
