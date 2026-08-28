from pathlib import Path
import json


def find_project_root() -> Path:
    current = Path(__file__).resolve()

    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists():
            return directory

    raise RuntimeError("Project root not found")


PROJECT_ROOT = find_project_root()


def _load_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(parts)


def _load_pdf(path: Path) -> str:
    import pymupdf 

    doc = pymupdf.open(str(path))
    try:
        parts = [page.get_text() for page in doc]
    finally:
        doc.close()
    return "\n\n".join(p for p in parts if p.strip())


def load_file(path: str | Path) -> str:
    path = Path(path)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False, indent=2)

    if suffix == ".docx":
        return _load_docx(path)

    if suffix == ".pdf":
        return _load_pdf(path)

    raise ValueError(
        f"Unsupported file format: {path.suffix}"
    )