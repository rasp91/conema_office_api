from enum import StrEnum


class DocumentType(StrEnum):
    IMAGE = "image"
    FILE = "file"
    YOUTUBE = "youtube"


class ResourceType(StrEnum):
    """activity_logs.resource_type values. Written by the kiosk detail-view endpoints (see e.g.
    src/kiosk/news/router.py) and read back by the reports in src/activity_log/router.py
    (ITEM_TITLE_MODELS, EXCLUDED_SECTIONS) - a single source of truth so a typo in one file can't
    silently break title resolution or section exclusion with no error anywhere."""

    NEWS = "news"
    EVENT = "event"
    INTERNAL_INFO = "internal-info"
    POSSIBILIST = "possibilist"
    PRESENTATION = "presentation"
    SHAREPOINT_ARTICLE = "sharepoint-article"
    HOME = "home"
    DOCUMENT = "document"


class ActionType(StrEnum):
    """activity_logs.action_type values written from backend code. "page_view" is logged
    directly by the kiosk frontend via POST /kiosk/activity/log and has no backend writer."""

    VIEW_DETAIL = "view_detail"
    PAGE_VIEW = "page_view"
