from pydantic import BaseModel
from typing import Any, List, Optional

class ChatRequest(BaseModel):
    project_id: str
    user_input: str
    mode: Optional[str] = "auto"  # "auto" | "chat" | "mcp"
    chat_room_id: str
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    project_id: str
    route: str                # "chat" | "mcp" | "clarify"
    output: Any
    missing: Optional[List[str]] = None