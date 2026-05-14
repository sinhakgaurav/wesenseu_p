"""
WesenseU AI Room Verification Service.
When WESENSEU_API_KEY is set, calls the real API.
Falls back to a deterministic mock for development/demo.
"""
import asyncio
import random
from typing import Optional
import httpx

from app.core.config import settings


DEFECT_TYPES = [
    "dirty_floor", "unmade_bed", "stained_linen", "dusty_surfaces",
    "missing_amenities", "wet_bathroom", "damaged_furniture",
]


async def verify_room_images(image_urls: list[str], room_number: str = "") -> dict:
    """
    Submit room images for AI verification.
    Returns: { score, status, defects, raw_response }
    """
    if settings.WESENSEU_API_KEY:
        return await _call_wesenseu_api(image_urls, room_number)
    return await _mock_verification(image_urls, room_number)


async def _call_wesenseu_api(image_urls: list[str], room_number: str) -> dict:
    payload = {
        "room_id": room_number,
        "images": image_urls,
        "check_items": [
            "bed_making", "floor_cleanliness", "bathroom", "amenities",
            "furniture", "linen", "windows", "dust",
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.WESENSEU_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{settings.WESENSEU_API_URL}/verify",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            score = float(data.get("score", 0))
            defects = data.get("defects", [])
            status = "approved" if score >= 80 else "rejected"

            return {
                "score": score,
                "status": status,
                "defects": defects,
                "raw_response": data,
            }
        except httpx.HTTPError as e:
            return {
                "score": 0,
                "status": "error",
                "defects": [],
                "raw_response": {"error": str(e)},
            }


async def _mock_verification(image_urls: list[str], room_number: str) -> dict:
    """Deterministic mock — simulates real API latency and response shape."""
    await asyncio.sleep(1.5)  # simulate network call

    num_images = len(image_urls)
    base_score = min(95, 60 + num_images * 8 + random.randint(0, 15))

    defects = []
    if base_score < 80:
        defects = random.sample(DEFECT_TYPES, k=random.randint(1, 3))

    status = "approved" if base_score >= 80 else "rejected"

    return {
        "score": float(base_score),
        "status": status,
        "defects": [{"type": d, "severity": "minor", "location": "room"} for d in defects],
        "raw_response": {
            "mock": True,
            "message": "Set WESENSEU_API_KEY in .env for live AI verification",
            "score": base_score,
            "room": room_number,
            "images_analysed": num_images,
        },
    }
