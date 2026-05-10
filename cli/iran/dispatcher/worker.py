import json
import aiohttp
import asyncio

from redis_client import redis_client
from config import QUEUE_NAME, SERVER2_URL, HTTP_PROXY


async def process_job(job):
    job_id = job["job_id"]

    redis_client.set(f"job:{job_id}:status", "processing")

    timeout = aiohttp.ClientTimeout(total=300)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            SERVER2_URL,
            json=job,
            proxy=HTTP_PROXY
        ) as response:

            text = await response.text()

            redis_client.set(f"job:{job_id}:status", "done")
            redis_client.set(f"job:{job_id}:result", text)


async def worker_loop():
    while True:
        _, raw_job = redis_client.blpop(QUEUE_NAME)

        job = json.loads(raw_job)

        try:
            await process_job(job)

        except Exception as e:
            redis_client.set(
                f"job:{job['job_id']}:status",
                "failed"
            )

            redis_client.set(
                f"job:{job['job_id']}:result",
                str(e)
            )

        await asyncio.sleep(0)


asyncio.run(worker_loop())