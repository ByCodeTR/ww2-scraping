/**
 * WW2 Görsel Arşivi - Ana Uygulama
 * State yönetimi ve event handling
 */

// Uygulama State
const state = {
    currentView: 'search',      // search, category, downloaded, favorites
    currentCategory: null,
    currentQuery: '',
    images: [],
    selectedImages: new Set(),
    categories: [],
    isLoading: false,
    minWidth: 600,
};

// DOM Elements
const elements = {
    searchInput: null,
    searchClear: null,
    categoryList: null,
    imageGrid: null,
    emptyState: null,
    pageTitle: null,
    pageSubtitle: null,
    downloadSelectedBtn: null,
    selectedCount: null,
    selectAllCheckbox: null,
    widthSelect: null,
    loadMoreContainer: null,
    modalCategorySelect: null,
};

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', async () => {
    // DOM elementlerini cache'le
    cacheElements();

    // Event listener'ları ekle
    setupEventListeners();

    // Kategorileri yükle
    await loadCategories();

    // İstatistikleri yükle
    await loadStats();

    // Hazır
    hideLoading();
    console.log('🎖️ WW2 Görsel Arşivi hazır!');
});

function cacheElements() {
    elements.searchInput = document.getElementById('searchInput');
    elements.searchClear = document.getElementById('searchClear');
    elements.categoryList = document.getElementById('categoryList');
    elements.imageGrid = document.getElementById('imageGrid');
    elements.emptyState = document.getElementById('emptyState');
    elements.pageTitle = document.getElementById('pageTitle');
    elements.pageSubtitle = document.getElementById('pageSubtitle');
    elements.downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
    elements.selectedCount = document.getElementById('selectedCount');
    elements.selectAllCheckbox = document.getElementById('selectAllCheckbox');
    elements.widthSelect = document.getElementById('widthSelect');
    elements.loadMoreContainer = document.getElementById('loadMoreContainer');
    elements.modalCategorySelect = document.getElementById('modalCategorySelect');
}

function setupEventListeners() {
    // Arama - Sadece Enter'a basınca
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Arama kutusu değiştiğinde clear butonunu güncelle
    elements.searchInput.addEventListener('input', () => {
        if (elements.searchInput.value.trim()) {
            elements.searchClear.classList.remove('hidden');
        } else {
            elements.searchClear.classList.add('hidden');
        }
    });

    elements.searchClear.addEventListener('click', clearSearch);

    // Hızlı arama butonları
    document.querySelectorAll('.quick-search-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.searchInput.value = btn.dataset.query;
            handleSearch();
        });
    });

    // Minimum genişlik filtresi
    elements.widthSelect.addEventListener('change', () => {
        state.minWidth = parseInt(elements.widthSelect.value);
        if (state.currentQuery) {
            handleSearch();
        }
    });

    // Tümünü seç
    elements.selectAllCheckbox.addEventListener('change', toggleSelectAll);

    // Seçilenleri indir
    elements.downloadSelectedBtn.addEventListener('click', downloadSelected);

    // Yenile butonu
    document.getElementById('refreshBtn').addEventListener('click', refresh);

    // Koleksiyon menüsü (İndirilenler, Favoriler, Videolar)
    document.querySelectorAll('.category-item[data-view]').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            if (view === 'downloaded') {
                loadDownloadedImages();
            } else if (view === 'favorites') {
                loadFavorites();
            } else if (view === 'videos') {
                loadVideos(item.dataset.query);
            }
        });
    });

    // Image grid tıklama (event delegation)
    elements.imageGrid.addEventListener('click', handleImageGridClick);

    // Modal event'leri
    document.getElementById('modalBackdrop').addEventListener('click', () => hideModal('imageModal'));
    document.getElementById('modalClose').addEventListener('click', () => hideModal('imageModal'));
    document.getElementById('modalDownloadBtn').addEventListener('click', downloadCurrentImage);
    document.getElementById('modalFavoriteBtn').addEventListener('click', toggleCurrentFavorite);

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboard);
}

