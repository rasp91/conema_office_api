import os
from datetime import timezone, datetime

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database.models.kiosk_sharepoint_articles import SharePointArticle
from src.kiosk.sharepoint.graph_client import GraphAPIError
from src.database.models.variables import Variable
from src.kiosk.sharepoint import graph_client
from src.upload import delete_file, IMAGE_EXTENSIONS
from src.logger import app_logger
from src.config import config

ICON_SUBDIR = "sharepoint/icons"
LAST_SYNC_KEY = "sharepoint_last_sync"


def _parse_published_at(value: str | None) -> datetime | None:
    """Graph returns published_at as an ISO 8601 string (e.g. '2026-07-07T22:00:00Z') -
    MySQL's TIMESTAMP column needs an actual datetime, not that raw string."""
    return datetime.fromisoformat(value) if value else None


def _sync_icon(article_id: str, has_icon: bool, previous_icon_path: str | None) -> str | None:
    """Download and save the article's banner icon, overwriting any previous file for this id.

    Returns the new relative path, the previous path unchanged if a transient Graph error
    occurs (so a flaky fetch doesn't blank out a previously-good icon), or None if the
    article has no icon (deleting any stale file).
    """
    if not has_icon:
        if previous_icon_path:
            delete_file(previous_icon_path)
        return None

    try:
        content, content_type = graph_client.get_article_icon(article_id)
    except GraphAPIError as e:
        if e.status_code == 404:
            if previous_icon_path:
                delete_file(previous_icon_path)
            return None
        app_logger.warning(f"Could not refresh icon for SharePoint article {article_id}: {e}")
        return previous_icon_path

    ext = IMAGE_EXTENSIONS.get(content_type)
    if not ext:
        app_logger.warning(f"Unmapped icon content-type '{content_type}' for SharePoint article {article_id}, defaulting to .jpg")
        ext = ".jpg"
    relative_path = f"{ICON_SUBDIR}/{article_id}{ext}"

    if previous_icon_path and previous_icon_path != relative_path:
        delete_file(previous_icon_path)

    dest_dir = os.path.join(config.DATA_PATH, ICON_SUBDIR)
    os.makedirs(dest_dir, exist_ok=True)
    with open(os.path.join(config.DATA_PATH, relative_path), "wb") as f:
        f.write(content)

    return relative_path


def _upsert_article(db: Session, article: dict, previous_icon_path: str | None) -> None:
    """Insert or update a single article row (atomic upsert, safe under concurrent syncs of
    the same id) plus its icon file. Does not commit - the caller controls the transaction
    boundary."""
    icon_path = _sync_icon(article["id"], article["has_icon"], previous_icon_path)
    published_at = _parse_published_at(article["published_at"])

    stmt = mysql_insert(SharePointArticle).values(
        id=article["id"],
        title=article["title"],
        description=article["description"],
        published_at=published_at,
        icon_path=icon_path,
    )
    stmt = stmt.on_duplicate_key_update(
        title=stmt.inserted.title,
        description=stmt.inserted.description,
        published_at=stmt.inserted.published_at,
        icon_path=stmt.inserted.icon_path,
    )
    db.execute(stmt)


def sync_articles(db: Session) -> int:
    """Fetch the latest SP_ARTICLES_LIMIT articles from Graph and upsert them into the DB
    cache by SharePoint article id. Never deletes rows - the table is a permanent history."""
    articles = graph_client.list_articles(limit=config.SP_ARTICLES_LIMIT)
    ids = [a["id"] for a in articles]
    previous_icon_paths = (
        dict(db.execute(select(SharePointArticle.id, SharePointArticle.icon_path).where(SharePointArticle.id.in_(ids))).all())
        if ids
        else {}
    )

    for article in articles:
        _upsert_article(db, article, previous_icon_paths.get(article["id"]))

    _set_last_sync(db, datetime.now(timezone.utc))
    db.commit()
    return len(articles)


def upsert_article_from_detail(db: Session, detail: dict) -> None:
    """Refresh a single article's DB row from an already-fetched detail response, so older
    'history' rows stay eventually-consistent with SharePoint as they get viewed."""
    article = {
        "id": detail["id"],
        "title": detail["title"],
        "description": detail.get("description"),
        "published_at": detail["published_at"],
        "has_icon": detail["has_icon"],
    }
    previous_icon_path = db.execute(select(SharePointArticle.icon_path).where(SharePointArticle.id == article["id"])).scalar_one_or_none()
    _upsert_article(db, article, previous_icon_path)
    db.commit()


def get_last_sync(db: Session) -> datetime | None:
    var = db.execute(select(Variable).where(Variable.key == LAST_SYNC_KEY)).scalar_one_or_none()
    return datetime.fromisoformat(var.value) if var and var.value else None


def _set_last_sync(db: Session, when: datetime) -> None:
    """Does not commit - the caller controls the transaction boundary."""
    var = db.execute(select(Variable).where(Variable.key == LAST_SYNC_KEY)).scalar_one_or_none()
    if var:
        var.value = when.isoformat()
    else:
        db.add(Variable(key=LAST_SYNC_KEY, value=when.isoformat(), type="datetime", description="Last successful SharePoint articles sync"))
