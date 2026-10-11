import json
from pathlib import Path

MEMORY_FILE = Path('data/chat_history.json')


def memory_entry(user_input: str, model_response: str) -> None:
    """Make an entry to the memory file for the model to read"""
    entry = {
        "user": user_input,
        "response": model_response
    }
    if MEMORY_FILE.exists():
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=3)
    else:
        with MEMORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=3)


def memory_read() -> None:
    """Read the memory file"""
    if MEMORY_FILE.exists():
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
