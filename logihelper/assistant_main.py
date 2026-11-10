import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import assistant_preprocessing as preprocessing
from . import log_generator as log

MODEL_NAME = "hf.co/mradermacher/ChipExpert-8B-Instruct-GGUF:Q4_K_M"
OLLAMA_URL = "http://127.0.0.1:11434"


def _ollama_request(endpoint, payload):
    request = Request(
        f"{OLLAMA_URL}/api/{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return urlopen(request, timeout=600)


def init_model(model_name):
    """Download the model on startup if it is missing from Ollama."""
    try:
        try:
            with _ollama_request("show", {"model": model_name}):
                return model_name
        except HTTPError as error:
            if error.code != 404:
                raise
            error.close()

        print(f"[Ollama] Downloading {model_name}...", flush=True)
        with _ollama_request("pull", {"model": model_name, "stream": False}) as response:
            result = json.load(response)
        if result.get("status") != "success":
            raise RuntimeError(result.get("error", f"Ollama pull failed: {result}"))
    except HTTPError as error:
        with error:
            detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama could not prepare {model_name}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Start Ollama at {OLLAMA_URL} before launching LogiHelper.") from error
    return model_name


def generate_answer(model, query_raw, stream=False):
    """
    Generate the answer to the question
    """
    query, detected_terms = preprocessing.normalize_user_query(query_raw)
    query += " .Строго обязательно отвечай на русском."
    print("[LOGS] Filtered user query:", query)
    extracted_context = preprocessing.get_from_guide(query, detected_terms)

    system_prompt = (
        "You are a tutor for cybernetics and digital logic. Answer using the reference below. "
        "Answer directly in at most three sentences. In sequential logic, keep the clock signal, "
        "stored state, and outputs distinct. Use plain text only. "
        "Do not draw diagrams, ASCII art, boxes, or tables. "
        "If the user writes in Russian you must translate your answer to Russian. Tell if you can't. Keep technical terms with English equivalents in parentheses. "
        "If the reference does not provide enough information, say so."
        + extracted_context
    )
    # if not extracted_context:
    #     answer = "В справке LogiHelper не нашлось сведений для ответа на этот вопрос."
    #     if stream:
    #         return iter((answer,))
    #     return {"generated_text": answer, "system_prompt": system_prompt}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query_raw}
    ]

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.5, "num_predict": 384},
    }

    def token_generator():
        with _ollama_request("chat", payload) as response:
            for line in response:
                chunk = json.loads(line)
                if "error" in chunk:
                    raise RuntimeError(chunk["error"])
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

    if stream:
        return token_generator()
    return {"generated_text": "".join(token_generator()), "system_prompt": system_prompt}


if __name__ == "__main__":
    query_raw = input()

    model_name = MODEL_NAME
    model = init_model(model_name)

    model_output = generate_answer(model, query_raw)

    # Generating logs for model
    log.generate_log(model_output["system_prompt"],
                     model_name,
                     query_raw,
                     model_output["generated_text"])

    print("[ASSISTANT]:", model_output["generated_text"])
