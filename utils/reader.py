from pathlib import Path
import json


def find_project_root() -> Path:
    current = Path(__file__).resolve()

    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists():
            return directory

    raise RuntimeError("Project root not found")


PROJECT_ROOT = find_project_root()


def load_file(path: str | Path) -> str:
    path = Path(path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)

    raise ValueError(
        f"Unsupported file format: {path.suffix}"
    )