// ==================== KATEGORİLER ====================

async function loadCategories() {
    try {
        const result = await api.getCategories();

        if (result.success && result.categories) {
            state.categories = result.categories;
            renderCategories(result.categories);
            populateCategorySelect(result.categories);
        }
    } catch (error) {
        console.error('Kategoriler yüklenemedi:', error);
        showToast('Kategoriler yüklenirken hata oluştu', 'error');
    }
}

function renderCategories(categories) {
    elements.categoryList.innerHTML = '';

    categories.forEach(category => {
        const item = createCategoryItem(category);
        item.addEventListener('click', () => selectCategory(category));
        elements.categoryList.appendChild(item);
    });
}

function populateCategorySelect(categories) {
    const select = elements.modalCategorySelect;
    select.innerHTML = '<option value="diger">Kategori Seç...</option>';

    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.slug;
        option.textContent = `${category.icon} ${category.name}`;
        select.appendChild(option);
    });
}

async function selectCategory(category) {
    // Aktif kategoriyi güncelle
    state.currentView = 'category';
    state.currentCategory = category.slug;
    state.currentQuery = '';
    elements.searchInput.value = '';

    // UI güncelle
    updateActiveCategory(category.slug);
    setPageTitle(category.name, `${category.icon} ${category.description || ''}`);

    // Görselleri yükle
    await loadCategoryImages(category.slug);
}

function updateActiveCategory(slug) {
    document.querySelectorAll('.category-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.category === slug) {
            item.classList.add('active');
        }
    });
}

async function loadCategoryImages(slug) {
    showLoading('Görseller yükleniyor...');

    try {
        const result = await api.getCategoryImages(slug, 100);

        if (result.success) {
            state.images = result.images || [];
            renderImages(state.images);

            if (state.images.length === 0) {
                showEmptyState('Bu kategoride henüz görsel yok', '📭');
            }
        }
    } catch (error) {
        console.error('Kategori görselleri yüklenemedi:', error);
        showToast('Görseller yüklenirken hata oluştu', 'error');
        showEmptyState('Görseller yüklenemedi', '❌');
    } finally {
        hideLoading();
    }
}

// ==================== ARAMA ====================

async function handleSearch() {
    const query = elements.searchInput.value.trim();

    if (!query) {
        elements.searchClear.classList.add('hidden');
        return;
    }

    elements.searchClear.classList.remove('hidden');

    state.currentView = 'search';
    state.currentQuery = query;
    state.currentCategory = null;

    // Kategori seçimini temizle
    updateActiveCategory(null);
    setPageTitle(`"${query}" Araması`, 'Görseller ve videolar aranıyor...');

    showLoading('Aranıyor...');

    // Tab elementlerini seç
    elements.searchTabs = document.getElementById('searchTabs');
    elements.tabImageCount = document.getElementById('tabImageCount');
    elements.tabVideoCount = document.getElementById('tabVideoCount');

    // Tab click eventleri (sadece bir kez eklenmeli, burada kontrol edelim)
    if (!elements.tabsInitialized) {
        document.querySelectorAll('.search-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                switchSearchTab(tabName);
            });
        });
        elements.tabsInitialized = true;
    }

    try {
        // Paralel olarak hem görsel hem video ara
        const [imageResult, videoResult] = await Promise.all([
            api.searchImages(query, {
                limit: 50,
                minWidth: state.minWidth,
                category: state.currentCategory,
            }),
            api.searchVideos(query, 30)
        ]);

        const images = imageResult.success ? (imageResult.images || []) : [];
        const videos = videoResult.success ? (videoResult.videos || []) : [];

        // Sonuçları state'e kaydet
        state.searchResultImages = images;
        state.searchResultVideos = videos;

        // Tab sayılarını güncelle
        elements.tabImageCount.textContent = images.length;
        elements.tabVideoCount.textContent = videos.length;

        // Tabları göster
        elements.searchTabs.classList.remove('hidden');

        // Varsayılan olarak görseller tabını aç
        if (images.length > 0) {
            switchSearchTab('images');
        } else if (videos.length > 0) {
            switchSearchTab('videos');
        } else {
            switchSearchTab('images');
            showEmptyState('Sonuç bulunamadı', '🔍');
            elements.searchTabs.classList.add('hidden');
        }

        const totalResults = images.length + videos.length;
        setPageTitle(
            `"${query}" Araması`,
            `${totalResults} sonuç bulundu`
        );

    } catch (error) {
        console.error('Arama hatası:', error);
        showToast('Arama sırasında hata oluştu', 'error');
        showEmptyState('Arama yapılamadı', '❌');
    } finally {
        hideLoading();
    }
}

