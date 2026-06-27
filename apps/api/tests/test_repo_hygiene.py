from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]


def test_env_is_ignored_and_example_is_present():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore
    assert "!/.env.example" not in gitignore
    assert (ROOT / ".env.example").exists()


def test_no_obvious_secret_values_committed():
    example = (ROOT / ".env.example").read_text()
    assert "change-me" in example
    assert not re.search(r"\bsk-[A-Za-z0-9]{20,}\b", example)
    assert "AKIA" not in example
