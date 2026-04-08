import io
import os
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from src.config import config
from src.logger import app_logger

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/msword",
    "application/vnd.ms-excel",
    "text/plain",
}
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
FILE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "text/plain": ".txt",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_FILE_SIZE = 20 * 1024 * 1024    # 20 MB

THUMBNAIL_SIZE = (640, 360)  # 16:9


def make_thumbnail(data: bytes) -> bytes:
    """Center-crop to 16:9 and resize to THUMBNAIL_SIZE, return JPEG bytes."""
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        w, h = img.size
        target_ratio = 16 / 9
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        elif current_ratio < target_ratio:
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))
        img = img.resize(THUMBNAIL_SIZE, Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()


def save_upload(file: UploadFile, subdir: str, allowed_types: dict[str, str], max_size: int) -> str:
    """Save an uploaded file to DATA_PATH/subdir, return relative path."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = file.file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size // (1024 * 1024)} MB.",
        )

    ext = allowed_types[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    dest_dir = os.path.join(config.DATA_PATH, subdir)
    os.makedirs(dest_dir, exist_ok=True)

    with open(os.path.join(dest_dir, filename), "wb") as f:
        f.write(contents)

    return f"{subdir}/{filename}"


def delete_file(relative_path: str) -> None:
    """Delete a file from DATA_PATH by its relative path. Silently ignores missing files."""
    if not relative_path:
        return
    full_path = os.path.join(config.DATA_PATH, relative_path)
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
    except Exception as e:
        app_logger.warning(f"Could not delete file {full_path}: {e}")