function switchSearchTab(tabName) {
    // Aktif tab stilini güncelle
    document.querySelectorAll('.search-tab').forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    hideEmptyState();
    elements.imageGrid.innerHTML = ''; // Grid'i temizle

    if (tabName === 'images') {
        const images = state.searchResultImages || [];
        state.images = images;

        if (images.length === 0) {
            showEmptyState('Görsel bulunamadı', '🖼️');
        } else {
            images.forEach(image => {
                const card = createImageCard(image, state.selectedImages.has(image.source_id));
                elements.imageGrid.appendChild(card);
            });
        }
        elements.downloadSelectedBtn.disabled = state.selectedImages.size === 0;

    } else if (tabName === 'videos') {
        const videos = state.searchResultVideos || [];

        if (videos.length === 0) {
            showEmptyState('Video bulunamadı', '🎬');
        } else {
            videos.forEach(video => {
                const card = createVideoCard(video);
                elements.imageGrid.appendChild(card);
            });
        }
    }

    updateSelectionUI();
}

function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'image-card video-card';
    card.innerHTML = `
        <div class="video-badge">🎬 Video</div>
        <div class="video-license">✅ Telifsiz</div>
        <img 
            src="${video.thumbnail_url}" 
            alt="${escapeHtml(video.title)}"
            class="image-card-image"
            loading="lazy"
            onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%231a1a25%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 fill=%22%23606070%22 font-size=%2212%22>Video</text></svg>'"
        >
        <div class="image-card-overlay"></div>
        <div class="image-card-content">
            <h4 class="image-card-title">${escapeHtml(video.title)}</h4>
            <div class="image-card-meta">
                <span>📥 ${video.downloads || 0} indirme</span>
                ${video.year ? `<span>📅 ${video.year}</span>` : ''}
            </div>
            <div class="video-actions">
                <button class="btn btn-primary btn-small video-download-btn">⬇️ İndir</button>
                <button class="btn btn-secondary btn-small video-watch-btn">▶️ İzle</button>
            </div>
        </div>
    `;

    // İndir butonu
    card.querySelector('.video-download-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        window.open(video.download_url, '_blank');
        showToast('İndirme sayfası açıldı', 'success');
    });

    // İzle butonu  
    card.querySelector('.video-watch-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        window.open(video.page_url, '_blank');
    });

    // Kart tıklama
    card.addEventListener('click', () => {
        window.open(video.page_url, '_blank');
    });

    return card;
}

function clearSearch() {
    elements.searchInput.value = '';
    elements.searchClear.classList.add('hidden');
    state.currentQuery = '';

    // Varsayılan görünüme dön
    if (state.currentCategory) {
        loadCategoryImages(state.currentCategory);
    } else {
        state.images = [];
        renderImages([]);
        setPageTitle('Aramaya Başla', 'WW2 görselleri arayın veya kategorilere göz atın');
        showEmptyState();
    }
}

// ==================== GÖRSEL RENDER ====================

function renderImages(images) {
    // Empty state'i gizle
    hideEmptyState();

    // Mevcut kartları temizle
    elements.imageGrid.querySelectorAll('.image-card').forEach(card => card.remove());

    // Yeni kartları ekle
    images.forEach(image => {
        const isSelected = state.selectedImages.has(image.source_id || image.id);
        const card = createImageCard(image, isSelected);
        elements.imageGrid.appendChild(card);
    });

    // Seçim durumunu güncelle
    updateSelectionUI();
}

