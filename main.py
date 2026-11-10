from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from starlette.responses import HTMLResponse
from logihelper.assistant_main import MODEL_NAME, init_model, generate_answer


WEB_DIR = Path(__file__).resolve().parent / "web"


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


class Message(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def get_home_page():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/ask")
def ask_assistant(message: Message):
    user_text = message.text
    result = generate_answer(model, message.text, stream=True)

    return StreamingResponse(result, media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
