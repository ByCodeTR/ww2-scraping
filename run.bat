@echo off
chcp 65001 > nul
title WW2 Görsel Arşivi

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║   🎖️  WW2 GÖRSEL ARŞİVİ                                   ║
echo  ║   İkinci Dünya Savaşı Görsel Koleksiyonu                  ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: Proje dizinine git
cd /d "%~dp0"

:: Python kontrolü
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadı! Lütfen Python 3.8+ yükleyin.
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Virtual environment kontrolü
if not exist "venv" (
    echo 📦 Virtual environment oluşturuluyor...
    python -m venv venv
    echo ✅ Virtual environment oluşturuldu.
)

:: Virtual environment aktif et
call venv\Scripts\activate.bat

:: Gereksinimleri kontrol et
echo 📦 Gereksinimler kontrol ediliyor...
pip install -r requirements.txt -q

:: Uygulamayı başlat
echo.
echo 🚀 Uygulama başlatılıyor...
echo.
echo ════════════════════════════════════════════════════════════════
echo    📍 Uygulama: http://localhost:8000
echo    📚 API Docs: http://localhost:8000/docs
echo    
echo    Durdurmak için Ctrl+C basın
echo ════════════════════════════════════════════════════════════════
echo.

:: Tarayıcıyı aç (2 saniye sonra)
start "" "http://localhost:8000"

:: Sunucuyu başlat
python backend\main.py

pause
