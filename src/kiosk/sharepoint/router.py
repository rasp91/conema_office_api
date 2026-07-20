import threading
from datetime import timedelta, timezone, datetime

from sqlalchemy.orm import selectinload, Session
from sqlalchemy import select
from fastapi import status, BackgroundTasks, HTTPException, APIRouter, Depends, Header, Query

from src.database.models.kiosk_sharepoint_article_divisions import SharePointArticleDivision
from src.database.models.kiosk_sharepoint_articles import SharePointArticle
from src.kiosk.sharepoint.graph_client import GraphAPIError
from src.kiosk.sharepoint.schemas import SharePointArticleDetailModel, SharePointArticleModel, SyncResponseModel
from src.kiosk.sharepoint import graph_client, sync
from src.database import get_db, SessionLocal
from src.logger import app_logger
from src.config import config

router = APIRouter()

_sync_lock = threading.Lock()
_sync_running = False


def _verify_sync_key(sync_key: str = Header(..., alias="SYNC-KEY")) -> None:
    # Separate from verify_api_key (already applied to this whole router) since that key is
    # bundled into the public kiosk frontend - this endpoint mutates the DB and should need a
    # secret only the external scheduler (scripts/sync-sharepoint.ps1) knows.
    if sync_key != config.SP_SYNC_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync key")


def _run_background_sync() -> None:
    global _sync_running
    db = SessionLocal()
    try:
        count = sync.sync_articles(db)
        app_logger.info(f"SharePoint background sync completed: {count} articles.")
    except Exception as e:
        app_logger.exception(e)
    finally:
        db.close()
        with _sync_lock:
            _sync_running = False


def _maybe_trigger_background_sync(background_tasks: BackgroundTasks, db: Session) -> None:
    global _sync_running
    last_sync = sync.get_last_sync(db)
    if last_sync and (datetime.now(timezone.utc) - last_sync) < timedelta(minutes=config.SP_SYNC_INTERVAL_MINUTES):
        return
    with _sync_lock:
        if _sync_running:
            return
        _sync_running = True
    background_tasks.add_task(_run_background_sync)


def _run_background_refresh(detail: dict) -> None:
    db = SessionLocal()
    try:
        sync.upsert_article_from_detail(db, detail)
    except Exception as e:
        app_logger.exception(e)
    finally:
        db.close()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="Get SharePoint Articles",
    response_model=list[SharePointArticleModel],
)
def get_sharepoint_articles(
    background_tasks: BackgroundTasks,
    limit: int = Query(default=config.SP_ARTICLES_LIMIT, ge=1, le=200),
    division: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SharePointArticle]:
    try:
        _maybe_trigger_background_sync(background_tasks, db)
        query = (
            select(SharePointArticle)
            .options(selectinload(SharePointArticle.division_links))
            .order_by(SharePointArticle.published_at.desc())
            .limit(limit)
        )
        if division is not None:
            query = query.join(SharePointArticleDivision).where(SharePointArticleDivision.division == division)
        return db.execute(query).scalars().all()
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch SharePoint articles.")


@router.get(
    "/divisions",
    status_code=status.HTTP_200_OK,
    name="Get SharePoint Divisions",
    response_model=list[str],
)
def get_sharepoint_divisions(db: Session = Depends(get_db)) -> list[str]:
    # Divisions aren't a fixed set - this reflects whatever values are actually present
    # in the locally synced articles, so the kiosk never offers a filter that would
    # render an empty grid.
    try:
        return (
            db.execute(select(SharePointArticleDivision.division).distinct().order_by(SharePointArticleDivision.division)).scalars().all()
        )
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch SharePoint divisions.")


@router.post(
    "/sync",
    status_code=status.HTTP_200_OK,
    name="Sync SharePoint Articles",
    dependencies=[Depends(_verify_sync_key)],
    response_model=SyncResponseModel,
)
def sync_sharepoint_articles(db: Session = Depends(get_db)) -> SyncResponseModel:
    # Shares _sync_lock/_sync_running with the background auto-trigger so a scheduler-invoked
    # sync can't overlap an in-progress one - _sync_divisions replaces division rows via
    # delete-then-insert, which isn't safe under concurrent syncs of the same article id.
    global _sync_running
    with _sync_lock:
        if _sync_running:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A SharePoint sync is already running.")
        _sync_running = True
    try:
        return SyncResponseModel(synced=sync.sync_articles(db))
    except GraphAPIError as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="SharePoint service unavailable.")
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync SharePoint articles.")
    finally:
        with _sync_lock:
            _sync_running = False


@router.get(
    "/{article_id}",
    status_code=status.HTTP_200_OK,
    name="Get SharePoint Article",
    response_model=SharePointArticleDetailModel,
)
def get_sharepoint_article(article_id: str, background_tasks: BackgroundTasks) -> dict:
    try:
        detail = graph_client.get_article(article_id)
        background_tasks.add_task(_run_background_refresh, detail)
        return detail
    except GraphAPIError as e:
        app_logger.exception(e)
        if e.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="SharePoint service unavailable.")
    except Exception as e:
        app_logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch SharePoint article.")
