from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
