"""
WW2 Görsel Arşivi - FastAPI Backend
Ana uygulama dosyası
"""
import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Proje yolunu ayarla
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, get_db, Category, Image, SearchHistory
from backend.scrapers import WikimediaScraper, NationalArchivesScraper, ArchiveOrgScraper
from backend.services import DownloadService

# FastAPI uygulaması
app = FastAPI(
    title="WW2 Görsel Arşivi",
    description="İkinci Dünya Savaşı görselleri için scraping ve arşivleme uygulaması",
    version="2.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyalar
FRONTEND_DIR = BASE_DIR / "frontend"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Klasörleri oluştur
FRONTEND_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Static file serving
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

if DOWNLOADS_DIR.exists():
    app.mount("/downloads", StaticFiles(directory=str(DOWNLOADS_DIR)), name="downloads")

# Global instances - Tüm scraperlar
wikimedia_scraper = WikimediaScraper()
nara_scraper = NationalArchivesScraper()
archive_scraper = ArchiveOrgScraper()
download_service = DownloadService()

# Backward compatibility
scraper = wikimedia_scraper


# Pydantic modelleri
class SearchRequest(BaseModel):
    query: str
    category_slug: Optional[str] = None
    limit: int = 50
    min_width: int = 800


class DownloadRequest(BaseModel):
    images: List[dict]
    category_slug: str = "diger"


class ImageResponse(BaseModel):
    id: int
    title: str
    source_url: str
    thumbnail_url: Optional[str]
    is_downloaded: bool
    is_favorite: bool


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında veritabanını hazırla"""
    init_db()
    print("✅ Veritabanı hazırlandı")


@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatılırken kaynakları temizle"""
    await scraper.close()
    await download_service.close()


@app.get("/")
async def root():
    """Ana sayfa - Frontend'e yönlendir"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "WW2 Görsel Arşivi API", "docs": "/docs"}


@app.get("/api/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# ==================== KATEGORİLER ====================

@app.get("/api/categories")
async def get_categories():
    """Tüm kategorileri getir"""
    with get_db() as db:
        categories = db.query(Category).all()
        return {
            "success": True,
            "categories": [cat.to_dict() for cat in categories]
        }


@app.get("/api/categories/{slug}")
async def get_category(slug: str):
    """Belirli bir kategoriyi getir"""
    with get_db() as db:
        category = db.query(Category).filter(Category.slug == slug).first()
        if not category:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı")
        return {
            "success": True,
            "category": category.to_dict()
        }


# ==================== ARAMA ====================

@app.get("/api/search")
async def search_images(
    q: str = Query(..., description="Arama terimi"),
    category: Optional[str] = Query(None, description="Kategori slug"),
    limit: int = Query(100, ge=1, le=200, description="Sonuç limiti"),
    min_width: int = Query(600, ge=100, description="Minimum genişlik (HD filtresi)")
):
    """Wikimedia'da görsel ara"""
    result = await scraper.search_images(
        query=q,
        category_slug=category,
        limit=limit,
        min_width=min_width
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Arama hatası"))
    
    # Arama geçmişine kaydet
    with get_db() as db:
        category_obj = None
        if category:
            category_obj = db.query(Category).filter(Category.slug == category).first()
        
        history = SearchHistory(
            query=q,
            results_count=result["total"],
            category_id=category_obj.id if category_obj else None
        )
        db.add(history)
        db.commit()
    
    return result


@app.get("/api/category-images/{slug}")
async def get_category_images(
    slug: str,
    limit: int = Query(100, ge=1, le=200)
):
    """Kategori bazlı görseller getir"""
    result = await scraper.get_category_images(
        category_slug=slug,
        limit=limit
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Hata"))
    
    return result


@app.get("/api/bulk-search/{slug}")
async def bulk_search_images(
    slug: str,
    limit: int = Query(200, ge=1, le=500)
):
    """Toplu arama - Maksimum görsel bulmak için"""
    result = await scraper.bulk_search(
        category_slug=slug,
        limit=limit
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Hata"))
    
    return result


@app.get("/api/search-all")
async def search_all_sources(
    q: str = Query(..., description="Arama terimi"),
    limit: int = Query(100, ge=1, le=300)
):
    """Tüm kaynaklarda arama (Wikimedia + NARA + Archive.org)"""
    all_images = []
    sources_searched = []
    
    # Wikimedia
    try:
        wiki_result = await wikimedia_scraper.search_images(q, limit=limit//3)
        if wiki_result["success"]:
            all_images.extend(wiki_result["images"])
            sources_searched.append("wikimedia")
    except Exception as e:
        print(f"Wikimedia hatası: {e}")
    
    # National Archives
    try:
        nara_result = await nara_scraper.search_images(q, limit=limit//3)
        if nara_result["success"]:
            all_images.extend(nara_result["images"])
            sources_searched.append("nara")
    except Exception as e:
        print(f"NARA hatası: {e}")
    
    # Archive.org
    try:
        archive_result = await archive_scraper.search_images(q, limit=limit//3)
        if archive_result["success"]:
            all_images.extend(archive_result["images"])
            sources_searched.append("archive_org")
    except Exception as e:
        print(f"Archive.org hatası: {e}")
    
    return {
        "success": True,
        "images": all_images[:limit],
        "total": len(all_images),
        "sources": sources_searched,
        "query": q
    }


@app.get("/api/videos")
async def search_videos(
    q: str = Query(..., description="Arama terimi"),
    limit: int = Query(30, ge=1, le=100)
):
    """WW2 video klipleri ara (Archive.org)"""
    result = await archive_scraper.search_videos(q, limit=limit)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Video arama hatası"))
    
    return result


@app.get("/api/videos/{category}")
async def get_category_videos(
    category: str,
    limit: int = Query(20, ge=1, le=50)
):
    """Kategori bazlı videolar getir"""
    result = await archive_scraper.get_category_videos(category, limit=limit)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Hata"))
    
    return result


# ==================== İNDİRME ====================

@app.post("/api/download")
async def download_single_image(
    url: str = Query(..., description="Görsel URL'i"),
    category: str = Query("diger", description="Hedef kategori"),
    title: Optional[str] = Query(None, description="Dosya adı")
):
    """Tek görsel indir"""
    filename = None
    if title:
        # Başlıktan dosya adı oluştur
        filename = title.replace(" ", "_")[:100]
        # Uzantı ekle
        ext = url.split(".")[-1].split("?")[0].lower()
        if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            filename = f"{filename}.{ext}"
        else:
            filename = f"{filename}.jpg"
    
    result = await download_service.download_image(
        url=url,
        category_slug=category,
        filename=filename
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/api/download-batch")
async def download_batch(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Toplu görsel indirme (arka planda)"""
    
    async def do_download():
        return await download_service.download_multiple(
            images=request.images,
            category_slug=request.category_slug
        )
    
    # Hemen başlat ve sonucu döndür
    result = await download_service.download_multiple(
        images=request.images,
        category_slug=request.category_slug
    )
    
    return result


# ==================== İNDİRİLMİŞ GÖRSELLER ====================

@app.get("/api/downloaded")
async def get_downloaded_images(
    category: Optional[str] = Query(None, description="Kategori filtresi")
):
    """İndirilmiş görselleri listele"""
    images = download_service.get_downloaded_images(category_slug=category)
    
    # Görsellerin web URL'lerini oluştur
    for img in images:
        relative_path = os.path.relpath(img["file_path"], str(DOWNLOADS_DIR))
        img["web_url"] = f"/downloads/{relative_path.replace(os.sep, '/')}"
    
    return {
        "success": True,
        "images": images,
        "total": len(images)
    }


@app.get("/api/downloaded/{category}/{filename}")
async def get_downloaded_image(category: str, filename: str):
    """İndirilmiş görseli getir"""
    file_path = DOWNLOADS_DIR / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    
    return FileResponse(str(file_path))


@app.get("/api/open-downloads-folder")
async def open_downloads_folder():
    """İndirme klasörünü Windows Explorer'da aç"""
    import subprocess
    import platform
    
    try:
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{DOWNLOADS_DIR}"')
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(DOWNLOADS_DIR)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(DOWNLOADS_DIR)])
        
        return {
            "success": True,
            "path": str(DOWNLOADS_DIR),
            "message": "Klasör açıldı"
        }
    except Exception as e:
        return {
            "success": False,
            "path": str(DOWNLOADS_DIR),
            "error": str(e)
        }


# ==================== İSTATİSTİKLER ====================

@app.get("/api/stats")
async def get_statistics():
    """İstatistikleri getir"""
    with get_db() as db:
        # Kategori istatistikleri
        categories = db.query(Category).all()
        
        # Toplam indirilen görsel sayısı
        downloaded_images = download_service.get_downloaded_images()
        
        # Kategori bazlı dağılım
        category_stats = {}
        for img in downloaded_images:
            cat = img.get("category", "diger")
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        return {
            "success": True,
            "total_downloaded": len(downloaded_images),
            "categories": [cat.to_dict() for cat in categories],
            "category_distribution": category_stats,
            "total_size_mb": round(
                sum(img.get("file_size", 0) for img in downloaded_images) / (1024 * 1024), 
                2
            )
        }


# ==================== ARAMA GEÇMİŞİ ====================

@app.get("/api/history")
async def get_search_history(limit: int = Query(20, ge=1, le=100)):
    """Arama geçmişini getir"""
    with get_db() as db:
        history = db.query(SearchHistory).order_by(
            SearchHistory.created_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "history": [h.to_dict() for h in history]
        }


@app.delete("/api/history")
async def clear_search_history():
    """Arama geçmişini temizle"""
    with get_db() as db:
        db.query(SearchHistory).delete()
        db.commit()
        return {"success": True, "message": "Geçmiş temizlendi"}


# ==================== FAVORİLER ====================

@app.post("/api/favorites/{image_id}")
async def toggle_favorite(image_id: int):
    """Favori durumunu değiştir"""
    with get_db() as db:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Görsel bulunamadı")
        
        image.is_favorite = not image.is_favorite
        db.commit()
        
        return {
            "success": True,
            "is_favorite": image.is_favorite
        }


@app.get("/api/favorites")
async def get_favorites():
    """Favori görselleri getir"""
    with get_db() as db:
        favorites = db.query(Image).filter(Image.is_favorite == True).all()
        return {
            "success": True,
            "images": [img.to_dict() for img in favorites],
            "total": len(favorites)
        }


# Uygulamayı çalıştır
if __name__ == "__main__":
    import uvicorn
    print("🎖️ WW2 Görsel Arşivi başlatılıyor...")
    print("📍 http://localhost:8000")
    print("📚 API Dokümantasyonu: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
