from pydantic import BaseModel
from typing import Optional, List


class ImageInput(BaseModel):
    mime_type: str
    data: str


class ChatRequest(BaseModel):
    prompt: str
    images: Optional[List[ImageInput]] = []