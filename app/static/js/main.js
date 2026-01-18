/**
 * Whale Wallet - Main JavaScript
 * Core utilities, API client, and shared functionality
 */

// ============================================
// API Client
// ============================================
const API = {
    baseUrl: '/api/v1',
    token: localStorage.getItem('whale_token'),

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                this.clearToken();
                window.location.href = '/login';
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            Toast.error(error.message);
            throw error;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    setToken(token) {
        this.token = token;
        localStorage.setItem('whale_token', token);
    },

    clearToken() {
        this.token = null;
        localStorage.removeItem('whale_token');
    },

    isAuthenticated() {
        return !!this.token;
    }
};

// ============================================
// Toast Notifications
// ============================================
const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 4000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
      <span class="toast-icon">${this.getIcon(type)}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

        this.container.appendChild(toast);

        if (duration > 0) {
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    },

    success(message) { this.show(message, 'success'); },
    error(message) { this.show(message, 'error'); },
    warning(message) { this.show(message, 'warning'); },
    info(message) { this.show(message, 'info'); },

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }
};

// ============================================
// Modal Manager
// ============================================
const Modal = {
    open(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },

    close(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    },

    closeAll() {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
};

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        Modal.closeAll();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        Modal.closeAll();
    }
});

// ============================================
// Format Utilities
// ============================================
const Format = {
    currency(value, currency = 'USD', compact = false) {
        const options = {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        };

        if (compact && Math.abs(value) >= 1000) {
            options.notation = 'compact';
        }

        return new Intl.NumberFormat('en-US', options).format(value);
    },

    number(value, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    },

    crypto(value, symbol) {
        const formatted = this.number(value, 6);
        return `${formatted} ${symbol}`;
    },

    address(address, chars = 6) {
        if (!address) return '';
        if (address.length <= chars * 2 + 3) return address;
        return `${address.slice(0, chars)}...${address.slice(-chars)}`;
    },

    date(dateString, options = {}) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            ...options
        });
    },

    time(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    relative(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return this.date(dateString);
    }
};

// ============================================
// Loading States
// ============================================
const Loading = {
    show(container) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (el) {
            el.classList.add('loading');
            el.innerHTML = `
        <div class="flex items-center justify-center p-xl">
          <div class="loading-spinner"></div>
        </div>
      `;
        }
    },

    hide(container) {
        const el = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (el) {
            el.classList.remove('loading');
        }
    },

    button(btn, loading = true) {
        if (loading) {
            btn.disabled = true;
            btn.dataset.originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading-spinner"></span>';
        } else {
            btn.disabled = false;
            btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
        }
    }
};

// ============================================
// Sidebar Toggle (Mobile)
// ============================================
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// ============================================
// Copy to Clipboard
// ============================================
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.success('Copied to clipboard');
    } catch (err) {
        Toast.error('Failed to copy');
    }
}

// ============================================
// Chart Colors
// ============================================
const ChartColors = {
    primary: '#00d4aa',
    secondary: '#0ea5e9',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    gradient: (ctx) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(0, 212, 170, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 212, 170, 0)');
        return gradient;
    }
};

// ============================================
// Chain Icons/Colors
// ============================================
const ChainMeta = {
    ethereum: { color: '#627eea', icon: '⧫' },
    bitcoin: { color: '#f7931a', icon: '₿' },
    solana: { color: '#14f195', icon: '◎' },
    polygon: { color: '#8247e5', icon: '⬡' },
    arbitrum: { color: '#28a0f0', icon: '🔷' },
    optimism: { color: '#ff0420', icon: '🔴' },
    base: { color: '#0052ff', icon: '🔵' },
    bsc: { color: '#f3ba2f', icon: '⬡' },
    avalanche: { color: '#e84142', icon: '🔺' },
    cosmos: { color: '#2e3148', icon: '⚛' },
    polkadot: { color: '#e6007a', icon: '●' },
    cardano: { color: '#0033ad', icon: '◆' },
    tron: { color: '#ff0013', icon: '⟁' },
    ton: { color: '#0088cc', icon: '💎' },
    near: { color: '#00c08b', icon: '⬢' },
    fantom: { color: '#1969ff', icon: '👻' },
    sui: { color: '#6fbcf0', icon: '💧' },
    aptos: { color: '#2dd8d8', icon: '🅰' }
};

// ============================================
// Form Validation
// ============================================
const Validate = {
    email(value) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(value);
    },

    address(value, chain = 'ethereum') {
        if (chain === 'ethereum' || chain === 'polygon' || chain === 'arbitrum' ||
            chain === 'optimism' || chain === 'base' || chain === 'bsc' ||
            chain === 'avalanche' || chain === 'fantom') {
            return /^0x[a-fA-F0-9]{40}$/.test(value);
        }
        if (chain === 'bitcoin') {
            return /^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$/.test(value);
        }
        if (chain === 'solana') {
            return /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(value);
        }
        return value.length > 0;
    },

    amount(value) {
        const num = parseFloat(value);
        return !isNaN(num) && num > 0;
    }
};

// ============================================
// Initialize on DOM Ready
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Check auth for protected pages
    const isLoginPage = window.location.pathname === '/login';

    if (!isLoginPage && !API.isAuthenticated()) {
        // Allow demo mode - comment out redirect for now
        // window.location.href = '/login';
    }

    // Initialize tooltips, popovers, etc if needed
    console.log('🐋 Whale Wallet initialized');
});

// Export for use in other scripts
window.WhaleWallet = {
    API,
    Toast,
    Modal,
    Format,
    Loading,
    ChartColors,
    ChainMeta,
    Validate,
    copyToClipboard,
    toggleSidebar
};
