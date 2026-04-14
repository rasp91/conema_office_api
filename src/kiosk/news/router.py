from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select
from fastapi import status, HTTPException, APIRouter, Depends

from src.database.models.kiosk_news_documents import NewsDocument
from src.database.models.kiosk_news_items import NewsItem
from src.kiosk.news.schemas import (
    NewsDocumentCreateModel,
    NewsItemUpdateModel,
    NewsItemCreateModel,
    NewsDocumentModel,
    ResponseModel,
    NewsItemModel,
)
from src.database import get_db
from src.upload import delete_file
from src.logger import app_logger
from src.auth import get_auth_user

router = APIRouter()


def _get_news_item_or_404(news_id: int, db: Session) -> NewsItem:
    item = db.execute(select(NewsItem).where(NewsItem.id == news_id).options(selectinload(NewsItem.documents))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found.")
    return item


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get News",
    response_model=list[NewsItemModel],
)
def get_news(db: Session = Depends(get_db)) -> list[NewsItem]:
    try:
        items = (
            db.execute(
                select(NewsItem)
                .where(NewsItem.is_visible == True)  # noqa: E712
                .options(selectinload(NewsItem.documents))
                .order_by(NewsItem.published_at.desc())
            )
            .scalars()
            .all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch news.")


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    name="Get All News",
    dependencies=[Depends(get_auth_user)],
    response_model=list[NewsItemModel],
)
def get_all_news(db: Session = Depends(get_db)) -> list[NewsItem]:
    try:
        items = (
            db.execute(select(NewsItem).options(selectinload(NewsItem.documents)).order_by(NewsItem.published_at.desc())).scalars().all()
        )
        return items
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch news.")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="Create News",
    dependencies=[Depends(get_auth_user)],
    response_model=NewsItemModel,
)
def create_news(data: NewsItemCreateModel, db: Session = Depends(get_db)) -> NewsItem:
    try:
        item = NewsItem(
            published_at=data.published_at,
            title=data.title,
            description=data.description,
            thumbnail_path=data.thumbnail_path,
            is_visible=data.is_visible,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        # Load documents relationship (empty on create)
        db.execute(select(NewsItem).where(NewsItem.id == item.id).options(selectinload(NewsItem.documents))).scalar_one()
        return item
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create news item.")


@router.put(
    "/{news_id}",
    status_code=status.HTTP_200_OK,
    name="Update News",
    dependencies=[Depends(get_auth_user)],
    response_model=NewsItemModel,
)
def update_news(news_id: int, data: NewsItemUpdateModel, db: Session = Depends(get_db)) -> NewsItem:
    try:
        item = _get_news_item_or_404(news_id, db)

        if data.published_at is not None:
            item.published_at = data.published_at
        if data.title is not None:
            item.title = data.title
        if data.description is not None:
            item.description = data.description
        if data.is_visible is not None:
            item.is_visible = data.is_visible
        # Allow explicitly setting thumbnail_path to None (removal)
        if "thumbnail_path" in data.model_fields_set:
            # Delete old thumbnail if being replaced or cleared
            if item.thumbnail_path and item.thumbnail_path != data.thumbnail_path:
                delete_file(item.thumbnail_path)
            item.thumbnail_path = data.thumbnail_path

        db.commit()
        db.refresh(item)
        return item
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update news item.")


@router.delete(
    "/{news_id}",
    status_code=status.HTTP_200_OK,
    name="Delete News",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_news(news_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = _get_news_item_or_404(news_id, db)

        # Delete all associated files from disk
        if item.thumbnail_path:
            delete_file(item.thumbnail_path)
        for doc in item.documents:
            delete_file(doc.file_path)

        db.delete(item)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete news item.")


@router.post(
    "/{news_id}/views",
    status_code=status.HTTP_200_OK,
    name="Increment News Views",
    response_model=ResponseModel,
)
def increment_views(news_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        item = db.execute(select(NewsItem).where(NewsItem.id == news_id)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found.")
        item.views = (item.views or 0) + 1
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to increment views.")


@router.post(
    "/{news_id}/documents",
    status_code=status.HTTP_201_CREATED,
    name="Add News Document",
    dependencies=[Depends(get_auth_user)],
    response_model=NewsDocumentModel,
)
def add_document(news_id: int, data: NewsDocumentCreateModel, db: Session = Depends(get_db)) -> NewsDocument:
    try:
        _get_news_item_or_404(news_id, db)
        doc = NewsDocument(
            news_item_id=news_id,
            name=data.name,
            file_path=data.file_path,
            type=data.type,
            sort_order=data.sort_order,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add document.")


@router.delete(
    "/{news_id}/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
    name="Delete News Document",
    dependencies=[Depends(get_auth_user)],
    response_model=ResponseModel,
)
def delete_document(news_id: int, doc_id: int, db: Session = Depends(get_db)) -> ResponseModel:
    try:
        doc = db.execute(select(NewsDocument).where(NewsDocument.id == doc_id, NewsDocument.news_item_id == news_id)).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        delete_file(doc.file_path)
        db.delete(doc)
        db.commit()
        return ResponseModel()
    except HTTPException:
        raise
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document.")
