"""
Throwaway discovery script — inspects the SharePoint site's content shape via
Microsoft Graph so src/kiosk/sharepoint/graph_client.py can be built against
real data. Run manually: python scripts/sp_discovery.py
"""

import json
import os
import urllib3

import msal
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

# This machine's Avast TLS-inspection root cert fails strict OpenSSL 3.x chain
# validation ("Basic Constraints of CA cert not marked critical"). Disabling
# verification here only, for this throwaway local discovery run — never do
# this in graph_client.py.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SP_TENANT_ID = os.environ["SP_TENANT_ID"]
SP_CLIENT_ID = os.environ["SP_CLIENT_ID"]
SP_CLIENT_SECRET = os.environ["SP_CLIENT_SECRET"]
SP_SITE_HOSTNAME = os.environ["SP_SITE_HOSTNAME"]
SP_SITE_PATH = os.environ["SP_SITE_PATH"]

GRAPH = "https://graph.microsoft.com/v1.0"


def get_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=SP_CLIENT_ID,
        client_credential=SP_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{SP_TENANT_ID}",
        verify=False,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Token acquisition failed: {json.dumps(result, indent=2)}")
    return result["access_token"]


def dump(label: str, data) -> None:
    print(f"\n{'=' * 10} {label} {'=' * 10}")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])


def main() -> None:
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    session = requests.Session()
    session.headers.update(headers)
    session.verify = False

    site_resp = session.get(f"{GRAPH}/sites/{SP_SITE_HOSTNAME}:{SP_SITE_PATH}", timeout=15)
    site_resp.raise_for_status()
    site = site_resp.json()
    site_id = site["id"]
    dump("Site", {"id": site_id, "displayName": site.get("displayName"), "webUrl": site.get("webUrl")})

    lists_resp = session.get(f"{GRAPH}/sites/{site_id}/lists", timeout=15)
    if lists_resp.ok:
        lists = lists_resp.json().get("value", [])
        dump(
            "Lists",
            [{"displayName": l.get("displayName"), "id": l.get("id"), "template": l.get("list", {}).get("template")} for l in lists],
        )
    else:
        dump("Lists (error)", {"status": lists_resp.status_code, "body": lists_resp.text[:1000]})

    pages_resp = session.get(f"{GRAPH}/sites/{site_id}/pages?$top=5", timeout=15)
    if pages_resp.ok:
        pages = pages_resp.json().get("value", [])
        dump(
            "Pages (first 5)",
            [
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "pageLayout": p.get("pageLayout"),
                    "promotionKind": p.get("promotionKind"),
                    "publishingState": p.get("publishingState"),
                }
                for p in pages
            ],
        )

        if pages:
            first_id = pages[0]["id"]
            detail_resp = session.get(f"{GRAPH}/sites/{site_id}/pages/{first_id}/microsoft.graph.sitePage?$expand=canvasLayout", timeout=15)
            if detail_resp.ok:
                dump("First page detail (canvasLayout)", detail_resp.json())
            else:
                dump("Page detail (error)", {"status": detail_resp.status_code, "body": detail_resp.text[:1000]})
    else:
        dump("Pages (error)", {"status": pages_resp.status_code, "body": pages_resp.text[:1000]})


if __name__ == "__main__":
    main()
