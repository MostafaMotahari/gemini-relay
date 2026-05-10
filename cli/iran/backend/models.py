from pydantic import BaseModel
from typing import List, Optional


class ImageInput(BaseModel):
    mime_type: str
    data: str


class ChatRequest(BaseModel):
    message: str
    images: Optional[List[ImageInput]] = []
    metadata: Optional[dict] = {}