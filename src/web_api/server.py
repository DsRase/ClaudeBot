from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import yaml
import os

app = FastAPI(title="ClaudeBot Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str
    thread_id: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

class ModelsResponse(BaseModel):
    default: str
    available: List[str]

def load_config():
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        config_path = "config.example.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

import asyncio

## МЕНЯТЬ
def get_response(message: str, user_id: str, model: str = None) -> str:
    import time
    time.sleep(2)
    return f"Вы написали: {message}"

@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    config = load_config()
    return ModelsResponse(
        default=config.get("default_model", "claude-opus-4.7"),
        available=config.get("available_models", [])
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    thread_id = request.thread_id or request.user_id
    response = get_response(request.message, request.user_id, request.model)
    return ChatResponse(response=response, thread_id=thread_id)

@app.get("/api/health")
async def health():
    return {"status": "ok"}