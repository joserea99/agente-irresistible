"""
Brandfolder API Service
Provides direct API access to Brandfolder assets, bypassing SPA limitations.

API Documentation: https://developers.brandfolder.com/docs
Authentication: https://brandfolder.com/profile#integrations
"""

import os
import time
import requests
from typing import Optional, List, Dict, Any
import tempfile

# Brandfolder API Configuration
BRANDFOLDER_API_BASE = "https://brandfolder.com/api/v4"

class BrandfolderAPI:
    """
    Service for interacting with the Brandfolder REST API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Brandfolder API client.
        
        Args:
            api_key: Brandfolder API key. If not provided, looks for BRANDFOLDER_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("BRANDFOLDER_API_KEY")
        
        if not self.api_key:
            raise ValueError("Brandfolder API key not provided. Set BRANDFOLDER_API_KEY or pass api_key.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Total the API declared for the LAST asset listing fetched (meta.total_count).
        # Lets callers reconcile "how many did I collect" vs "how many exist".
        self._last_total_count = None

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{BRANDFOLDER_API_BASE}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            status = None
            body = ""
            resp = getattr(e, "response", None)
            if resp is not None:
                status = resp.status_code
                try:
                    body = resp.text[:300]
                except Exception:
                    pass
            print(f"❌ Brandfolder API Error [{status}] on {endpoint}: {e} | {body}")
            return {"error": str(e), "status": status, "data": []}

    @staticmethod
    def _next_page_from_meta(result: Dict) -> Optional[int]:
        """
        Resolve the next page number from a Brandfolder response. The API is
        inconsistent: sometimes meta.next_page, sometimes meta.pagination.next_page,
        sometimes only links.next (a URL with ?page=). Check all three.
        """
        meta = result.get("meta") or {}
        np = meta.get("next_page")
        if np:
            return np
        pag = meta.get("pagination") or {}
        if pag.get("next_page"):
            return pag.get("next_page")
        links = result.get("links") or {}
        nxt = links.get("next")
        if isinstance(nxt, str) and "page=" in nxt:
            import re
            m = re.search(r"[?&]page=(\d+)", nxt)
            if m:
                return int(m.group(1))
        return None

    def _fetch_page(self, endpoint: str, params: Dict, page: Optional[int] = None,
                    max_attempts: int = 5) -> Dict[str, Any]:
        """
        Fetch a single page with exponential-backoff retries. A rate-limited or
        transient 5xx page is retried instead of being silently dropped. Returns
        the raw result dict (which still carries 'error' if every attempt failed).
        """
        page_params = dict(params)
        if page is not None:
            page_params["page"] = page
        result = self._request("GET", endpoint, page_params)
        attempts = 0
        while result.get("error") and attempts < max_attempts:
            attempts += 1
            wait = min(2 ** attempts, 15)  # 2,4,8,15,15s — absorb Brandfolder rate limits
            print(f"⚠️ {endpoint} page {page} error (retry {attempts}/{max_attempts}) in {wait}s: {result.get('error')}")
            time.sleep(wait)
            result = self._request("GET", endpoint, page_params)
        return result

    def _list_all(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fully paginate a listing endpoint (e.g. /collections). Prefers total_pages
        when present; otherwise follows next_page. Never truncates on the first
        empty/short page the way a naive loop would.
        """
        params = dict(params or {})
        params.setdefault("per", 100)
        result = self._fetch_page(endpoint, params, page=1)
        out = list(result.get("data") or [])
        meta = result.get("meta") or {}
        total_pages = meta.get("total_pages")
        if total_pages and total_pages > 1:
            for page in range(2, total_pages + 1):
                pr = self._fetch_page(endpoint, params, page=page)
                out.extend(pr.get("data") or [])
        else:
            nxt = self._next_page_from_meta(result)
            guard = 0
            while nxt and guard < 1000:
                guard += 1
                pr = self._fetch_page(endpoint, params, page=nxt)
                rows = pr.get("data") or []
                if not rows:
                    break
                out.extend(rows)
                nxt = self._next_page_from_meta(pr)
        return out

    def get_brandfolders(self) -> List[Dict]:
        """
        Get all accessible brandfolders.
        
        Returns:
            List of brandfolder objects with id, name, etc.
        """
        result = self._request("GET", "/brandfolders")
        data = result.get("data", []) or []
        if data:
            return data

        # Direct listing was empty. Some accounts only expose brandfolders through
        # their organization(s), so try that path before giving up.
        print("⚠️ /brandfolders vacío; intentando vía organizaciones...")
        try:
            orgs = self._request("GET", "/organizations").get("data", []) or []
            print(f"   organizaciones visibles: {len(orgs)}")
            seen = set()
            for org in orgs:
                org_id = org.get("id")
                if not org_id:
                    continue
                org_bfs = self._list_all(f"/organizations/{org_id}/brandfolders")
                org_name = org.get("attributes", {}).get("name", org_id)
                print(f"   org '{org_name}' ({org_id}): {len(org_bfs)} brandfolder(s)")
                for bf in org_bfs:
                    if bf.get("id") and bf["id"] not in seen:
                        seen.add(bf["id"])
                        data.append(bf)
        except Exception as e:
            print(f"   fallback de organizaciones falló: {e}")

        if not data:
            print("⚠️ /brandfolders y organizaciones vacíos; intentando vía /collections...")
            try:
                cols = self._list_all("/collections")
                if cols:
                    print(f"   colecciones visibles: {len(cols)}")
                    # Sort so that *All ICN Assets or all-icn is first
                    cols.sort(key=lambda c: 0 if "all" in (c.get("attributes", {}).get("slug", "") or "").lower() else 1)
                    for col in cols:
                        if col.get("id") and col["id"] not in seen:
                            seen.add(col["id"])
                            data.append(col)
            except Exception as e:
                print(f"   fallback de colecciones falló: {e}")

        if not data:
            print(
                "⚠️ Brandfolder no devolvió NINGUNA biblioteca — ni por acceso directo "
                "ni por organización ni por colecciones. La API key autentica (HTTP 200) pero la cuenta dueña "
                "de la llave ya NO tiene acceso. Verifica en Brandfolder "
                "que esa cuenta siga siendo miembro del Brandfolder con los assets."
            )
        return data
    
    def get_brandfolder_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get a specific brandfolder or collection by its slug (URL name).
        
        Args:
            slug: The brandfolder slug (e.g., 'irresistiblechurchnetwork')
        """
        brandfolders = self.get_brandfolders()
        for bf in brandfolders:
            bf_slug = bf.get("attributes", {}).get("slug")
            if bf_slug == slug:
                return bf
        # If looking for 'irresistiblechurchnetwork', accept 'all-icn' or the first collection
        if slug == "irresistiblechurchnetwork":
            for bf in brandfolders:
                if bf.get("attributes", {}).get("slug") in ("all-icn", "irresistiblechurchnetwork"):
                    return bf
        return brandfolders[0] if brandfolders else None
    
    def get_sections(self, brandfolder_id: str) -> List[Dict]:
        """
        Get all sections within a brandfolder or collection.
        
        Args:
            brandfolder_id: The ID of the brandfolder or collection
        """
        result = self._request("GET", f"/brandfolders/{brandfolder_id}/sections")
        sections = result.get("data", [])
        if not sections:
            # Fallback to collection sections
            col_result = self._request("GET", f"/collections/{brandfolder_id}/sections")
            sections = col_result.get("data", []) or []
        return sections
    
    def get_collections(self, brandfolder_id: str = None) -> List[Dict]:
        """
        Get all collections within a brandfolder or for the authenticated user.
        
        Args:
            brandfolder_id: The ID of the brandfolder (optional)
        """
        if brandfolder_id:
            result = self._request("GET", f"/brandfolders/{brandfolder_id}/collections")
            cols = result.get("data", [])
            if cols:
                return cols
        result = self._request("GET", "/collections")
        return result.get("data", []) or []
    
    def get_assets(self, section_id: str = None, collection_id: str = None, 
                   brandfolder_id: str = None, include_attachments: bool = True,
                   per_page: int = 100) -> List[Dict]:
        """
        Get assets from a section, collection, or brandfolder.
        
        Args:
            section_id: Get assets from this section
            collection_id: Get assets from this collection
            brandfolder_id: Get all assets from this brandfolder
            include_attachments: Whether to include attachment URLs
            per_page: Number of results per page (max 100)
        """
        params = {"per": per_page}
        if include_attachments:
            params["include"] = "attachments"
        
        if section_id:
            endpoint = f"/sections/{section_id}/assets"
        elif collection_id:
            endpoint = f"/collections/{collection_id}/assets"
        elif brandfolder_id:
            endpoint = f"/brandfolders/{brandfolder_id}/assets"
        else:
            raise ValueError("Must provide section_id, collection_id, or brandfolder_id")
        
        # --- Page 1 (with brandfolder→collection fallback) ---
        result = self._fetch_page(endpoint, params, page=1)
        if brandfolder_id and (result.get("error") or not result.get("data")):
            # A collection id was passed as brandfolder_id, or the key only has
            # collection scope — fall back to the collection endpoint.
            col_endpoint = f"/collections/{brandfolder_id}/assets"
            col_result = self._fetch_page(col_endpoint, params, page=1)
            if col_result.get("data"):
                result = col_result
                endpoint = col_endpoint

        assets = list(result.get("data") or [])
        included = list(result.get("included") or [])
        meta = result.get("meta") or {}
        total_count = meta.get("total_count")
        total_pages = meta.get("total_pages")
        self._last_total_count = total_count

        # --- Collect every remaining page WITHOUT silently truncating. ---
        # Iterate page numbers up to total_pages so a single failed page no longer
        # kills the whole tail (the old `break` did exactly that, capping the
        # umbrella collection at a partial count). Fall back to following next_page
        # only when the API doesn't report total_pages.
        missing_pages = []
        if total_pages and total_pages > 1:
            for page in range(2, total_pages + 1):
                pr = self._fetch_page(endpoint, params, page=page)
                page_assets = pr.get("data") or []
                if pr.get("error") and not page_assets:
                    print(f"❌ {endpoint} page {page} failed after retries — will retry in reconcile.")
                    missing_pages.append(page)
                    continue
                assets.extend(page_assets)
                included.extend(pr.get("included") or [])
        else:
            next_page = self._next_page_from_meta(result)
            guard = 0
            while next_page and guard < 10000:
                guard += 1
                pr = self._fetch_page(endpoint, params, page=next_page)
                page_assets = pr.get("data") or []
                if pr.get("error") and not page_assets:
                    print(f"❌ {endpoint} page {next_page} failed after retries — stopping.")
                    break
                assets.extend(page_assets)
                included.extend(pr.get("included") or [])
                next_page = self._next_page_from_meta(pr)

        # --- Reconcile collected vs the total the API declared (meta.total_count). ---
        def _unique(items):
            return len({a.get("id") for a in items if a.get("id")})

        if total_count and _unique(assets) < total_count and missing_pages:
            print(f"🔁 {endpoint}: {_unique(assets)}/{total_count} — retrying {len(missing_pages)} failed page(s)...")
            for page in list(missing_pages):
                pr = self._fetch_page(endpoint, params, page=page, max_attempts=4)
                page_assets = pr.get("data") or []
                if page_assets:
                    assets.extend(page_assets)
                    included.extend(pr.get("included") or [])
                    missing_pages.remove(page)

        if total_count and _unique(assets) < total_count:
            print(f"⚠️ COVERAGE SHORTFALL on {endpoint}: got {_unique(assets)}/{total_count} "
                  f"(unrecovered pages: {missing_pages or 'silent/next_page gap'}).")

        return self._map_attachments_to_assets(assets, included)

    def diagnose_collection_assets(self, coll_id: str) -> Dict[str, Any]:
        """
        Lightweight coverage probe for ONE collection/brandfolder: fully paginate
        (ids only, no attachments) and report how many assets were reachable vs the
        total the API declares, plus whether pagination truncated. Read-only.
        """
        params = {"per": 200}  # ids only → bigger pages are safe (no attachment payload)
        endpoint = f"/brandfolders/{coll_id}/assets"
        endpoint_used = "brandfolder"
        result = self._fetch_page(endpoint, params, page=1)
        if result.get("error") or not result.get("data"):
            endpoint = f"/collections/{coll_id}/assets"
            endpoint_used = "collection"
            result = self._fetch_page(endpoint, params, page=1)

        ids = {a["id"] for a in (result.get("data") or []) if a.get("id")}
        meta = result.get("meta") or {}
        api_total = meta.get("total_count")
        total_pages = meta.get("total_pages")
        truncated = False
        truncation_mode = "none"
        stopped_at = None

        if total_pages and total_pages > 1:
            for page in range(2, total_pages + 1):
                pr = self._fetch_page(endpoint, params, page=page)
                rows = pr.get("data") or []
                if pr.get("error") and not rows:
                    truncated = True
                    truncation_mode = "page_error"
                    stopped_at = stopped_at or page
                    continue
                ids.update(a["id"] for a in rows if a.get("id"))
        else:
            nxt = self._next_page_from_meta(result)
            guard = 0
            while nxt and guard < 10000:
                guard += 1
                pr = self._fetch_page(endpoint, params, page=nxt)
                rows = pr.get("data") or []
                if pr.get("error") and not rows:
                    truncated = True
                    truncation_mode = "page_error"
                    stopped_at = nxt
                    break
                ids.update(a["id"] for a in rows if a.get("id"))
                nxt = self._next_page_from_meta(pr)

        if api_total and len(ids) < api_total and truncation_mode == "none":
            truncated = True
            truncation_mode = "silent"

        return {
            "ids": ids,
            "collected": len(ids),
            "api_total": api_total,
            "endpoint_used": endpoint_used,
            "truncated": truncated,
            "truncation_mode": truncation_mode,
            "stopped_at_page": stopped_at,
        }

    def search_assets(self, brandfolder_id: str, query: str,
                      include_attachments: bool = True) -> List[Dict]:
        """
        Search for assets within a brandfolder.
        
        Args:
            brandfolder_id: The brandfolder to search in
            query: Search query string
            include_attachments: Whether to include attachment details
        """
        params = {
            "search": query,
            "per": 100
        }
        if include_attachments:
            params["include"] = "attachments"
        
        # Initial Request
        endpoint = f"/brandfolders/{brandfolder_id}/assets"
        result = self._request("GET", endpoint, params)
        if result.get("error") or not result.get("data"):
            col_endpoint = f"/collections/{brandfolder_id}/assets"
            col_result = self._request("GET", col_endpoint, params)
            if col_result.get("data"):
                result = col_result
                endpoint = col_endpoint
        
        # Map included attachments to assets
        assets = result.get("data") or []
        included = result.get("included") or []
        
        # Pagination Loop
        meta = result.get("meta", {})
        next_page = meta.get("next_page")
        
        while next_page:
            print(f"🔎 Fetching search page {next_page}...")
            
            params["page"] = next_page
            result = self._request("GET", endpoint, params)
            
            new_assets = result.get("data") or []
            new_included = result.get("included") or []
            
            if not new_assets:
                break
                
            assets.extend(new_assets)
            included.extend(new_included)
            
            # Update info
            meta = result.get("meta", {})
            next_page = meta.get("next_page")

        return self._map_attachments_to_assets(assets, included)
    
    def _map_attachments_to_assets(self, assets: List[Dict], included: List[Dict]) -> List[Dict]:
        """
        Map attachments from the 'included' array to their respective assets.
        The API returns attachments separately and we need to merge them.
        """
        # Build a map of attachment ID -> attachment data
        attachment_map = {}
        for item in included:
            if item.get("type") == "attachments":
                attachment_map[item.get("id")] = item
        
        # Add included field to each asset with its attachments
        for asset in assets:
            asset_attachments = []
            
            # Safe access to nested relationships
            rels = asset.get("relationships") or {}
            att_rels = rels.get("attachments") or {}
            att_refs = att_rels.get("data") or []
            
            for att_ref in att_refs:
                att_id = att_ref.get("id")
                if att_id in attachment_map:
                    asset_attachments.append(attachment_map[att_id])
            asset["included"] = asset_attachments
        
        return assets

    
    def get_asset_details(self, asset_id: str) -> Dict:
        """
        Get full details of a specific asset.
        
        Args:
            asset_id: The asset ID
        """
        params = {"include": "attachments,custom_fields,tags"}
        result = self._request("GET", f"/assets/{asset_id}", params)
        
        asset = result.get("data") or {}
        included = result.get("included") or []
        
        # We need to map it as a list, then extract the first (and only) item
        mapped_assets = self._map_attachments_to_assets([asset], included)
        return mapped_assets[0] if mapped_assets else {}
    
    def download_attachment(self, attachment_url: str, cookies: Optional[Dict] = None) -> Optional[str]:
        """
        Download an attachment to a temporary file.
        
        Args:
            attachment_url: URL of the attachment to download
            cookies: Optional cookies for authentication
            
        Returns:
            Path to the downloaded file, or None if failed
        """
        try:
            print(f"⬇️ Downloading: {attachment_url[:60]}...")
            
            headers = {}
            # Only send Auth header if it's a Brandfolder API URL, not a signed GCS/S3 link
            if "brandfolder.com/api" in attachment_url:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.get(
                attachment_url,
                headers=headers,
                cookies=cookies,
                stream=True,
                timeout=(10, 300) # 10s connect, 300s (5min) read timeout per chunk
            )

            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get("Content-Type", "")
            ext = ".bin"
            if "video" in content_type or "mp4" in attachment_url.lower():
                ext = ".mp4"
            elif "audio" in content_type or "mp3" in attachment_url.lower():
                ext = ".mp3"
            elif "pdf" in content_type or ".pdf" in attachment_url.lower():
                ext = ".pdf"
            elif "word" in content_type or ".docx" in attachment_url.lower():
                ext = ".docx"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                print(f"✅ Downloaded to: {tmp_file.name}")
                return tmp_file.name
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def extract_asset_info(self, asset: Dict) -> Dict[str, Any]:
        """
        Extract useful information from an asset object.
        
        Args:
            asset: Raw asset data from API
            
        Returns:
            Cleaned asset information
        """
        attributes = asset.get("attributes", {})
        
        info = {
            "id": asset.get("id"),
            "name": attributes.get("name", "Untitled"),
            "description": attributes.get("description", ""),
            "created_at": attributes.get("created_at"),
            "updated_at": attributes.get("updated_at"),
            "attachments": [],
            "tags": [],
            "extension": attributes.get("extension"),
        }
        
        # Extract attachments
        included = asset.get("included") or []
        
        # relationships might be None if key exists
        rels = asset.get("relationships") or {}
        atts_rel = rels.get("attachments") or {}
        attachments = atts_rel.get("data") or []
        
        # Look in included data for attachment details + tags
        for att in included:
            item_type = att.get("type")
            if item_type == "attachments":
                att_attrs = att.get("attributes", {})
                info["attachments"].append({
                    "id": att.get("id"),
                    "url": att_attrs.get("url") or "",
                    "filename": att_attrs.get("filename") or "untitled",
                    "mimetype": att_attrs.get("mimetype") or "",
                    "size": att_attrs.get("size"),
                    "extension": att_attrs.get("extension") or ""
                })
            elif item_type == "tags":
                tag_name = (att.get("attributes", {}) or {}).get("name")
                if tag_name:
                    info["tags"].append(tag_name)

        return info
    
    def get_all_content(self, brandfolder_id: str, topic_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ALL content from a brandfolder, organized by type.
        
        Args:
            brandfolder_id: The brandfolder ID
            topic_filter: Optional topic to prioritize in search
            
        Returns:
            Dict with sections, assets, videos, audios, documents
        """
        result = {
            "sections": [],
            "assets": [],
            "videos": [],
            "audios": [],
            "documents": [],
            "total_assets": 0
        }
        
        # Get all sections
        sections = self.get_sections(brandfolder_id)
        result["sections"] = [
            {"id": s.get("id"), "name": s.get("attributes", {}).get("name")}
            for s in sections
        ]
        
        # Search if topic provided, otherwise get all
        if topic_filter:
            assets = self.search_assets(brandfolder_id, topic_filter)
        else:
            assets = self.get_assets(brandfolder_id=brandfolder_id)
        
        result["total_assets"] = len(assets)
        
        # Categorize assets
        for asset in assets:
            info = self.extract_asset_info(asset)
            result["assets"].append(info)
            
            # Categorize by type
            ext = (info.get("extension") or "").lower()
            name = (info.get("name") or "").lower()
            
            if ext in ["mp4", "mov", "avi", "webm"] or "video" in name:
                result["videos"].append(info)
            elif ext in ["mp3", "wav", "m4a", "ogg"] or "audio" in name:
                result["audios"].append(info)
            elif ext in ["pdf", "doc", "docx", "ppt", "pptx"]:
                result["documents"].append(info)
        
        return result


def test_connection(api_key: str) -> Dict[str, Any]:
    """
    Test the API connection and return basic info.
    
    Args:
        api_key: Brandfolder API key to test
        
    Returns:
        Dict with connection status and brandfolder info
    """
    try:
        api = BrandfolderAPI(api_key)
        brandfolders = api.get_brandfolders()
        
        return {
            "success": True,
            "message": f"✅ Connected! Found {len(brandfolders)} brandfolder(s)",
            "brandfolders": [
                {
                    "id": bf.get("id"),
                    "name": bf.get("attributes", {}).get("name"),
                    "slug": bf.get("attributes", {}).get("slug")
                }
                for bf in brandfolders
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Connection failed: {str(e)}",
            "brandfolders": []
        }
