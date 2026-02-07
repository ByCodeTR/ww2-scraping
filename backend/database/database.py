"""
Veritabanı bağlantı yönetimi
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager

from .models import Base, Category

# Proje kök dizini
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "ww2_archive.db")

# Dizin yoksa oluştur
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite bağlantısı
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Veritabanını ve tabloları oluştur"""
    Base.metadata.create_all(bind=engine)
    
    # Varsayılan kategorileri ekle
    _create_default_categories()


def _create_default_categories():
    """Varsayılan kategorileri oluştur"""
    default_categories = [
        {"name": "Tanklar & Zırhlı Araçlar", "slug": "tanklar", "icon": "🔸", 
         "description": "Panzer, Sherman, T-34 ve diğer zırhlı araçlar"},
        {"name": "Uçaklar & Hava Kuvvetleri", "slug": "ucaklar", "icon": "✈️",
         "description": "Savaş uçakları, bombardıman uçakları, pilotlar"},
        {"name": "Gemiler & Deniz Kuvvetleri", "slug": "gemiler", "icon": "🚢",
         "description": "Savaş gemileri, denizaltılar, deniz muharebeleri"},
        {"name": "Askerler & Portreler", "slug": "askerler", "icon": "👤",
         "description": "Asker fotoğrafları, portreler, günlük yaşam"},
        {"name": "Haritalar & Stratejiler", "slug": "haritalar", "icon": "🗺️",
         "description": "Savaş haritaları, strateji planları, cephe hatları"},
        {"name": "Savaş Sahneleri", "slug": "savas_sahneleri", "icon": "💥",
         "description": "Muharebe fotoğrafları, çatışma anları"},
        {"name": "Propaganda Posterleri", "slug": "posterler", "icon": "📜",
         "description": "Dönemin propaganda afişleri ve posterleri"},
        {"name": "Liderler & Generaller", "slug": "liderler", "icon": "👔",
         "description": "Askeri ve siyasi liderler, generaller, komutanlar"},
    ]
    
    with get_db() as db:
        for cat_data in default_categories:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)
        db.commit()


@contextmanager
def get_db():
    """Veritabanı oturumu context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """FastAPI dependency için veritabanı oturumu"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
