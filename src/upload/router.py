import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import config
from src.logger import app_logger

router = APIRouter()

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


class UploadResponse(BaseModel):
    path: str


def _save_upload(file: UploadFile, subdir: str, allowed_types: dict[str, str], max_size: int) -> str:
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

    dest_path = os.path.join(dest_dir, filename)
    with open(dest_path, "wb") as f:
        f.write(contents)

    return f"{subdir}/{filename}"


@router.post(
    "/image",
    status_code=status.HTTP_200_OK,
    name="Upload Image",
    response_model=UploadResponse,
)
def upload_image(file: UploadFile, subdir: str = "news/images") -> UploadResponse:
    """Upload an image. Use subdir to specify target folder (e.g. 'news/images', 'news/thumbnails')."""
    try:
        path = _save_upload(file, subdir, IMAGE_EXTENSIONS, MAX_IMAGE_SIZE)
        return UploadResponse(path=path)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image.")


@router.post(
    "/file",
    status_code=status.HTTP_200_OK,
    name="Upload File",
    response_model=UploadResponse,
)
def upload_file(file: UploadFile, subdir: str = "news/files") -> UploadResponse:
    """Upload a document file. Use subdir to specify target folder (e.g. 'news/files')."""
    try:
        path = _save_upload(file, subdir, FILE_EXTENSIONS, MAX_FILE_SIZE)
        return UploadResponse(path=path)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file.")


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
