// UI Interactions & Utilities

const UI = {
    // Show alert notification
    alert(message, type = 'info', duration = 5000) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = `
            <span>${this.getIcon(type)}</span>
            <span>${message}</span>
        `;
        
        // Insert at top of page
        const main = document.querySelector('main') || document.body;
        main.insertBefore(alertEl, main.firstChild);
        
        // Auto-remove after duration
        setTimeout(() => {
            alertEl.remove();
        }, duration);
    },
    
    // Get icon for alert type
    getIcon(type) {
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return icons[type] || '💬';
    },
    
    // Show loading spinner
    showLoading(text = 'Loading...') {
        const loader = document.createElement('div');
        loader.id = 'loader';
        loader.innerHTML = `
            <div class="spinner"></div>
            <p>${text}</p>
        `;
        document.body.appendChild(loader);
    },
    
    // Hide loading spinner
    hideLoading() {
        const loader = document.getElementById('loader');
        if (loader) loader.remove();
    },
    
    // Toggle button state
    toggleButton(buttonId, disabled = true) {
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.disabled = disabled;
            btn.style.opacity = disabled ? '0.5' : '1';
        }
    },
    
    // Clear form
    clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) form.reset();
    },
    
    // Get form data
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return null;
        
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    },
    
    // Validate email
    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    // Validate password strength
    validatePassword(password) {
        return {
            isValid: password.length >= 6,
            message: password.length < 6 ? 'Password must be at least 6 characters' : 'Password is strong'
        };
    },
    
    // Format timestamp
    formatTime(date) {
        if (!date) return '';
        const d = new Date(date);
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    },
    
    // Format date
    formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return d.toLocaleDateString('en-US', options);
    },
    
    // Escape HTML
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    },
    
    // Confirm dialog
    confirm(message) {
        return confirm(message);
    },
    
    // Redirect
    redirect(url) {
        window.location.href = url;
    }
};

// Export
window.UI = UI;