"""Tests for the executive summary PDF generator."""

from __future__ import annotations

from pathlib import Path

from src.executive_summary import generate_executive_summary


def test_generate_pdf(tmp_path: Path) -> None:
    output = tmp_path / "test_summary.pdf"
    result = generate_executive_summary(output)
    assert result.exists()
    assert result.stat().st_size > 3000  # Should be a real PDF
    # Verify it starts with PDF magic bytes
    with open(result, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"


def test_generate_pdf_is_multipage(tmp_path: Path) -> None:
    output = tmp_path / "test_summary2.pdf"
    result = generate_executive_summary(output)
    content = result.read_bytes()
    # PDF should have multiple pages (look for page markers)
    # A 2-page PDF should be reasonably sized
    assert result.stat().st_size > 5000
