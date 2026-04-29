from pathlib import Path


def save_chart(png: bytes, path: Path) -> None:
    if not png:
        raise ValueError("png bytes are empty")
    if not path.parent.exists():
        raise FileNotFoundError(f"Directory does not exist: {path.parent}")
    path.write_bytes(png)
