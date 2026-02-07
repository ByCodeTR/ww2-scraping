"""
Veritabanı modelleri - WW2 Görsel Arşivi
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Category(Base):
    """Görsel kategorileri"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # Türkçe isim
    slug = Column(String(100), nullable=False, unique=True)  # URL-friendly isim
    icon = Column(String(50), default="📁")  # Emoji ikon
    description = Column(Text, nullable=True)
    image_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    images = relationship("Image", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "icon": self.icon,
            "description": self.description,
            "image_count": self.image_count
        }


class Image(Base):
    """İndirilen görseller"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=False)  # Orijinal kaynak URL
    thumbnail_url = Column(String(1000), nullable=True)  # Küçük önizleme
    file_path = Column(String(500), nullable=True)  # Yerel dosya yolu
    file_name = Column(String(255), nullable=True)
    
    # Görsel bilgileri
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(50), nullable=True)
    
    # Kaynak bilgileri
    source = Column(String(100), default="wikimedia")  # wikimedia, national_archives, etc.
    source_id = Column(String(255), nullable=True)  # Kaynaktaki benzersiz ID
    license = Column(String(100), nullable=True)
    author = Column(String(255), nullable=True)
    
    # Durum
    is_downloaded = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    download_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Kategori ilişkisi
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="images")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source_url": self.source_url,
            "thumbnail_url": self.thumbnail_url,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "source": self.source,
            "license": self.license,
            "author": self.author,
            "is_downloaded": self.is_downloaded,
            "is_favorite": self.is_favorite,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "download_date": self.download_date.isoformat() if self.download_date else None
        }


class SearchHistory(Base):
    """Arama geçmişi"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "query": self.query,
            "results_count": self.results_count,
            "category_id": self.category_id,
            "created_at": self.created_at.isoformat()
        }


class DownloadQueue(Base):
    """İndirme kuyruğu"""
    __tablename__ = "download_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, downloading, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    image = relationship("Image")

    def to_dict(self):
        return {
            "id": self.id,
            "image_id": self.image_id,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message
        }
