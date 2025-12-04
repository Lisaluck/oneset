class DashboardManager {
    constructor() {
        this.apiBase = 'http://127.0.0.1:8000/api';  // Tumhara API base URL
        this.currentView = 'dashboard';
        this.init();
    }

    async init() {
        await this.checkAuth();
        this.initEventListeners();
        this.loadDashboardData();
    }

    async checkAuth() {
        try {
            const response = await fetch(`${this.apiBase}/users/current_user/`, {
                credentials: 'include'
            });

            if (!response.ok) {
                window.location.href = '/login/';
                return;
            }
        } catch (error) {
            window.location.href = '/login/';
        }
    }

    initEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                this.handleNavigation(e.target.closest('.nav-item').dataset.view);
            });
        });

        // Add item button
        document.querySelectorAll('.add-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.showAddItemModal();
            });
        });

        // Modal handlers
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                this.hideAddItemModal();
            });
        });

        document.getElementById('addItemForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddItem();
        });

        // Dynamic form fields based on item type
        document.getElementById('itemType')?.addEventListener('change', (e) => {
            this.handleItemTypeChange(e.target.value);
        });

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.handleLogout();
        });

        // Search
        document.querySelector('.search-input')?.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        // Close modal when clicking outside
        document.getElementById('addItemModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'addItemModal') {
                this.hideAddItemModal();
            }
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${this.apiBase}/content/dashboard_stats/`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
                this.updateRecentItems(data.recent_items);
            } else {
                this.showMessage('Error loading dashboard data', 'error');
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showMessage('Network error. Please check your connection.', 'error');
        }
    }

    updateDashboardStats(data) {
        document.getElementById('totalItems').textContent = data.total_items || 0;
        document.getElementById('completedTasks').textContent = data.completed_tasks || 0;
        document.getElementById('starredItems').textContent = data.starred_items || 0;
        document.getElementById('pendingTasks').textContent = data.pending_tasks || 0;
    }

    updateRecentItems(items) {
        const container = document.getElementById('recentItems');
        container.innerHTML = '';

        if (!items || items.length === 0) {
            container.innerHTML = '<div class="no-items">No recent items. Start by adding some content!</div>';
            return;
        }

        items.forEach(item => {
            const itemElement = this.createItemElement(item);
            container.appendChild(itemElement);
        });
    }

    createItemElement(item) {
        const div = document.createElement('div');
        div.className = 'recent-item';
        div.innerHTML = `
            <div class="item-icon">
                <i class="fas ${this.getItemIcon(item.content_type)}"></i>
            </div>
            <div class="item-content">
                <h4>${this.escapeHtml(item.title)}</h4>
                <p>${this.formatDate(item.created_at)} • ${item.content_type}</p>
            </div>
            <div class="item-actions">
                <button class="star-btn ${item.is_starred ? 'starred' : ''}" data-id="${item.id}">
                    <i class="fas fa-star"></i>
                </button>
            </div>
        `;

        // Add star functionality
        div.querySelector('.star-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleStar(item.id);
        });

        return div;
    }

    getItemIcon(type) {
        const icons = {
            'note': 'fa-sticky-note',
            'task': 'fa-check-circle',
            'link': 'fa-link',
            'code': 'fa-code',
            'document': 'fa-file-pdf'
        };
        return icons[type] || 'fa-file';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'Today';
        } else if (diffDays === 2) {
            return 'Yesterday';
        } else if (diffDays <= 7) {
            return `${diffDays - 1} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    async toggleStar(itemId) {
        try {
            const response = await fetch(`${this.apiBase}/content/${itemId}/toggle_star/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (response.ok) {
                this.loadDashboardData();
                this.showMessage('Item updated!', 'success');
            }
        } catch (error) {
            console.error('Error toggling star:', error);
            this.showMessage('Error updating item', 'error');
        }
    }

    async handleAddItem() {
        const form = document.getElementById('addItemForm');
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // Show loading state
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        submitBtn.disabled = true;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${this.apiBase}/content/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });

            if (response.ok) {
                this.hideAddItemModal();
                this.loadDashboardData();
                this.showMessage('Item added successfully!', 'success');
            } else {
                const error = await response.json();
                this.showMessage(error.error || 'Failed to add item', 'error');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        } catch (error) {
            this.showMessage('Network error. Please try again.', 'error');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    async handleLogout() {
        if (!confirm('Are you sure you want to logout?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/users/logout/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (response.ok) {
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error logging out:', error);
            this.showMessage('Error logging out', 'error');
        }
    }

    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showMessage(message, type) {
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
        `;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }

    // Navigation handler
    handleNavigation(view) {
        this.currentView = view;
        
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`).classList.add('active');

        // Show correct view
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        if (view === 'dashboard') {
            document.getElementById('dashboardView').classList.add('active');
            this.loadDashboardData();
        } else {
            document.getElementById('contentView').classList.add('active');
            this.loadContentView(view);
        }
    }

    async loadContentView(view) {
        const contentGrid = document.getElementById('contentGrid');
        const titleElement = document.getElementById('contentViewTitle');
        
        // Set title based on view
        const titles = {
            'all': 'All Items',
            'notes': 'Notes',
            'tasks': 'Tasks',
            'links': 'Links',
            'code': 'Code Snippets',
            'documents': 'Documents',
            'starred': 'Starred Items',
            'work': 'Work Items',
            'personal': 'Personal Items'
        };
        
        titleElement.textContent = titles[view] || 'Items';
        contentGrid.innerHTML = '<div class="no-items">Loading...</div>';

        try {
            let url = `${this.apiBase}/content/`;
            if (view !== 'all') {
                if (['notes', 'tasks', 'links', 'code', 'documents'].includes(view)) {
                    url += `?type=${view}`;
                } else if (view === 'starred') {
                    url += `?starred=true`;
                } else if (['work', 'personal'].includes(view)) {
                    url += `?category=${view}`;
                }
            }

            const response = await fetch(url, {
                credentials: 'include'
            });

            if (response.ok) {
                const items = await response.json();
                this.displayContentItems(items, contentGrid);
            }
        } catch (error) {
            console.error('Error loading content:', error);
            contentGrid.innerHTML = '<div class="no-items">Error loading items</div>';
        }
    }

    displayContentItems(items, container) {
        container.innerHTML = '';

        if (!items || items.length === 0) {
            container.innerHTML = '<div class="no-items">No items found. Add some content to get started!</div>';
            return;
        }

        items.forEach(item => {
            const itemElement = this.createContentItemElement(item);
            container.appendChild(itemElement);
        });
    }

    createContentItemElement(item) {
        const div = document.createElement('div');
        div.className = 'content-item';
        div.innerHTML = `
            <div class="content-item-header">
                <div class="content-item-title">${this.escapeHtml(item.title)}</div>
                <span class="content-item-type">${item.content_type}</span>
            </div>
            <div class="content-item-content">
                ${this.formatItemContent(item)}
            </div>
            <div class="content-item-meta">
                <span>${this.formatDate(item.created_at)}</span>
                <div class="content-item-actions">
                    <button class="star-btn ${item.is_starred ? 'starred' : ''}" data-id="${item.id}">
                        <i class="fas fa-star"></i>
                    </button>
                    ${item.content_type === 'task' ? `
                        <button class="complete-btn ${item.is_completed ? 'completed' : ''}" data-id="${item.id}">
                            <i class="fas ${item.is_completed ? 'fa-undo' : 'fa-check'}"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        // Add event listeners
        div.querySelector('.star-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleStar(item.id);
        });

        if (item.content_type === 'task') {
            div.querySelector('.complete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleComplete(item.id);
            });
        }

        return div;
    }

    formatItemContent(item) {
        switch (item.content_type) {
            case 'note':
                return item.content || '<em>No content</em>';
            case 'task':
                const priority = item.priority ? `<span class="priority ${item.priority}">${item.priority}</span>` : '';
                const dueDate = item.due_date ? `Due: ${this.formatDate(item.due_date)}` : '';
                return `${priority} ${dueDate}`.trim();
            case 'link':
                return item.url ? `<a href="${item.url}" target="_blank">${item.url}</a>` : '<em>No URL</em>';
            case 'code':
                return `<pre><code>${item.content || 'No code'}</code></pre>`;
            case 'document':
                return item.file ? `<em>Document: ${item.file}</em>` : '<em>No document</em>';
            default:
                return item.content || '<em>No content</em>';
        }
    }

    async toggleComplete(itemId) {
        try {
            const response = await fetch(`${this.apiBase}/content/${itemId}/toggle_complete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });

            if (response.ok) {
                this.loadContentView(this.currentView);
                this.showMessage('Task updated!', 'success');
            }
        } catch (error) {
            console.error('Error toggling complete:', error);
            this.showMessage('Error updating task', 'error');
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    showAddItemModal() {
        document.getElementById('addItemModal').style.display = 'flex';
        document.getElementById('addItemForm').reset();
        this.handleItemTypeChange('note');
    }

    hideAddItemModal() {
        document.getElementById('addItemModal').style.display = 'none';
    }

    handleItemTypeChange(type) {
        document.getElementById('taskFields').style.display = 'none';
        document.getElementById('linkFields').style.display = 'none';
        document.getElementById('codeFields').style.display = 'none';

        if (type === 'task') {
            document.getElementById('taskFields').style.display = 'block';
        } else if (type === 'link') {
            document.getElementById('linkFields').style.display = 'block';
        } else if (type === 'code') {
            document.getElementById('codeFields').style.display = 'block';
        }
    }

    handleSearch(query) {
        console.log('Search query:', query);
        // Implement search functionality
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
});