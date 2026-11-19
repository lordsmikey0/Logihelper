import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
from starlette.responses import HTMLResponse
from logihelper.assistant_main import MODEL_NAME, OllamaChatError, generate_answer, init_model
from logihelper.circ_parser import CircParser


WEB_DIR = Path(__file__).resolve().parent / "web"
logger = logging.getLogger("uvicorn.error")


app = FastAPI()

model = init_model(MODEL_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/css", StaticFiles(directory=WEB_DIR / "static" / "css"), name="css")
app.mount("/js", StaticFiles(directory=WEB_DIR / "static" / "js"), name="js")


class CircuitFile(BaseModel):
    name: str
    content: str


class Message(BaseModel):
    text: str
    circuit: CircuitFile | None = None


@app.get("/", response_class=HTMLResponse)
def get_home_page():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/ask")
def ask_assistant(message: Message):
    circuit_description = ""
    if message.circuit is not None:
        if not message.circuit.name.lower().endswith(".circ"):
            return PlainTextResponse("Выберите файл с расширением .circ.", status_code=400)
        try:
            circuit_description = CircParser.parse_text(message.circuit.content).describe_circuit()
        except (ET.ParseError, ValueError, AttributeError, TypeError) as error:
            logger.info("Circuit parsing failed: %s", error)
            return PlainTextResponse(
                "Не удалось разобрать схему. Проверьте файл .circ и поддерживаемые компоненты.",
                status_code=400,
            )
    result = generate_answer(model, message.text, stream=True, circuit_description=circuit_description)

    try:
        first_chunk = next(result, "")
    except OllamaChatError as error:
        logger.warning("Ollama request failed for %s: %s", model, error)
        return PlainTextResponse(
            "Ollama не смогла начать генерацию. Подробности ошибки есть в терминале сервера.",
            status_code=502,
        )

    def stream_reply():
        yield first_chunk
        try:
            yield from result
        except OllamaChatError as error:
            logger.warning("Ollama response interrupted for %s: %s", model, error)
            yield "\n\nОтвет прервался на стороне Ollama. Попробуйте отправить сообщение ещё раз."

    return StreamingResponse(stream_reply(), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
