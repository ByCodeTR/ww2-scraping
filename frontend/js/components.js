/**
 * WW2 Görsel Arşivi - UI Bileşenleri
 * Yeniden kullanılabilir UI component'leri
 */

/**
 * Görsel kartı oluştur
 */
function createImageCard(image, isSelected = false) {
    const card = document.createElement('div');
    card.className = `image-card${isSelected ? ' selected' : ''}`;
    card.dataset.imageId = image.source_id || image.id;
    card.dataset.imageData = JSON.stringify(image);

    // Dosya boyutunu formatla
    const fileSize = formatFileSize(image.file_size);
    const resolution = image.width && image.height ? `${image.width}×${image.height}` : '';

    card.innerHTML = `
        <div class="image-card-checkbox" title="Seç"></div>
        ${image.is_downloaded ? '<span class="image-card-badge">✓ İndirildi</span>' : ''}
        <img 
            src="${image.thumbnail_url || image.source_url}" 
            alt="${escapeHtml(image.title)}"
            class="image-card-image"
            loading="lazy"
            onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%231a1a25%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 fill=%22%23606070%22 font-size=%2212%22>Yüklenemedi</text></svg>'"
        >
        <div class="image-card-overlay"></div>
        <div class="image-card-content">
            <h4 class="image-card-title">${escapeHtml(image.title)}</h4>
            <div class="image-card-meta">
                ${resolution ? `<span>📐 ${resolution}</span>` : ''}
                ${fileSize ? `<span>📦 ${fileSize}</span>` : ''}
            </div>
        </div>
    `;

    return card;
}

/**
 * Kategori liste öğesi oluştur
 */
function createCategoryItem(category) {
    const li = document.createElement('li');
    li.className = 'category-item';
    li.dataset.category = category.slug;

    // Sayaç sadece 0'dan büyükse göster
    const countHtml = category.image_count > 0
        ? `<span class="category-count">${category.image_count}</span>`
        : '';

    li.innerHTML = `
        <span class="category-icon">${category.icon || '📁'}</span>
        <span class="category-name">${escapeHtml(category.name)}</span>
        ${countHtml}
    `;

    return li;
}

/**
 * Toast bildirimi göster
 */
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close">✕</button>
    `;

    // Kapatma butonu
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    container.appendChild(toast);

    // Otomatik kaldır
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'toastSlide 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);

    return toast;
}

/**
 * Modal göster/gizle
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

/**
 * Loading overlay göster/gizle
 */
function showLoading(message = 'Yükleniyor...') {
    const overlay = document.getElementById('loadingOverlay');
    const text = overlay.querySelector('.loading-text');
    if (text) text.textContent = message;
    overlay.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

/**
 * İndirme ilerleme modalını güncelle
 */
function updateDownloadProgress(current, total, status) {
    const progressFill = document.getElementById('progressFill');
    const downloadStatus = document.getElementById('downloadStatus');
    const downloadCount = document.getElementById('downloadCount');

    const percentage = Math.round((current / total) * 100);

    if (progressFill) progressFill.style.width = `${percentage}%`;
    if (downloadStatus) downloadStatus.textContent = status;
    if (downloadCount) downloadCount.textContent = `${current} / ${total}`;
}

/**
 * Görsel detay modalını doldur
 */
function populateImageModal(image) {
    document.getElementById('modalImage').src = image.source_url || image.thumbnail_url;
    document.getElementById('modalTitle').textContent = image.title || 'İsimsiz';
    document.getElementById('modalDescription').textContent = image.description || 'Açıklama yok';
    document.getElementById('modalSize').textContent = formatFileSize(image.file_size);
    document.getElementById('modalResolution').textContent =
        image.width && image.height ? `${image.width} × ${image.height} px` : 'Bilinmiyor';
    document.getElementById('modalSource').textContent = image.source || 'Wikimedia Commons';

    // Lisansı basitleştir: Telifli / Telifsiz
    const license = (image.license || '').toLowerCase();
    const isFree = license.includes('public domain') ||
        license.includes('cc0') ||
        license.includes('cc by') ||
        license.includes('pd') ||
        license.includes('no restrictions') ||
        license === '';
    document.getElementById('modalLicense').textContent = isFree ? '✅ Telifsiz' : '⚠️ Telifli';
    document.getElementById('modalLicense').style.color = isFree ? '#4ade80' : '#facc15';

    document.getElementById('modalSourceLink').href = image.source_url || '#';

    // Modal'a image data'yı kaydet
    const modal = document.getElementById('imageModal');
    modal.dataset.currentImage = JSON.stringify(image);
}

/**
 * Dosya boyutunu formatla
 */
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '';

    const units = ['B', 'KB', 'MB', 'GB'];
    let unitIndex = 0;
    let size = bytes;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * HTML escape
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Debounce fonksiyonu
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Empty state göster
 */
function showEmptyState(message = null, icon = '🖼️') {
    const grid = document.getElementById('imageGrid');
    const emptyState = document.getElementById('emptyState');

    // Mevcut kartları temizle
    grid.querySelectorAll('.image-card').forEach(card => card.remove());

    if (emptyState) {
        if (message) {
            emptyState.querySelector('h3').textContent = message;
        }
        emptyState.querySelector('.empty-icon').textContent = icon;
        emptyState.classList.remove('hidden');
    }
}

/**
 * Empty state gizle
 */
function hideEmptyState() {
    const emptyState = document.getElementById('emptyState');
    if (emptyState) {
        emptyState.classList.add('hidden');
    }
}

/**
 * Confirmation dialog
 */
function confirm(message) {
    return new Promise((resolve) => {
        // Basit confirm için browser'ın native dialog'unu kullan
        resolve(window.confirm(message));
    });
}
