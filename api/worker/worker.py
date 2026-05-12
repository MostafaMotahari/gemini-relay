import json
import asyncio

from redis_client import redis_client
from config import (
    PENDING_QUEUE,
    PROCESSING_QUEUE,
    MAX_RETRIES,
    RESULT_EXPIRE_SECONDS,
    KEY_COOLDOWN_SECONDS,
)

from key_manager import (
    get_available_key,
    cooldown_key,
)

from gemini import generate


async def store_result(job_id, status, result):
    redis_client.setex(
        f"job:{job_id}:status",
        RESULT_EXPIRE_SECONDS,
        status
    )

    redis_client.setex(
        f"job:{job_id}:result",
        RESULT_EXPIRE_SECONDS,
        result
    )


async def process_job(raw_job):
    job = json.loads(raw_job)

    job_id = job["job_id"]

    key_data = get_available_key()

    if not key_data:
        print("No available API keys")

        redis_client.rpush(PENDING_QUEUE, raw_job)

        await asyncio.sleep(5)
        return

    redis_client.set(
        f"job:{job_id}:status",
        "processing"
    )

    try:
        response = await generate(
            api_key=key_data["api_key"],
            prompt=job["prompt"],
            images=job["images"]
        )

        await store_result(
            job_id,
            "done",
            response
        )

        redis_client.lrem(
            PROCESSING_QUEUE,
            1,
            raw_job
        )

        print(f"Job completed: {job_id}")

    except Exception as e:
        error_text = str(e)

        redis_client.lrem(
            PROCESSING_QUEUE,
            1,
            raw_job
        )

        if "429" in error_text or "quota" in error_text.lower():
            print("API key exhausted")

            cooldown_key(
                key_data["redis_key"],
                KEY_COOLDOWN_SECONDS
            )

            redis_client.rpush(
                PENDING_QUEUE,
                raw_job
            )

            return

        job["retry_count"] += 1

        if job["retry_count"] >= MAX_RETRIES:
            await store_result(
                job_id,
                "failed",
                error_text
            )

            print(f"Job permanently failed: {job_id}")
            return

        redis_client.rpush(
            PENDING_QUEUE,
            json.dumps(job)
        )

        print(error_text)
        print(f"Retrying job: {job_id}")


async def worker_loop(worker_id):
    while True:
        result = redis_client.brpoplpush(
            PENDING_QUEUE,
            PROCESSING_QUEUE,
            timeout=0
        )

        if not result:
            continue

        await process_job(result)


async def main():
    key_count = len(redis_client.keys("apikey:*"))

    if key_count == 0:
        raise RuntimeError("No API keys configured")

    tasks = []

    for i in range(key_count):
        tasks.append(worker_loop(i))

    await asyncio.gather(*tasks)


asyncio.run(main())