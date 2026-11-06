from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from starlette.responses import HTMLResponse
from assistant_main import MODEL_NAME, init_model, generate_answer


app = FastAPI()

model = init_model(MODEL_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")


class Message(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def get_home_page():
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content


@app.post("/ask")
def ask_assistant(message: Message):
    user_text = message.text
    result = generate_answer(model, message.text, stream=True)

    return StreamingResponse(result, media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
