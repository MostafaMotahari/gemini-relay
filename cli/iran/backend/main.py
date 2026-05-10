import json
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from models import ChatRequest
from redis_client import redis_client
from config import QUEUE_NAME


app = FastAPI()


@app.post("/api/chat")
async def create_chat_job(payload: ChatRequest):
    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "message": payload.message,
        "images": [img.model_dump() for img in payload.images],
        "metadata": payload.metadata,
    }

    redis_client.rpush(QUEUE_NAME, json.dumps(job))

    redis_client.set(f"job:{job_id}:status", "queued")

    return JSONResponse({
        "success": True,
        "job_id": job_id,
        "status": "queued"
    })


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    status = redis_client.get(f"job:{job_id}:status")

    if not status:
        return JSONResponse({
            "success": False,
            "error": "job_not_found"
        }, status_code=404)

    result = redis_client.get(f"job:{job_id}:result")

    return JSONResponse({
        "success": True,
        "job_id": job_id,
        "status": status,
        "result": result
    })