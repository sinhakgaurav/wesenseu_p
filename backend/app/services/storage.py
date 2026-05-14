"""
File storage service.
- STORAGE_BACKEND=local  → saves to ./media/ and serves via /media/ (default)
- STORAGE_BACKEND=s3     → uploads to AWS S3 / MinIO / Cloudflare R2
Switch by setting STORAGE_BACKEND in your .env file.
"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.core.config import settings

MEDIA_ROOT = Path("media")
MEDIA_ROOT.mkdir(exist_ok=True)


def _s3_client():
    try:
        import boto3
        kwargs = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        return boto3.client("s3", **kwargs)
    except Exception:
        return None


def _use_s3() -> bool:
    if settings.STORAGE_BACKEND == "local":
        return False
    return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)


async def upload_file(file: UploadFile, folder: str = "uploads") -> str:
    """Upload a file and return its public URL."""
    ext = Path(file.filename or "file").suffix or ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"{folder}/{filename}"

    content = await file.read()

    if _use_s3():
        return await _upload_s3(content, key, file.content_type or "application/octet-stream")
    return await _save_local(content, key)


async def _upload_s3(content: bytes, key: str, content_type: str) -> str:
    import asyncio
    client = _s3_client()
    if not client:
        raise RuntimeError("S3 client could not be initialised")

    def _put():
        client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    await asyncio.to_thread(_put)

    if settings.S3_ENDPOINT_URL:
        return f"{settings.S3_ENDPOINT_URL}/{settings.AWS_BUCKET_NAME}/{key}"
    return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


async def _save_local(content: bytes, key: str) -> str:
    dest = MEDIA_ROOT / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)
    return f"/media/{key}"


async def delete_file(url: str) -> None:
    """Best-effort delete. Does not raise on failure."""
    try:
        if _use_s3() and "amazonaws.com" in url:
            import asyncio
            key = url.split(".amazonaws.com/")[-1]
            client = _s3_client()
            if client:
                await asyncio.to_thread(
                    client.delete_object,
                    Bucket=settings.AWS_BUCKET_NAME,
                    Key=key,
                )
        elif url.startswith("/media/"):
            local_path = MEDIA_ROOT / url.removeprefix("/media/")
            if local_path.exists():
                local_path.unlink()
    except Exception:
        pass
