from pathlib import Path


def safe_write(root: Path, relative_path: str, content: str) -> Path:
    """Write a file under root. Refuses absolute paths and '..' escapes."""
    root = root.resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Path escapes workspace: {relative_path!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target