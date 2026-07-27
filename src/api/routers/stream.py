"""
Server-Sent Events endpoint for real-time alert push.

The pipeline calls `notify_user(user_id, event)` after saving new changes.
Connected clients receive the event immediately via SSE.
"""
import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_current_user_sse
from src.db.models import User

router = APIRouter(prefix="/stream", tags=["stream"])

# In-memory queues keyed by user_id. Phase 3 replaces this with Redis pub/sub.
_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)


def notify_user(user_id: str, event: dict) -> None:
    """Called by the pipeline after new relevant changes are saved."""
    try:
        _queues[user_id].put_nowait(event)
    except asyncio.QueueFull:
        pass


async def _event_generator(user_id: str) -> AsyncGenerator[dict, None]:
    queue = _queues[user_id]
    yield {"event": "connected", "data": json.dumps({"status": "listening"})}
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=30)
            yield {"event": "alert", "data": json.dumps(event)}
        except asyncio.TimeoutError:
            yield {"event": "heartbeat", "data": ""}


@router.get("/alerts")
async def stream_alerts(current_user: User = Depends(get_current_user_sse)):
    return EventSourceResponse(_event_generator(current_user.id))
