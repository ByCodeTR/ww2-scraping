/**
 * Environment Configuration
 * Bu dosya deploy ortamına göre API URL'ini ayarlar
 */

// Render backend URL'ini buraya ekle (deploy sonrası)
const ENV = {
    // Production'da Render URL'i olacak, local'de boş string
    API_BASE: window.location.hostname === 'localhost' ? '' : 'https://ww2-scraping-api.onrender.com'
};

// Global olarak erişilebilir yap
window.ENV = ENV;
