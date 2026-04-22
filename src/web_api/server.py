from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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

class ChatResponse(BaseModel):
    response: str
    thread_id: str

def get_response(message: str, user_id: str) -> str:
    return f"Вы написали: {message}"

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    thread_id = request.thread_id or request.user_id
    response = get_response(request.message, request.user_id)
    return ChatResponse(response=response, thread_id=thread_id)

@app.get("/api/health")
async def health():
    return {"status": "ok"}