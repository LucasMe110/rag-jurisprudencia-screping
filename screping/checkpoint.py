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


def _load_all(path: Path) -> dict:
    """Lê o arquivo inteiro como dict indexado por tribunal.

    Migra o formato flat antigo (com 'next_month' no topo) para {'tjsc': <conteúdo>}.
    """
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if "next_month" in data:
        return {"tjsc": data}
    return data


def load_checkpoint(tribunal: str, path: Path = CHECKPOINT_PATH) -> dict:
    data = _load_all(path)
    if tribunal not in data:
        return _default()
    return data[tribunal]


def save_checkpoint(tribunal: str, data: dict, path: Path = CHECKPOINT_PATH) -> None:
    all_data = _load_all(path)
    all_data[tribunal] = data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
