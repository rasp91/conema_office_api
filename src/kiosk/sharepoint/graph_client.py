import base64
import re
from urllib.parse import urlparse, parse_qs, unquote

import requests
import msal

from src.logger import app_logger
from src.config import config

GRAPH = "https://graph.microsoft.com/v1.0"
GRAPH_TIMEOUT = 10
IMAGE_WEBPART_TYPE = "d1d91016-032f-456d-98a4-721247c305e8"


_session = requests.Session()

_msal_app: msal.ConfidentialClientApplication | None = None
_site_id: str | None = None
_site_assets_drive_id: str | None = None
_site_pages_drive_id: str | None = None


class GraphAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _get_msal_app() -> msal.ConfidentialClientApplication:
    # Built lazily (not at import time) since construction itself performs tenant
    # discovery over the network - the app must still start if Graph is unreachable.
    global _msal_app
    if _msal_app is None:
        _msal_app = msal.ConfidentialClientApplication(
            client_id=config.SP_CLIENT_ID,
            client_credential=config.SP_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{config.SP_TENANT_ID}",
        )
    return _msal_app


def _get_access_token() -> str:
    try:
        # MSAL's own token cache already returns a cached, non-expired token when available.
        result = _get_msal_app().acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    except Exception as e:
        raise GraphAPIError(f"Failed to reach Microsoft identity platform: {e}") from e
    if "access_token" not in result:
        raise GraphAPIError(f"Failed to acquire Graph access token: {result.get('error_description', 'unknown error')}")
    return result["access_token"]


