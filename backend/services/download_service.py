"""
Görsel indirme servisi
"""
import os
import asyncio
import aiohttp
from typing import Optional, Callable
from datetime import datetime
import hashlib

# Proje kök dizini
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")


class DownloadService:
    """Görsel indirme yönetimi"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._ensure_download_dirs()
    
    def _ensure_download_dirs(self):
        """İndirme klasörlerini oluştur"""
        categories = [
            "tanklar", "ucaklar", "gemiler", "askerler",
            "haritalar", "savas_sahneleri", "posterler", "liderler", "diger"
        ]
        for category in categories:
            path = os.path.join(DOWNLOADS_DIR, category)
            os.makedirs(path, exist_ok=True)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP session oluştur"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://commons.wikimedia.org/"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )
        return self.session
    
    async def close(self):
        """Session'ı kapat"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def download_image(
        self,
        url: str,
        category_slug: str = "diger",
        filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> dict:
        """
        Görsel indir
        
        Args:
            url: Görsel URL'i
            category_slug: Kategori klasörü
            filename: Dosya adı (opsiyonel, yoksa URL'den çıkarılır)
            progress_callback: İlerleme bildirimi fonksiyonu
        
        Returns:
            İndirme sonucu
        """
        session = await self._get_session()
        
        try:
            # Dosya adını belirle
            if not filename:
                filename = self._extract_filename(url)
            
            # Dosya yolunu oluştur
            category_dir = os.path.join(DOWNLOADS_DIR, category_slug)
            os.makedirs(category_dir, exist_ok=True)
            
            file_path = os.path.join(category_dir, filename)
            
            # Dosya zaten var mı kontrol et
            if os.path.exists(file_path):
                return {
                    "success": True,
                    "file_path": file_path,
                    "filename": filename,
                    "message": "Dosya zaten mevcut",
                    "already_exists": True
                }
            
            # İndirmeye başla
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"HTTP Error: {response.status}"
                    }
                
                # Dosya boyutunu al
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                # Dosyaya yaz
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # İlerleme bildirimi
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)
                
                # Dosya boyutunu al
                file_size = os.path.getsize(file_path)
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "filename": filename,
                    "file_size": file_size,
                    "already_exists": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_multiple(
        self,
        images: list,
        category_slug: str = "diger",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> dict:
        """
        Birden fazla görsel indir
        
        Args:
            images: Görsel listesi [{"source_url": "...", "title": "..."}]
            category_slug: Kategori klasörü
            progress_callback: İlerleme bildirimi (current, total, filename)
        
        Returns:
            Toplu indirme sonucu
        """
        results = {
            "success": True,
            "total": len(images),
            "downloaded": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        for i, image in enumerate(images):
            url = image.get("source_url", "")
            title = image.get("title", "unknown")
            
            if not url:
                results["failed"] += 1
                continue
            
            # İlerleme bildirimi
            if progress_callback:
                progress_callback(i + 1, len(images), title)
            
            # İndir
            result = await self.download_image(url, category_slug)
            
            if result.get("success"):
                if result.get("already_exists"):
                    results["skipped"] += 1
                else:
                    results["downloaded"] += 1
                results["details"].append({
                    "title": title,
                    "status": "success",
                    "file_path": result.get("file_path")
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "title": title,
                    "status": "failed",
                    "error": result.get("error")
                })
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        return results
    
    def _extract_filename(self, url: str) -> str:
        """URL'den dosya adını çıkar"""
        # URL'den dosya adını al
        filename = url.split("/")[-1].split("?")[0]
        
        # URL encoding'i çöz
        from urllib.parse import unquote
        filename = unquote(filename)
        
        # Geçersiz karakterleri temizle
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Maksimum uzunluk
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            # Hash ile kısalt
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:8]
            filename = f"{name[:150]}_{hash_suffix}{ext}"
        
        return filename
    
    def get_download_path(self, category_slug: str) -> str:
        """Kategori için indirme yolunu döndür"""
        return os.path.join(DOWNLOADS_DIR, category_slug)
    
    def get_downloaded_images(self, category_slug: Optional[str] = None) -> list:
        """İndirilmiş görselleri listele"""
        images = []
        
        if category_slug:
            categories = [category_slug]
        else:
            categories = os.listdir(DOWNLOADS_DIR)
        
        for cat in categories:
            cat_path = os.path.join(DOWNLOADS_DIR, cat)
            if not os.path.isdir(cat_path):
                continue
            
            for filename in os.listdir(cat_path):
                file_path = os.path.join(cat_path, filename)
                if os.path.isfile(file_path):
                    # Sadece resim dosyalarını al
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        images.append({
                            "filename": filename,
                            "file_path": file_path,
                            "category": cat,
                            "file_size": os.path.getsize(file_path),
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(file_path)
                            ).isoformat()
                        })
        
        return images
