import json
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest
from redis_client import redis_client
from config import PENDING_QUEUE


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat")
async def create_job(payload: ChatRequest):
    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "prompt": payload.prompt,
        "images": [img.model_dump() for img in payload.images],
        "retry_count": 0
    }

    redis_client.rpush(
        PENDING_QUEUE,
        json.dumps(job)
    )

    redis_client.set(
        f"job:{job_id}:status",
        "queued"
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": "queued"
    }


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    status = redis_client.get(f"job:{job_id}:status")

    if not status:
        return JSONResponse(
            {
                "success": False,
                "error": "job_not_found"
            },
            status_code=404
        )

    result = redis_client.get(f"job:{job_id}:result")

    return {
        "success": True,
        "job_id": job_id,
    }