function handleImageGridClick(e) {
    const card = e.target.closest('.image-card');
    if (!card) return;

    const checkbox = e.target.closest('.image-card-checkbox');

    if (checkbox) {
        // Checkbox tıklandı - seçimi değiştir
        toggleImageSelection(card);
    } else {
        // Kart tıklandı - modal aç
        openImageModal(card);
    }
}

function toggleImageSelection(card) {
    const imageId = card.dataset.imageId;

    if (state.selectedImages.has(imageId)) {
        state.selectedImages.delete(imageId);
        card.classList.remove('selected');
    } else {
        state.selectedImages.add(imageId);
        card.classList.add('selected');
    }

    updateSelectionUI();
}

function toggleSelectAll() {
    const isChecked = elements.selectAllCheckbox.checked;

    if (isChecked) {
        // Tümünü seç
        state.images.forEach(image => {
            state.selectedImages.add(image.source_id || image.id);
        });
    } else {
        // Tümünü temizle
        state.selectedImages.clear();
    }

    // Kartları güncelle
    document.querySelectorAll('.image-card').forEach(card => {
        if (isChecked) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });

    updateSelectionUI();
}

function updateSelectionUI() {
    const count = state.selectedImages.size;

    // Download butonu
    elements.downloadSelectedBtn.disabled = count === 0;

    // Badge
    const badge = elements.selectedCount;
    if (count > 0) {
        badge.textContent = count;
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }

    // Tümünü seç checkbox
    elements.selectAllCheckbox.checked = count > 0 && count === state.images.length;
}

// ==================== MODAL ====================

function openImageModal(card) {
    try {
        const imageData = JSON.parse(card.dataset.imageData);
        populateImageModal(imageData);
        showModal('imageModal');
    } catch (error) {
        console.error('Modal açılamadı:', error);
    }
}

async function downloadCurrentImage() {
    const modal = document.getElementById('imageModal');
    const imageData = JSON.parse(modal.dataset.currentImage);
    const category = elements.modalCategorySelect.value;

    const downloadBtn = document.getElementById('modalDownloadBtn');
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">İndiriliyor...</span>';

    try {
        const result = await api.downloadImage(
            imageData.source_url,
            category,
            imageData.title
        );

        if (result.success) {
            showToast('Görsel başarıyla indirildi!', 'success');

            // Kartı güncelle
            const card = document.querySelector(`[data-image-id="${imageData.source_id}"]`);
            if (card && !card.querySelector('.image-card-badge')) {
                const badge = document.createElement('span');
                badge.className = 'image-card-badge';
                badge.textContent = '✓ İndirildi';
                card.appendChild(badge);
            }

            await loadStats();
        }
    } catch (error) {
        console.error('İndirme hatası:', error);
        showToast('İndirme sırasında hata oluştu', 'error');
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<span class="btn-icon">⬇️</span><span class="btn-text">İndir</span>';
    }
}

async function toggleCurrentFavorite() {
    // Şimdilik sadece toast göster
    showToast('Favoriler özelliği yakında!', 'info');
}

// ==================== TOPLU İNDİRME ====================

async function downloadSelected() {
    if (state.selectedImages.size === 0) {
        showToast('Lütfen önce görsel seçin', 'warning');
        return;
    }

    // Seçili görselleri bul
    const selectedImageData = state.images.filter(img =>
        state.selectedImages.has(img.source_id || img.id)
    );

    // Kategori seç (varsayılan olarak ilk kategori veya diger)
    const category = state.currentCategory || 'diger';

    // Progress modal'ı göster
    showModal('downloadModal');
    updateDownloadProgress(0, selectedImageData.length, 'Hazırlanıyor...');

    try {
        const result = await api.downloadBatch(selectedImageData, category);

        if (result.success) {
            updateDownloadProgress(
                result.downloaded + result.skipped,
                result.total,
                'Tamamlandı!'
            );

            setTimeout(() => {
                hideModal('downloadModal');
                showToast(
                    `${result.downloaded} görsel indirildi, ${result.skipped} atlandı`,
                    result.failed > 0 ? 'warning' : 'success'
                );

                // Seçimi temizle
                state.selectedImages.clear();
                document.querySelectorAll('.image-card.selected').forEach(card => {
                    card.classList.remove('selected');
                });
                updateSelectionUI();

                // İstatistikleri güncelle
                loadStats();
            }, 1000);
        }
    } catch (error) {
        console.error('Toplu indirme hatası:', error);
        hideModal('downloadModal');
        showToast('İndirme sırasında hata oluştu', 'error');
    }
}

