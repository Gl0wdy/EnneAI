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
    if path: sys_path = Path(path)
    else: return 'None'

    if not sys_path.is_absolute():
        sys_path = PROJECT_ROOT / path

    sys_path = sys_path.resolve()

    if not sys_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not sys_path.is_file():
        raise ValueError(f"Not a file: {path}")

    if sys_path.suffix.lower() == ".txt":
        return sys_path.read_text(encoding="utf-8")

    if sys_path.suffix.lower() == ".json":
        data = json.loads(sys_path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)

    raise ValueError(
        f"Unsupported file format: {sys_path.suffix}"
    )