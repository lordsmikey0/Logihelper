import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path('logs.jsonl')

def generate_log(
        system_prompt: str,
        model_name: str,
        user_input:str,
        assistant_response: str,
        ) -> None:
    if LOG_FILE.exists():
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_prompt": system_prompt,
            "model_name": model_name,
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")