// ==================== İNDİRİLMİŞ GÖRSELLER ====================

async function loadDownloadedImages() {
    state.currentView = 'downloaded';
    state.currentCategory = null;
    state.currentQuery = '';

    updateActiveCategory(null);
    document.querySelector('[data-view="downloaded"]').classList.add('active');
    setPageTitle('İndirilen Görseller', 'Yerel koleksiyonunuz');

    // Klasörde Aç butonunu göster
    showOpenFolderButton();

    showLoading('Görseller yükleniyor...');

    try {
        const result = await api.getDownloadedImages();

        if (result.success) {
            // İndirilen görselleri uygun formata dönüştür
            const images = result.images.map(img => ({
                source_id: img.filename,
                title: img.filename,
                source_url: img.web_url,
                thumbnail_url: img.web_url,
                file_size: img.file_size,
                is_downloaded: true,
            }));

            state.images = images;
            renderImages(images);

            if (images.length === 0) {
                showEmptyState('Henüz görsel indirmediniz', '📭');
            }
        }
    } catch (error) {
        console.error('İndirilen görseller yüklenemedi:', error);
        showToast('Görseller yüklenirken hata oluştu', 'error');
    } finally {
        hideLoading();
    }
}

async function loadFavorites() {
    state.currentView = 'favorites';
    state.currentCategory = null;
    state.currentQuery = '';

    updateActiveCategory(null);
    document.querySelector('[data-view="favorites"]').classList.add('active');
    setPageTitle('Favoriler', 'Beğendiğiniz görseller');

    showEmptyState('Favori özelliği yakında!', '⭐');
}

// ==================== VİDEOLAR ====================

async function loadVideos(query) {
    state.currentView = 'videos';
    state.currentCategory = null;
    state.currentQuery = query;

    updateActiveCategory(null);
    // Video item'ı aktif yap
    document.querySelectorAll('[data-view="videos"]').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.query === query) {
            item.classList.add('active');
        }
    });

    setPageTitle('🎬 WW2 Videoları', `"${query}" araması`);
    showLoading('Videolar yükleniyor...');

    try {
        const result = await api.searchVideos(query, 30);

        if (result.success && result.videos) {
            renderVideos(result.videos);

            if (result.videos.length === 0) {
                showEmptyState('Video bulunamadı', '🎬');
            }
        }
    } catch (error) {
        console.error('Videolar yüklenemedi:', error);
        showToast('Videolar yüklenirken hata oluştu', 'error');
        showEmptyState('Videolar yüklenemedi', '❌');
    } finally {
        hideLoading();
    }
}

