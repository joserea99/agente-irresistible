"""
Brandfolder API Service
Provides direct API access to Brandfolder assets, bypassing SPA limitations.

API Documentation: https://developers.brandfolder.com/docs
Authentication: https://brandfolder.com/profile#integrations
"""

import os
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
            print(f"❌ API Error: {e}")
            return {"error": str(e), "data": []}
    
    def get_brandfolders(self) -> List[Dict]:
        """
        Get all accessible brandfolders.
        
        Returns:
            List of brandfolder objects with id, name, etc.
        """
        result = self._request("GET", "/brandfolders")
        return result.get("data", [])
    
    def get_brandfolder_by_slug(self, slug: str) -> Optional[Dict]:
        """
        Get a specific brandfolder by its slug (URL name).
        
        Args:
            slug: The brandfolder slug (e.g., 'irresistiblechurchnetwork')
        """
        brandfolders = self.get_brandfolders()
        for bf in brandfolders:
            if bf.get("attributes", {}).get("slug") == slug:
                return bf
        return None
    
    def get_sections(self, brandfolder_id: str) -> List[Dict]:
        """
        Get all sections within a brandfolder.
        
        Args:
            brandfolder_id: The ID of the brandfolder
        """
        result = self._request("GET", f"/brandfolders/{brandfolder_id}/sections")
        return result.get("data", [])
    
    def get_collections(self, brandfolder_id: str) -> List[Dict]:
        """
        Get all collections within a brandfolder.
        
        Args:
            brandfolder_id: The ID of the brandfolder
        """
        result = self._request("GET", f"/brandfolders/{brandfolder_id}/collections")
        return result.get("data", [])
    
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
        
        result = self._request("GET", endpoint, params)
        
        # Map included attachments to assets
        assets = result.get("data") or []
        included = result.get("included") or []
        return self._map_attachments_to_assets(assets, included)
    
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
        
        result = self._request("GET", f"/brandfolders/{brandfolder_id}/assets", params)
        
        # Map included attachments to assets
        assets = result.get("data") or []
        included = result.get("included") or []
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
        
        # Look in included data for attachment details
        for att in included:
            if att.get("type") == "attachments":
                att_attrs = att.get("attributes", {})
                info["attachments"].append({
                    "id": att.get("id"),
                    "url": att_attrs.get("url") or "",
                    "filename": att_attrs.get("filename") or "untitled",
                    "mimetype": att_attrs.get("mimetype") or "",
                    "size": att_attrs.get("size"),
                    "extension": att_attrs.get("extension") or ""
                })
        
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
