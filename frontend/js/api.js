/**
 * WW2 Görsel Arşivi - API İstemcisi
 * Backend ile iletişim
 */

const API_BASE = window.ENV?.API_BASE || '';

class ApiClient {
    /**
     * API isteği gönder
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE}/api${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== KATEGORİLER ====================

    /**
     * Tüm kategorileri getir
     */
    async getCategories() {
        return this.request('/categories');
    }

    /**
     * Belirli bir kategoriyi getir
     */
    async getCategory(slug) {
        return this.request(`/categories/${slug}`);
    }

    // ==================== ARAMA ====================

    /**
     * Görsel ara
     * @param {string} query - Arama terimi
     * @param {Object} options - Arama seçenekleri
     */
    async searchImages(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            limit: options.limit || 50,
            min_width: options.minWidth || 800,
        });

        if (options.category) {
            params.append('category', options.category);
        }

        return this.request(`/search?${params.toString()}`);
    }

    /**
     * Kategori bazlı görseller getir
     */
    async getCategoryImages(slug, limit = 50) {
        return this.request(`/category-images/${slug}?limit=${limit}`);
    }

    /**
     * Tüm kaynaklarda ara (Wikimedia + NARA + Archive.org)
     */
    async searchAllSources(query, limit = 100) {
        return this.request(`/search-all?q=${encodeURIComponent(query)}&limit=${limit}`);
    }

    /**
     * Video ara (Archive.org)
     */
    async searchVideos(query, limit = 30) {
        return this.request(`/videos?q=${encodeURIComponent(query)}&limit=${limit}`);
    }

    /**
     * Kategori videolarını getir
     */
    async getCategoryVideos(category, limit = 20) {
        return this.request(`/videos/${category}?limit=${limit}`);
    }

    // ==================== İNDİRME ====================

    /**
     * Tek görsel indir
     */
    async downloadImage(url, category, title = null) {
        const params = new URLSearchParams({
            url: url,
            category: category || 'diger',
        });

        if (title) {
            params.append('title', title);
        }

        return this.request(`/download?${params.toString()}`, {
            method: 'POST',
        });
    }

    /**
     * Toplu indirme
     */
    async downloadBatch(images, categorySlug) {
        return this.request('/download-batch', {
            method: 'POST',
            body: JSON.stringify({
                images: images,
                category_slug: categorySlug,
            }),
        });
    }

    // ==================== İNDİRİLMİŞ GÖRSELLER ====================

    /**
     * İndirilmiş görselleri listele
     */
    async getDownloadedImages(category = null) {
        const params = category ? `?category=${category}` : '';
        return this.request(`/downloaded${params}`);
    }

    /**
     * İndirme klasörünü aç
     */
    async openDownloadsFolder() {
        return this.request('/open-downloads-folder');
    }

    // ==================== İSTATİSTİKLER ====================

    /**
     * İstatistikleri getir
     */
    async getStats() {
        return this.request('/stats');
    }

    // ==================== ARAMA GEÇMİŞİ ====================

    /**
     * Arama geçmişini getir
     */
    async getSearchHistory(limit = 20) {
        return this.request(`/history?limit=${limit}`);
    }

    /**
     * Arama geçmişini temizle
     */
    async clearSearchHistory() {
        return this.request('/history', {
            method: 'DELETE',
        });
    }

    // ==================== FAVORİLER ====================

    /**
     * Favori durumunu değiştir
     */
    async toggleFavorite(imageId) {
        return this.request(`/favorites/${imageId}`, {
            method: 'POST',
        });
    }

    /**
     * Favori görselleri getir
     */
    async getFavorites() {
        return this.request('/favorites');
    }

    // ==================== SAĞLIK KONTROLÜ ====================

    /**
     * API sağlık kontrolü
     */
    async healthCheck() {
        return this.request('/health');
    }
}

// Global API instance
const api = new ApiClient();
