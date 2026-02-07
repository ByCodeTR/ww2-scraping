# WW2 Görsel Arşivi 🎖️

İkinci Dünya Savaşı görselleri için kapsamlı scraping ve arşivleme uygulaması.

## 🚀 Hızlı Başlangıç

### Windows
```batch
run.bat
```

### Manuel Kurulum
```bash
# 1. Virtual environment oluştur
python -m venv venv

# 2. Aktif et
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Gereksinimleri yükle
pip install -r requirements.txt

# 4. Uygulamayı başlat
python backend/main.py
```

## 📍 Erişim
- **Uygulama**: http://localhost:8000
- **API Dokümantasyonu**: http://localhost:8000/docs

## 📁 Proje Yapısı

```
WW2-Gorsel-Arsivi/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Ana uygulama
│   ├── database/           # SQLite veritabanı
│   ├── scrapers/           # Wikimedia scraper
│   └── services/           # İndirme servisi
├── frontend/               # Web arayüzü
│   ├── index.html          # Ana sayfa
│   ├── css/                # Stiller
│   └── js/                 # JavaScript
├── downloads/              # İndirilen görseller
│   ├── tanklar/
│   ├── ucaklar/
│   ├── gemiler/
│   └── ...
├── requirements.txt        # Python bağımlılıkları
└── run.bat                 # Tek tıkla çalıştırma
```

## 🎨 Özellikler

- ✅ **Modern Dark Theme** - Göz yormayan, şık arayüz
- ✅ **8 Kategori** - Tanklar, Uçaklar, Gemiler, Askerler, Haritalar, Savaş Sahneleri, Posterler, Liderler
- ✅ **HD Öncelikli** - Yüksek çözünürlüklü görselleri öncelikli indir
- ✅ **Toplu İndirme** - Birden fazla görseli tek seferde indir
- ✅ **Türkçe Arayüz** - Tamamen Türkçe

## 📜 Lisans

Bu uygulama eğitim amaçlıdır. İndirilen görseller genellikle Public Domain veya Creative Commons lisanslıdır.

---

Made with ❤️ for WW2 History Enthusiasts
