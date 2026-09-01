from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from starlette.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # TODO: connect QWEN
    bot_response = 'successful response'

    return {"reply": bot_response}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
