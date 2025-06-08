"""
Tests for the quality module.
"""
from app.core.quality import QualityGate, ensure_quality


def test_quality_gate_init():
    """Test QualityGate initialization."""
    gate = QualityGate(threshold=90)
    assert gate.threshold == 90
    assert gate.status == "PASSED"


def test_quality_gate_check_coverage():
    """Test coverage check functionality."""
    gate = QualityGate(threshold=80)
    assert gate.check_coverage(85) is True
    assert gate.check_coverage(75) is False


def test_quality_gate_status():
    """Test status getter and setter."""
    gate = QualityGate()
    assert gate.get_status() == "PASSED"

    gate.set_status("FAILED")
    assert gate.get_status() == "FAILED"


def test_ensure_quality():
    """Test ensure_quality function."""
    assert ensure_quality() is True
