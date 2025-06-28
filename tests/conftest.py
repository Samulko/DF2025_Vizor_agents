"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Disable logging during tests unless explicitly needed
import logging

logging.disable(logging.CRITICAL)


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging after each test."""
    yield
    logging.disable(logging.CRITICAL)


@pytest.fixture
def test_env(monkeypatch):
    """Set up test environment variables."""
    test_vars = {
        "OPENAI_API_KEY": "test_key",
        "ANTHROPIC_API_KEY": "test_key",
        "DEEPSEEK_API_KEY": "test_key",
        "TRIAGE_AGENT_PROVIDER": "openai",
        "TRIAGE_AGENT_MODEL": "gpt-4",
        "LOG_LEVEL": "ERROR",
        "MAX_AGENT_STEPS": "5",
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    yield test_vars