def _request(method: str, url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {_get_access_token()}"
    try:
        resp = _session.request(method, url, headers=headers, timeout=GRAPH_TIMEOUT, **kwargs)
    except (requests.Timeout, requests.ConnectionError) as e:
        raise GraphAPIError(f"SharePoint request failed: {e}") from e
    if not resp.ok:
        status_code = 404 if resp.status_code == 404 else 502
        raise GraphAPIError(f"SharePoint request to {url} failed with {resp.status_code}: {resp.text[:500]}", status_code=status_code)
    return resp


def _get_site_id() -> str:
    global _site_id
    if _site_id is None:
        resp = _request("GET", f"{GRAPH}/sites/{config.SP_SITE_HOSTNAME}:{config.SP_SITE_PATH}")
        _site_id = resp.json()["id"]
    return _site_id


def _get_site_assets_drive_id() -> str:
    global _site_assets_drive_id
    if _site_assets_drive_id is None:
        resp = _request("GET", f"{GRAPH}/sites/{_get_site_id()}/lists/{config.SP_SITE_ASSETS_LIST_ID}/drive")
        _site_assets_drive_id = resp.json()["id"]
    return _site_assets_drive_id


def _get_site_pages_drive_id() -> str:
    global _site_pages_drive_id
    if _site_pages_drive_id is None:
        resp = _request("GET", f"{GRAPH}/sites/{_get_site_id()}/lists/{config.SP_SITE_PAGES_LIST_ID}/drive")
        _site_pages_drive_id = resp.json()["id"]
    return _site_pages_drive_id


def _extract_site_assets_path(path: str | None) -> str | None:
    """Extract the path relative to the SiteAssets drive root from a server-relative path."""
    if not path:
        return None
    marker = "/SiteAssets/"
    idx = path.find(marker)
    return path[idx + len(marker) :] if idx != -1 else None


def _banner_image_relative_path(banner_image_url: str | None) -> str | None:
    """Extract the SiteAssets-relative path from a getpreview.ashx BannerImage URL."""
    if not banner_image_url:
        return None
    path = parse_qs(urlparse(banner_image_url).query).get("path", [None])[0]
    return _extract_site_assets_path(unquote(path)) if path else None


def _get_site_assets_content(relative_path: str) -> tuple[bytes, str]:
    resp = _request("GET", f"{GRAPH}/drives/{_get_site_assets_drive_id()}/root:/{relative_path}:/content")
    return resp.content, resp.headers.get("Content-Type", "image/jpeg")


def _resolve_inline_image_path(properties: dict) -> str | None:
    """Resolve an image webpart's SiteAssets-relative path.

    Prefers the (possibly cropped) rendered shape when the image was edited in the
    page editor, else the originally-inserted source. Images inserted without any
    edit may lack both fields - those are skipped rather than guessed at.
    """
    if properties.get("listId") != config.SP_SITE_ASSETS_LIST_ID:
        return None
    shape_url = properties.get("imageShapeData", {}).get("savedImageShape", {}).get("serverRelativeUrl")
    source_url = properties.get("advancedImageEditorData", {}).get("originalSourceUrl")
    return _extract_site_assets_path(unquote(shape_url or source_url)) if (shape_url or source_url) else None


_IMAGE_PLUGIN_DIV_RE = re.compile(r'<div\s+class="imagePlugin[^"]*"[^>]*>')
_DATA_IMAGEURL_RE = re.compile(r'data-imageurl="([^"]*)"')


def _render_image_plugins(html: str) -> str:
    """Rewrite inert `imagePlugin` placeholder divs (rendered by SharePoint's own JS, invisible
    outside SharePoint) into real inline `<img>` tags, inserted as the div's first child so any
    positioning classes on the div still wrap the image."""

    def replace(match: re.Match) -> str:
        div_tag = match.group(0)
        url_match = _DATA_IMAGEURL_RE.search(div_tag)
        relative_path = _extract_site_assets_path(unquote(url_match.group(1))) if url_match else None
        if not relative_path:
            return div_tag
        try:
            content, content_type = _get_site_assets_content(relative_path)
        except GraphAPIError as e:
            app_logger.warning(f"Skipping unresolvable inline SharePoint image '{relative_path}': {e}")
            return div_tag
        b64 = base64.b64encode(content).decode("ascii")
        return f'{div_tag}<img src="data:{content_type};base64,{b64}" alt="" style="max-width:100%;height:auto;" />'

    return _IMAGE_PLUGIN_DIV_RE.sub(replace, html)


def _inline_image_html(properties: dict) -> str | None:
    relative_path = _resolve_inline_image_path(properties)
    if not relative_path:
        return None
    try:
        content, content_type = _get_site_assets_content(relative_path)
    except GraphAPIError as e:
        app_logger.warning(f"Skipping unresolvable inline SharePoint image '{relative_path}': {e}")
        return None
    alt = (properties.get("altText") or "").replace('"', "&quot;")
    b64 = base64.b64encode(content).decode("ascii")
    return f'<img src="data:{content_type};base64,{b64}" alt="{alt}" style="max-width:100%;height:auto;" />'


def _get_list_item(article_id: str) -> dict:
    resp = _request("GET", f"{GRAPH}/sites/{_get_site_id()}/lists/{config.SP_NEWS_LIST_ID}/items/{article_id}?$expand=fields")
    return resp.json()


def _resolve_page_id(page_web_url: str) -> str | None:
    """Resolve the Graph Site Page id from its webUrl.

    The Pages API's $filter is silently ignored by this tenant (returns an empty page
    instead of an error), so name-based filtering doesn't work. Instead, resolve the page
    as a driveItem under the Site Pages library - its eTag embeds the same GUID used as
    the sitePage id (confirmed against a known page: eTag "{81EC5ADD-...},43" for page id
    "81ec5add-...").
    """
    marker = "/SitePages/"
    idx = page_web_url.find(marker)
    if idx == -1:
        return None
    relative_path = unquote(page_web_url[idx + len(marker) :])

    resp = _request("GET", f"{GRAPH}/drives/{_get_site_pages_drive_id()}/root:/{relative_path}")
    match = re.search(r"\{([0-9A-Fa-f-]+)\}", resp.json().get("eTag", ""))
    return match.group(1).lower() if match else None


def _extract_body_html(canvas_layout: dict) -> str:
    parts = []
    for section in canvas_layout.get("horizontalSections", []):
        for column in section.get("columns", []):
            for webpart in column.get("webparts", []):
                odata_type = webpart.get("@odata.type")
                if odata_type == "#microsoft.graph.textWebPart":
                    html = webpart.get("innerHtml")
                    if html:
                        parts.append(_render_image_plugins(html))
                elif odata_type == "#microsoft.graph.standardWebPart" and webpart.get("webPartType") == IMAGE_WEBPART_TYPE:
                    image_html = _inline_image_html(webpart.get("data", {}).get("properties", {}))
                    if image_html:
                        parts.append(image_html)
    return "\n".join(parts)


def list_articles(limit: int) -> list[dict]:
    site_id = _get_site_id()
    url = (
        f"{GRAPH}/sites/{site_id}/lists/{config.SP_NEWS_LIST_ID}/items"
        f"?$expand=fields&$filter=fields/TranslationLanguage eq '{config.SP_LANGUAGE_FILTER}'"
        f"&$orderby=fields/PublishedOn desc&$top={limit}"
    )
    resp = _request("GET", url, headers={"Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly"})
    items = resp.json().get("value", [])

    return [
        {
            "id": item["id"],
            "title": item.get("fields", {}).get("Title", ""),
            "description": item.get("fields", {}).get("Description"),
            "published_at": item.get("fields", {}).get("PublishedOn"),
            "has_icon": bool(_banner_image_relative_path(item.get("fields", {}).get("BannerImage"))),
        }
        for item in items
    ]


def get_article(article_id: str) -> dict:
    item = _get_list_item(article_id)
    fields = item.get("fields", {})
    site_id = _get_site_id()

    body_html = ""
    page_url = fields.get("Url")
    if page_url:
        try:
            page_id = _resolve_page_id(page_url)
            if page_id:
                detail_resp = _request("GET", f"{GRAPH}/sites/{site_id}/pages/{page_id}/microsoft.graph.sitePage?$expand=canvasLayout")
                body_html = _extract_body_html(detail_resp.json().get("canvasLayout", {}))
        except GraphAPIError:
            body_html = ""  # fall through to the description below

    return {
        "id": item["id"],
        "title": fields.get("Title", ""),
        "description": fields.get("Description"),  # internal use only - not part of SharePointArticleDetailModel
        "body_html": body_html or fields.get("Description", ""),
        "published_at": fields.get("PublishedOn"),
        "web_url": page_url,
        "has_icon": bool(_banner_image_relative_path(fields.get("BannerImage"))),
    }


def get_article_icon(article_id: str) -> tuple[bytes, str]:
    fields = _get_list_item(article_id).get("fields", {})
    relative_path = _banner_image_relative_path(fields.get("BannerImage"))
    if not relative_path:
        raise GraphAPIError("Article has no icon.", status_code=404)

    return _get_site_assets_content(relative_path)