function renderVideos(videos) {
    hideEmptyState();

    // Mevcut içeriği temizle
    elements.imageGrid.querySelectorAll('.image-card, .video-card').forEach(card => card.remove());

    videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'image-card video-card';
        card.innerHTML = `
            <div class="video-badge">🎬 Video</div>
            <div class="video-license">✅ Telifsiz</div>
            <img 
                src="${video.thumbnail_url}" 
                alt="${escapeHtml(video.title)}"
                class="image-card-image"
                loading="lazy"
                onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%231a1a25%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 fill=%22%23606070%22 font-size=%2212%22>Video</text></svg>'"
            >
            <div class="image-card-overlay"></div>
            <div class="image-card-content">
                <h4 class="image-card-title">${escapeHtml(video.title)}</h4>
                <div class="image-card-meta">
                    <span>📥 ${video.downloads || 0} indirme</span>
                    ${video.year ? `<span>📅 ${video.year}</span>` : ''}
                </div>
                <div class="video-actions">
                    <button class="btn btn-primary btn-small video-download-btn" data-url="${video.download_url}">
                        ⬇️ İndir
                    </button>
                    <button class="btn btn-secondary btn-small video-watch-btn" data-url="${video.page_url}">
                        ▶️ İzle
                    </button>
                </div>
            </div>
        `;

        // İndir butonu
        card.querySelector('.video-download-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            window.open(video.download_url, '_blank');
            showToast('İndirme sayfası açıldı', 'success');
        });

        // İzle butonu  
        card.querySelector('.video-watch-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            window.open(video.page_url, '_blank');
        });

        // Kart tıklama - izle sayfası
        card.addEventListener('click', () => {
            window.open(video.page_url, '_blank');
        });

        elements.imageGrid.appendChild(card);
    });

    // Seçim UI'ını güncelle
    updateSelectionUI();
}

// ==================== İSTATİSTİKLER ====================

async function loadStats() {
    try {
        const result = await api.getStats();

        if (result.success) {
            const downloadCount = result.total_downloaded || 0;
            document.getElementById('totalImages').textContent = downloadCount;
            document.getElementById('totalSize').textContent = `${result.total_size_mb || 0} MB`;

            // İndirilen sayısını sadece 0'dan büyükse göster
            const downloadedCountEl = document.getElementById('downloadedCount');
            if (downloadCount > 0) {
                downloadedCountEl.textContent = downloadCount;
                downloadedCountEl.classList.remove('hidden');
            } else {
                downloadedCountEl.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('İstatistikler yüklenemedi:', error);
    }
}

// ==================== YARDIMCI FONKSİYONLAR ====================

function showOpenFolderButton() {
    // Mevcut buton varsa kaldır
    hideOpenFolderButton();

    // Yeni buton oluştur
    const btn = document.createElement('button');
    btn.id = 'openFolderBtn';
    btn.className = 'btn btn-secondary';
    btn.innerHTML = '<span class="btn-icon">📂</span><span class="btn-text">Klasörde Aç</span>';
    btn.onclick = openDownloadsFolder;

    // Header actions'a ekle
    const headerActions = document.querySelector('.header-actions');
    headerActions.insertBefore(btn, headerActions.firstChild);
}

function hideOpenFolderButton() {
    const btn = document.getElementById('openFolderBtn');
    if (btn) btn.remove();
}

async function openDownloadsFolder() {
    try {
        const result = await api.openDownloadsFolder();
        if (result.success) {
            showToast('Klasör açıldı! 📂', 'success');
        } else {
            showToast('Klasör yolu: ' + result.path, 'info');
        }
    } catch (error) {
        console.error('Klasör açılamadı:', error);
        showToast('Klasör açılamadı', 'error');
    }
}

function setPageTitle(title, subtitle = '') {
    // Eğer downloaded view değilse folder butonunu gizle
    if (state.currentView !== 'downloaded') {
        hideOpenFolderButton();
    }
    elements.pageTitle.textContent = title;
    elements.pageSubtitle.textContent = subtitle;
}

async function refresh() {
    if (state.currentView === 'category' && state.currentCategory) {
        await loadCategoryImages(state.currentCategory);
    } else if (state.currentView === 'search' && state.currentQuery) {
        await handleSearch();
    } else if (state.currentView === 'downloaded') {
        await loadDownloadedImages();
    } else {
        await loadCategories();
        await loadStats();
    }
    showToast('Yenilendi', 'success');
}

function handleKeyboard(e) {
    // ESC - Modal kapat
    if (e.key === 'Escape') {
        hideModal('imageModal');
        hideModal('downloadModal');
    }

    // Ctrl+A - Tümünü seç (input'ta değilse)
    if (e.ctrlKey && e.key === 'a' && document.activeElement !== elements.searchInput) {
        e.preventDefault();
        elements.selectAllCheckbox.checked = true;
        toggleSelectAll();
    }
}
