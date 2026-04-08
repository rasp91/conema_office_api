import uuid
import os

from pydantic import BaseModel
from fastapi import status, HTTPException, UploadFile, APIRouter

from src.upload import make_thumbnail, save_upload, ALLOWED_IMAGE_TYPES, IMAGE_EXTENSIONS, FILE_EXTENSIONS, MAX_IMAGE_SIZE, MAX_FILE_SIZE
from src.logger import app_logger
from src.config import config

router = APIRouter()


class UploadResponse(BaseModel):
    path: str


@router.post(
    "/image",
    status_code=status.HTTP_200_OK,
    name="Upload Image",
    response_model=UploadResponse,
)
def upload_image(file: UploadFile, subdir: str = "news/images") -> UploadResponse:
    """Upload an image. Use subdir to specify target folder (e.g. 'news/images', 'news/thumbnails')."""
    try:
        path = save_upload(file, subdir, IMAGE_EXTENSIONS, MAX_IMAGE_SIZE)
        return UploadResponse(path=path)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image.")


@router.post(
    "/image/thumbnail",
    status_code=status.HTTP_200_OK,
    name="Upload Thumbnail",
    response_model=UploadResponse,
)
def upload_thumbnail(file: UploadFile, subdir: str = "news/thumbnails") -> UploadResponse:
    """Upload an image, center-crop to 16:9 and resize to 640×360, save as JPEG."""
    try:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file.content_type}",
            )
        contents = file.file.read()
        if len(contents) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_IMAGE_SIZE // (1024 * 1024)} MB.",
            )
        thumb_data = make_thumbnail(contents)
        filename = f"{uuid.uuid4()}.jpg"
        dest_dir = os.path.join(config.DATA_PATH, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        with open(os.path.join(dest_dir, filename), "wb") as f:
            f.write(thumb_data)
        return UploadResponse(path=f"{subdir}/{filename}")
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload thumbnail.")


@router.post(
    "/file",
    status_code=status.HTTP_200_OK,
    name="Upload File",
    response_model=UploadResponse,
)
def upload_file(file: UploadFile, subdir: str = "news/files") -> UploadResponse:
    """Upload a document file. Use subdir to specify target folder (e.g. 'news/files')."""
    try:
        path = save_upload(file, subdir, FILE_EXTENSIONS, MAX_FILE_SIZE)
        return UploadResponse(path=path)
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file.")
