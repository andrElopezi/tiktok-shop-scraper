import json
from pathlib import Path
from typing import Iterable, Any
from rich.console import Console

console = Console()

def export_json(data: Iterable[dict], output_path: str | Path) -> Path:
    """
    Write iterable of product dicts to a JSON file with UTF-8 encoding.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(list(data), f, ensure_ascii=False, indent=2)
    console.log(f"[green]Wrote {output_path}[/green]")
    return output_path