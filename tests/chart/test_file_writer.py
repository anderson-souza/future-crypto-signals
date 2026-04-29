from pathlib import Path

import pytest

from src.chart.file_writer import save_chart


def test_writes_file(tmp_path):
    path = tmp_path / "chart.png"
    save_chart(b"fakepng", path)
    assert path.exists()
    assert path.read_bytes() == b"fakepng"


def test_parent_missing_raises(tmp_path):
    path = tmp_path / "nonexistent_dir" / "chart.png"
    with pytest.raises(FileNotFoundError):
        save_chart(b"fakepng", path)


def test_empty_bytes_raises(tmp_path):
    path = tmp_path / "chart.png"
    with pytest.raises(ValueError, match="png bytes are empty"):
        save_chart(b"", path)
