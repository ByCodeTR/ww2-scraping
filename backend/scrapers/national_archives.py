"""
National Archives API Scraper
ABD Ulusal Arşivi'nden WW2 görselleri
"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import re


class NationalArchivesScraper:
    """National Archives Catalog API üzerinden WW2 görselleri arama"""
    
    BASE_URL = "https://catalog.archives.gov/api/v1"
    
    # WW2 ile ilgili arama terimleri
    WW2_QUERIES = {
        "tanklar": ["tank world war", "armored vehicle 1944", "sherman tank", "tank battle"],
        "ucaklar": ["aircraft world war", "bomber 1944", "fighter plane ww2", "air force"],
        "gemiler": ["battleship world war", "navy 1944", "submarine", "aircraft carrier"],
        "askerler": ["soldier world war", "troops 1944", "infantry", "marines"],
        "haritalar": ["map world war", "battle map 1944", "military map"],
        "savas_sahneleri": ["battle world war", "combat 1944", "d-day", "normandy"],
        "posterler": ["poster world war", "propaganda 1944", "war bonds"],
        "liderler": ["eisenhower", "patton", "macarthur", "roosevelt war"]
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
    
    async def search_images(
        self,
        query: str,
        category_slug: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """National Archives'da görsel ara"""
        session = await self._get_session()
        all_images = []
        
        # Arama sorgusu
        search_query = f"world war II {query}"
        
        params = {
            "q": search_query,
            "resultTypes": "item",
            "rows": min(limit, 100),
            "description.fileUnit.mediaType": "image"
        }
        
        try:
            async with session.get(f"{self.BASE_URL}/search", params=params) as response:
                if response.status != 200:
                    return {"success": False, "error": f"API error: {response.status}", "images": []}
                
                data = await response.json()
                
                if "results" not in data or "result" not in data["results"]:
                    return {"success": True, "images": [], "total": 0}
                
                for item in data["results"]["result"]:
                    # Görsel URL'sini bul
                    image_url = self._extract_image_url(item)
                    if not image_url:
                        continue
                    
                    desc = item.get("description", {})
                    
                    image = {
                        "source_id": f"nara_{item.get('naId', '')}",
                        "title": self._clean_title(desc.get("title", item.get("title", "Untitled"))),
                        "description": desc.get("scopeAndContentNote", "")[:500] if desc.get("scopeAndContentNote") else "",
                        "source_url": image_url,
                        "thumbnail_url": self._get_thumbnail_url(image_url),
                        "width": 0,  # NARA API boyut vermez
                        "height": 0,
                        "file_size": 0,
                        "mime_type": "image/jpeg",
                        "license": "Public Domain",
                        "author": "National Archives",
                        "source": "nara"
                    }
                    all_images.append(image)
                
                await asyncio.sleep(self.rate_limit_delay)
                
                return {
                    "success": True,
                    "images": all_images[:limit],
                    "total": len(all_images),
                    "query": search_query
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "images": []}
    
    async def get_category_images(
        self,
        category_slug: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Kategori bazlı görseller getir"""
        if category_slug not in self.WW2_QUERIES:
            return {"success": False, "error": "Kategori bulunamadı", "images": []}
        
        all_images = []
        queries = self.WW2_QUERIES[category_slug][:3]
        
        for query in queries:
            if len(all_images) >= limit:
                break
            
            result = await self.search_images(query, limit=limit//len(queries))
            if result["success"]:
                all_images.extend(result["images"])
        
        # Duplicate'leri kaldır
        seen = set()
        unique_images = []
        for img in all_images:
            if img["source_id"] not in seen:
                seen.add(img["source_id"])
                unique_images.append(img)
        
        return {
            "success": True,
            "images": unique_images[:limit],
            "total": len(unique_images)
        }
    
    def _extract_image_url(self, item: dict) -> Optional[str]:
        """Item'dan görsel URL'sini çıkar"""
        try:
            # objects içinde dosya URL'si ara
            if "objects" in item:
                objects = item["objects"]
                if isinstance(objects, dict) and "object" in objects:
                    obj = objects["object"]
                    if isinstance(obj, list):
                        for o in obj:
                            if "file" in o:
                                file_info = o["file"]
                                if isinstance(file_info, dict):
                                    url = file_info.get("@url")
                                    if url and self._is_image_url(url):
                                        return url
                    elif isinstance(obj, dict) and "file" in obj:
                        file_info = obj["file"]
                        if isinstance(file_info, dict):
                            return file_info.get("@url")
            
            # digitalObject içinde ara
            desc = item.get("description", {})
            if "digitalObject" in desc:
                digital = desc["digitalObject"]
                if isinstance(digital, list):
                    for d in digital:
                        if "objectUrl" in d:
                            return d["objectUrl"]
                elif isinstance(digital, dict):
                    return digital.get("objectUrl")
            
            return None
        except Exception:
            return None
    
    def _is_image_url(self, url: str) -> bool:
        """URL bir görsel mi?"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff']
        url_lower = url.lower()
        return any(ext in url_lower for ext in image_extensions)
    
    def _get_thumbnail_url(self, url: str) -> str:
        """Thumbnail URL'si oluştur"""
        # NARA için genelde aynı URL kullanılır
        return url
    
    def _clean_title(self, title: str) -> str:
        """Başlığı temizle"""
        if not title:
            return "Untitled"
        # HTML taglarını kaldır
        title = re.sub(r'<[^>]+>', '', title)
        # Fazla boşlukları temizle
        title = ' '.join(title.split())
        return title[:200]
