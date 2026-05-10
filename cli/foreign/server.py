import os
import re
import json
import base64
import shutil
import tempfile
import subprocess

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()

TMP_DIR = "tmp"

GEMINI_TIMEOUT = 300


class ImageInput(BaseModel):
    mime_type: str
    data: str


class ProcessRequest(BaseModel):
    prompt: str
    images: Optional[List[ImageInput]] = []


def check_gemini():
    if shutil.which("gemini") is None:
        raise RuntimeError("gemini CLI not found")


def save_image(image: ImageInput) -> str:
    ext_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }

    ext = ext_map.get(image.mime_type, ".jpg")

    image_bytes = base64.b64decode(image.data)

    os.makedirs(TMP_DIR, exist_ok=True)

    tmp = tempfile.NamedTemporaryFile(
        suffix=ext,
        delete=False,
        dir=TMP_DIR
    )

    tmp.write(image_bytes)
    tmp.close()

    return tmp.name


def build_gemini_command(prompt: str, image_paths: List[str]):
    full_prompt = prompt

    for path in image_paths:
        full_prompt += f" @{path}"

    return ["gemini", "-y", full_prompt]


def run_gemini(prompt: str, image_paths: List[str]) -> str:
    command = build_gemini_command(prompt, image_paths)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=GEMINI_TIMEOUT
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip()


@app.post("/process")
async def process(request: ProcessRequest):
    temp_files = []

    try:
        # check_gemini()

        for image in request.images:
            path = save_image(image)
            temp_files.append(path)

        output = run_gemini(
            prompt=request.prompt,
            image_paths=temp_files
        )

        return {
            "success": True,
            "response": output
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass


@app.get("/health")
async def health():
    try:
        check_gemini()

        return {
            "status": "healthy"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )