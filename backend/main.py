from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Kapruka Companion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "kapruka-companion-api",
        "time": datetime.utcnow().isoformat(),
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    return {
        "reply": (
            "Ayubowan! I am Kapruka Companion. "
            "Tell me what you want to buy, who it is for, your budget, and delivery city."
        ),
        "received": request.message,
    }