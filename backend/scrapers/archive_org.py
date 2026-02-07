"""
Archive.org Scraper
WW2 video klipleri için Internet Archive API
"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import re


class ArchiveOrgScraper:
    """Internet Archive üzerinden WW2 video ve görselleri arama"""
    
    BASE_URL = "https://archive.org"
    SEARCH_URL = f"{BASE_URL}/advancedsearch.php"
    
    # WW2 ile ilgili koleksiyonlar
    WW2_COLLECTIONS = [
        "prelinger",  # Prelinger Archives - eski filmler
        "wwii",  # WW2 koleksiyonu
        "newsreels",  # Haber filmleri
        "military",  # Askeri içerikler
    ]
    
    # Kategori bazlı arama terimleri
    WW2_QUERIES = {
        "tanklar": ["tank battle", "armored warfare", "panzer", "sherman"],
        "ucaklar": ["aircraft combat", "bomber raid", "fighter plane", "luftwaffe"],
        "gemiler": ["naval battle", "battleship", "submarine warfare", "pearl harbor"],
        "askerler": ["infantry combat", "soldier training", "military parade"],
        "haritalar": ["war map", "military strategy", "battle plan"],
        "savas_sahneleri": ["battle footage", "combat film", "d-day footage", "war documentary"],
        "posterler": ["propaganda film", "war bonds", "home front"],
        "liderler": ["eisenhower speech", "churchill", "roosevelt address"]
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.5
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "WW2ImageArchive/1.0"}
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_videos(
        self,
        query: str,
        limit: int = 30
    ) -> Dict[str, Any]:
        """Archive.org'da video ara"""
        session = await self._get_session()
        
        # Arama sorgusu - video formatlarını filtrele
        search_query = f"world war II {query} AND mediatype:movies"
        
        params = {
            "q": search_query,
            "fl[]": ["identifier", "title", "description", "year", "creator", "downloads", "item_size"],
            "sort[]": "downloads desc",
            "rows": limit,
            "page": 1,
            "output": "json"
        }
        
        try:
            async with session.get(self.SEARCH_URL, params=params) as response:
                if response.status != 200:
                    return {"success": False, "error": f"API error: {response.status}", "videos": []}
                
                data = await response.json()
                
                if "response" not in data or "docs" not in data["response"]:
                    return {"success": True, "videos": [], "total": 0}
                
                videos = []
                for doc in data["response"]["docs"]:
                    identifier = doc.get("identifier", "")
                    
                    video = {
                        "source_id": f"archive_{identifier}",
                        "title": self._clean_title(doc.get("title", "Untitled")),
                        "description": (doc.get("description", "") or "")[:500],
                        "year": doc.get("year", ""),
                        "creator": doc.get("creator", "Unknown"),
                        "downloads": doc.get("downloads", 0),
                        "thumbnail_url": f"https://archive.org/services/img/{identifier}",
                        "page_url": f"https://archive.org/details/{identifier}",
                        "embed_url": f"https://archive.org/embed/{identifier}",
                        "download_url": f"https://archive.org/download/{identifier}",
                        "source": "archive_org",
                        "media_type": "video"
                    }
                    videos.append(video)
                
                await asyncio.sleep(self.rate_limit_delay)
                
                return {
                    "success": True,
                    "videos": videos,
                    "total": data["response"].get("numFound", len(videos)),
                    "query": query
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "videos": []}
    
    async def search_images(
        self,
        query: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Archive.org'da görsel ara"""
        session = await self._get_session()
        
        search_query = f"world war II {query} AND mediatype:image"
        
        params = {
            "q": search_query,
            "fl[]": ["identifier", "title", "description", "year", "creator"],
            "sort[]": "downloads desc",
            "rows": limit,
            "page": 1,
            "output": "json"
        }
        
        try:
            async with session.get(self.SEARCH_URL, params=params) as response:
                if response.status != 200:
                    return {"success": False, "error": f"API error: {response.status}", "images": []}
                
                data = await response.json()
                
                if "response" not in data or "docs" not in data["response"]:
                    return {"success": True, "images": [], "total": 0}
                
                images = []
                for doc in data["response"]["docs"]:
                    identifier = doc.get("identifier", "")
                    
                    image = {
                        "source_id": f"archive_{identifier}",
                        "title": self._clean_title(doc.get("title", "Untitled")),
                        "description": (doc.get("description", "") or "")[:500],
                        "source_url": f"https://archive.org/download/{identifier}/{identifier}.jpg",
                        "thumbnail_url": f"https://archive.org/services/img/{identifier}",
                        "width": 0,
                        "height": 0,
                        "file_size": 0,
                        "mime_type": "image/jpeg",
                        "license": "Public Domain",
                        "author": doc.get("creator", "Unknown"),
                        "source": "archive_org"
                    }
                    images.append(image)
                
                await asyncio.sleep(self.rate_limit_delay)
                
                return {
                    "success": True,
                    "images": images,
                    "total": len(images),
                    "query": query
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "images": []}
    
    async def get_category_videos(
        self,
        category_slug: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Kategori bazlı videolar getir"""
        if category_slug not in self.WW2_QUERIES:
            return {"success": False, "error": "Kategori bulunamadı", "videos": []}
        
        all_videos = []
        queries = self.WW2_QUERIES[category_slug][:2]
        
        for query in queries:
            if len(all_videos) >= limit:
                break
            
            result = await self.search_videos(query, limit=limit//len(queries))
            if result["success"]:
                all_videos.extend(result["videos"])
        
        # Duplicate'leri kaldır
        seen = set()
        unique_videos = []
        for vid in all_videos:
            if vid["source_id"] not in seen:
                seen.add(vid["source_id"])
                unique_videos.append(vid)
        
        return {
            "success": True,
            "videos": unique_videos[:limit],
            "total": len(unique_videos)
        }
    
    def _clean_title(self, title: str) -> str:
        """Başlığı temizle"""
        if not title:
            return "Untitled"
        if isinstance(title, list):
            title = title[0] if title else "Untitled"
        title = re.sub(r'<[^>]+>', '', str(title))
        title = ' '.join(title.split())
        return title[:200]
