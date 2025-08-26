/**
 * Admin Users Management - Frontend JavaScript
 * Connected to Supabase backend via FastAPI
 */

class AdminUsers {
    constructor() {
        this.currentPage = 1;
        this.currentLimit = 10;
        this.currentSort = 'created_at';
        this.currentOrder = 'desc';
        this.currentQuery = '';
        this.currentRoleFilter = 'all';
        this.currentStatusFilter = 'all';
        this.searchTimeout = null;
        this.isEditing = false;
        
        // In-memory users array for optimistic updates
        this.users = [];
        this.totalUsers = 0;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadUsers();
        this.updateURLParams();
        
        // Auto-refresh every 30 seconds to keep data in sync
        setInterval(() => {
            this.loadUsers();
        }, 30000);
        
        // Check data age every 10 seconds
        setInterval(() => {
            this.checkDataAge();
        }, 10000);
    }

    bindEvents() {
        // Search with debounce
        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.currentQuery = e.target.value;
                this.currentPage = 1;
                this.updateURLParams();
                this.loadUsers();
            }, 300);
        });

        // Refresh buttons
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadUsers();
        });

        document.getElementById('forceRefreshBtn').addEventListener('click', () => {
            this.forceRefreshUsers();
        });

        document.getElementById('hardRefreshBtn').addEventListener('click', () => {
            console.log('🔄 Hard refresh - reloading page...');
            window.location.reload(true);
        });

        // Filters
        document.getElementById('roleFilter').addEventListener('change', (e) => {
            this.currentRoleFilter = e.target.value;
            this.currentPage = 1;
            this.updateURLParams();
            this.loadUsers();
        });

        document.getElementById('statusFilter').addEventListener('change', (e) => {
            this.currentStatusFilter = e.target.value;
            this.currentPage = 1;
            this.updateURLParams();
            this.loadUsers();
        });

        // Sort
        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.currentPage = 1;
            this.updateURLParams();
            this.loadUsers();
        });

        // Limit
        document.getElementById('limitSelect').addEventListener('change', (e) => {
            this.currentLimit = parseInt(e.target.value);
            this.currentPage = 1;
            this.updateURLParams();
            this.loadUsers();
        });

        // Pagination
        document.getElementById('prevBtn').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.updateURLParams();
                this.loadUsers();
            }
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            this.currentPage++;
            this.updateURLParams();
            this.loadUsers();
        });

        // Modal controls
        document.getElementById('addUserBtn').addEventListener('click', () => {
            this.openUserModal();
        });

        // Add user button in empty state
        const addUserBtnEmpty = document.getElementById('addUserBtnEmpty');
        if (addUserBtnEmpty) {
            addUserBtnEmpty.addEventListener('click', () => {
                this.openUserModal();
            });
        }

        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.closeUserModal();
        });

        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeUserModal();
        });

        document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
            this.closeDeleteModal();
        });

        // Form submissions
        document.getElementById('userForm').addEventListener('submit', (e) => {
            console.log('🎯 Form submit event triggered');
            this.handleUserFormSubmit(e);
        });

        document.getElementById('deleteForm').addEventListener('submit', (e) => {
            this.handleDeleteFormSubmit(e);
        });

        // Password validation
        document.getElementById('userPassword').addEventListener('input', () => {
            this.validatePasswords();
        });

        document.getElementById('userPasswordConfirm').addEventListener('input', () => {
            this.validatePasswords();
        });

        // Close modals on outside click
        document.getElementById('userModal').addEventListener('click', (e) => {
            if (e.target.id === 'userModal') {
                this.closeUserModal();
            }
        });

        document.getElementById('deleteModal').addEventListener('click', (e) => {
            if (e.target.id === 'deleteModal') {
                this.closeDeleteModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeUserModal();
                this.closeDeleteModal();
            }
        });
    }

    updateURLParams() {
        const params = new URLSearchParams();
        if (this.currentQuery) params.set('q', this.currentQuery);
        if (this.currentRoleFilter !== 'all') params.set('role', this.currentRoleFilter);
        if (this.currentStatusFilter !== 'all') params.set('status', this.currentStatusFilter);
        if (this.currentSort !== 'created_at') params.set('sort', this.currentSort);
        if (this.currentOrder !== 'desc') params.set('order', this.currentOrder);
        if (this.currentPage > 1) params.set('page', this.currentPage);
        if (this.currentLimit !== 10) params.set('limit', this.currentLimit);
        
        const newURL = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
        window.history.replaceState({}, '', newURL);
    }

    async loadUsers() {
        try {
            this.showLoading();
            
            const params = new URLSearchParams({
                q: this.currentQuery,
                page: this.currentPage,
                limit: this.currentLimit,
                sort: this.currentSort,
                order: this.currentOrder,
                role: this.currentRoleFilter,
                status: this.currentStatusFilter
            });

            console.log('🔄 Loading users with params:', params.toString());
            const response = await fetch(`/api/users?${params}`, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            
            console.log('📡 Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📊 Received data:', data);

            // Store users in memory for optimistic updates
            this.users = data.items || [];
            this.totalUsers = data.total || 0;
            
            this.renderUsers(data);
            this.updatePagination(data);
            this.updateStatistics(data);
            
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError(`Failed to load users: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async forceRefreshUsers() {
        console.log('🔄 Force refreshing users...');
        this.currentPage = 1;
        
        // Clear any cached data
        this.currentQuery = '';
        this.currentRoleFilter = 'all';
        this.currentStatusFilter = 'all';
        
        // Update URL params
        this.updateURLParams();
        
        // Force a completely fresh load
        await this.loadUsers();
        
        console.log('🔄 Force refresh completed');
    }

    updateLastRefreshTime() {
        const lastRefreshElement = document.getElementById('lastRefreshTime');
        const dataAgeElement = document.getElementById('dataAge');
        
        if (lastRefreshElement) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            lastRefreshElement.textContent = `Last refreshed: ${timeString}`;
            
            // Store the refresh timestamp
            this.lastRefreshTimestamp = now.getTime();
        }
        
        // Hide stale data warning
        if (dataAgeElement) {
            dataAgeElement.classList.add('hidden');
        }
    }

    checkDataAge() {
        const dataAgeElement = document.getElementById('dataAge');
        if (!dataAgeElement || !this.lastRefreshTimestamp) return;
        
        const now = Date.now();
        const ageInMinutes = (now - this.lastRefreshTimestamp) / (1000 * 60);
        
        if (ageInMinutes > 1) {
            dataAgeElement.classList.remove('hidden');
        }
    }

    showLoading() {
        document.getElementById('loadingState').classList.remove('hidden');
        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('usersTableBody').innerHTML = '';
        
        // Show loading indicator on refresh buttons
        const refreshBtn = document.getElementById('refreshBtn');
        const forceRefreshBtn = document.getElementById('forceRefreshBtn');
        if (refreshBtn) refreshBtn.disabled = true;
        if (forceRefreshBtn) forceRefreshBtn.disabled = true;
    }

    hideLoading() {
        document.getElementById('loadingState').classList.add('hidden');
        
        // Re-enable refresh buttons
        const refreshBtn = document.getElementById('refreshBtn');
        const forceRefreshBtn = document.getElementById('forceRefreshBtn');
        if (refreshBtn) refreshBtn.disabled = false;
        if (forceRefreshBtn) forceRefreshBtn.disabled = false;
        
        // Update last refresh time
        this.updateLastRefreshTime();
    }

    renderUsers(data) {
        const tbody = document.getElementById('usersTableBody');
        const emptyState = document.getElementById('emptyState');

        const users = data.items || [];
        
        console.log('🎨 Rendering users:', users);
        console.log('🎨 Users count:', users.length);

        if (!users || users.length === 0) {
            console.log('❌ No users to render, showing empty state');
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        
        const userRows = users.map(user => `
            <tr class="hover:bg-slate-800/30 border-b border-white/5 transition-all duration-200" data-row-id="${user.id}">
                <td class="p-4 text-white">
                    <div class="font-medium">${this.escapeHtml(user.name)}</div>
                </td>
                <td class="p-4 text-white/80">
                    ${this.escapeHtml(user.email)}
                </td>
                <td class="p-4">
                    <span class="role-${user.role}">
                        ${this.getRoleDisplayName(user.role)}
                    </span>
                </td>
                <td class="p-4">
                    <span class="status-${user.status}">
                        ${this.getStatusDisplayName(user.status)}
                    </span>
                </td>
                <td class="p-4 text-white/80" title="${this.escapeHtml(user.phone || '')}">
                    ${this.truncateText(user.phone || '-', 15)}
                </td>
                <td class="p-4 text-white/80" title="${this.escapeHtml(user.city || '')}">
                    ${this.truncateText(user.city || '-', 15)}
                </td>
                <td class="p-4 text-white/60 text-sm">
                    ${user.joining_date ? this.formatDate(user.joining_date) : '-'}
                </td>
                <td class="p-4 text-white/60 text-sm">
                    ${user.last_login ? this.formatDateTime(user.last_login) : 'Never'}
                </td>
                <td class="p-4">
                    <div class="flex items-center gap-2">
                        <button onclick="adminUsers.editUser('${user.id}')" 
                                class="inline-flex items-center gap-1 px-3 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 rounded-lg text-sm transition-all duration-200 hover:scale-105">
                            <span>✏️</span>
                            <span>Edit</span>
                        </button>
                        <button onclick="adminUsers.confirmDeleteUser('${user.id}', '${this.escapeHtml(user.name)}')" 
                                class="inline-flex items-center gap-1 px-3 py-1 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded-lg text-sm transition-all duration-200 hover:scale-105"
                                data-user-id="${user.id}">
                            <span>🗑️</span>
                            <span>Delete</span>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        console.log('🎨 Generated HTML rows:', userRows.length);
        tbody.innerHTML = userRows;
    }

    updatePagination(data) {
        const resultsInfo = document.getElementById('resultsInfo');
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        const start = ((data.page - 1) * data.limit) + 1;
        const end = Math.min(data.page * data.limit, data.total);
        
        resultsInfo.textContent = `${start}-${end} of ${data.total}`;
        pageInfo.textContent = `Page ${data.page} of ${data.pages}`;
        prevBtn.disabled = data.page <= 1;
        nextBtn.disabled = data.page >= data.pages;
    }

    updateStatistics(data) {
        const totalUsers = document.getElementById('totalUsers');
        const activeUsers = document.getElementById('activeUsers');
        const adminUsers = document.getElementById('adminUsers');
        const recentLogins = document.getElementById('recentLogins');

        const users = data.items || [];
        if (!users) return;

        // Calculate statistics
        const total = data.total || 0;
        const active = users.filter(user => user.status === 'active').length;
        const admins = users.filter(user => ['owner', 'admin'].includes(user.role)).length;
        
        // Calculate recent logins (last 7 days)
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        const recent = users.filter(user => 
            user.last_login && new Date(user.last_login) > sevenDaysAgo
        ).length;

        // Update display
        totalUsers.textContent = total;
        activeUsers.textContent = active;
        adminUsers.textContent = admins;
        recentLogins.textContent = recent;
    }

    openUserModal(user = null) {
        this.isEditing = !!user;
        const modal = document.getElementById('userModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('userForm');
        const passwordNote = document.getElementById('passwordNote');
        const passwordRequired = document.getElementById('passwordRequired');
        const confirmRequired = document.getElementById('confirmRequired');
        const modalIcon = document.getElementById('modalIcon');

        // Reset form
        form.reset();
        this.clearErrors();

        if (this.isEditing) {
            title.textContent = 'Edit User';
            modalIcon.textContent = '✏️';
            passwordNote.classList.remove('hidden');
            passwordRequired.classList.add('hidden');
            confirmRequired.classList.add('hidden');
            this.fillUserForm(user);
        } else {
            title.textContent = 'Add User';
            modalIcon.textContent = '➕';
            passwordNote.classList.add('hidden');
            passwordRequired.classList.remove('hidden');
            confirmRequired.classList.remove('hidden');
        }

        modal.classList.remove('hidden');
        
        // Focus first input
        setTimeout(() => {
            document.getElementById('userName').focus();
        }, 100);
    }

    closeUserModal() {
        document.getElementById('userModal').classList.add('hidden');
        this.clearErrors();
    }

    fillUserForm(user) {
        document.getElementById('userId').value = user.id;
        document.getElementById('userName').value = user.name;
        document.getElementById('userEmail').value = user.email;
        document.getElementById('userRole').value = user.role;
        document.getElementById('userStatus').value = user.status;
        document.getElementById('userPhone').value = user.phone || '';
        document.getElementById('userCity').value = user.city || '';
        document.getElementById('userState').value = user.state || '';
        document.getElementById('userJoiningDate').value = user.joining_date || '';
    }

    async editUser(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            if (data.ok) {
                this.openUserModal(data.data);
            } else {
                this.showError('Failed to load user details');
            }
        } catch (error) {
            console.error('Error loading user:', error);
            this.showError(`Failed to load user details: ${error.message}`);
        }
    }

    async handleUserFormSubmit(e) {
        e.preventDefault();
        console.log('📝 Form submission started');
        
        if (!this.validateForm()) {
            console.log('❌ Form validation failed');
            return;
        }
        
        console.log('✅ Form validation passed');

        const formData = new FormData(e.target);
        console.log('📋 Form data collected:');
        for (let [key, value] of formData.entries()) {
            console.log(`   ${key}: ${value}`);
        }
        
        const saveBtn = document.getElementById('saveBtn');
        
        try {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="animate-spin">⏳</span> Saving...';

            let url, method;
            if (this.isEditing) {
                const userId = document.getElementById('userId').value;
                url = `/api/users/${userId}`;
                method = 'PATCH';
            } else {
                url = '/api/users';
                method = 'POST';
            }

            console.log('💾 Attempting to save user:', method, url);
            console.log('💾 Form data contents:');
            for (let [key, value] of formData.entries()) {
                console.log(`   ${key}: ${value}`);
            }
            const response = await fetch(url, {
                method: method,
                body: formData
            });
            console.log('💾 Save response status:', response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();
                if (data.ok) {
                    this.showSuccess(this.isEditing ? 'User updated successfully' : 'User created successfully');
                    this.closeUserModal();
                    
                    if (this.isEditing) {
                        // Update the user in our local array
                        const userId = document.getElementById('userId').value;
                        const updatedUser = await this.getUserForUpdate(userId);
                        if (updatedUser) {
                            const index = this.users.findIndex(u => u.id === userId);
                            if (index !== -1) {
                                this.users[index] = { ...this.users[index], ...updatedUser };
                            }
                        }
                    } else {
                        // Add new user to local array (will be replaced by reload)
                        const newUserId = data.id;
                        const newUser = await this.getUserForUpdate(newUserId);
                        if (newUser) {
                            this.users.unshift(newUser);
                            this.totalUsers++;
                        }
                    }
                    
                    // Reload users to get fresh data
                    this.loadUsers();
                } else {
                    this.showError(data.error || 'Failed to save user');
                    if (data.error && data.error.includes('Email already exists')) {
                        this.showFieldError('emailError', 'Email already exists');
                    }
                }
            } else {
                // Handle error responses
                let errorMessage = 'Failed to save user';
                try {
                    const data = await response.json();
                    errorMessage = data.error || data.detail || errorMessage;
                    if (data.error && data.error.includes('Email already exists')) {
                        this.showFieldError('emailError', 'Email already exists');
                    }
                } catch (e) {
                    // Response might not be JSON
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('Error saving user:', error);
            this.showError(`Failed to save user: ${error.message}`);
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<span class="group-hover:scale-110 transition-transform duration-200">💾</span><span>Save User</span>';
        }
    }

    async getUserForUpdate(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            if (response.ok) {
                const data = await response.json();
                return data.data;
            }
        } catch (error) {
            console.error('Error getting updated user:', error);
        }
        return null;
    }

    confirmDeleteUser(userId, userName) {
        document.getElementById('deleteUserId').value = userId;
        document.getElementById('deleteUserName').textContent = userName;
        document.getElementById('deleteModal').classList.remove('hidden');
    }

    closeDeleteModal() {
        document.getElementById('deleteModal').classList.add('hidden');
    }

    async handleDeleteFormSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const userId = formData.get('user_id');
        
        // Optimistic UI update - immediately remove the row
        const row = document.querySelector(`[data-row-id="${userId}"]`);
        const deleteBtn = document.querySelector(`[data-user-id="${userId}"]`);
        
        if (row && deleteBtn) {
            // Disable delete button and show "Deleting..." state
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<span class="animate-spin">⏳</span> Deleting...';
            deleteBtn.classList.add('opacity-50', 'cursor-not-allowed');
            
            // Remove row from DOM immediately
            row.remove();
            
            // Update total count optimistically
            this.totalUsers = Math.max(0, this.totalUsers - 1);
            this.updateStatistics({ total: this.totalUsers, items: this.users.filter(u => u.id !== userId) });
            
            // Update pagination if current page becomes empty
            this.handlePageEmptyAfterDelete();
        }
        
        try {
            console.log('🗑️ Attempting to delete user:', userId);
            console.log('🗑️ Form data contents:');
            for (let [key, value] of formData.entries()) {
                console.log(`   ${key}: ${value}`);
            }
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE',
                body: formData
            });
            console.log('🗑️ Delete response status:', response.status, response.statusText);

            if (response.ok || response.status === 204) {
                // Success - remove from in-memory array
                this.users = this.users.filter(u => u.id !== userId);
                this.showSuccess('User deleted successfully');
                this.closeDeleteModal();
                
                // Background reconciliation
                setTimeout(() => {
                    this.loadUsers();
                }, 1000);
            } else if (response.status === 404) {
                // User already deleted - treat as success
                this.users = this.users.filter(u => u.id !== userId);
                this.showSuccess('User already deleted');
                this.closeDeleteModal();
                
                // Background reconciliation
                setTimeout(() => {
                    this.loadUsers();
                }, 1000);
            } else {
                // Other errors - restore the row
                let errorMessage = 'Failed to delete user';
                try {
                    const data = await response.json();
                    errorMessage = data.error || data.detail || errorMessage;
                } catch (e) {
                    // Response might not be JSON
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                this.showError(errorMessage);
                if (row && deleteBtn) {
                    this.restoreDeletedRow(row, deleteBtn, userId);
                }
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showError(`Failed to delete user: ${error.message}`);
            
            // Restore the row on error
            if (row && deleteBtn) {
                this.restoreDeletedRow(row, deleteBtn, userId);
            }
        }
    }

    validateForm() {
        let isValid = true;
        this.clearErrors();

        // Validate required fields
        const name = document.getElementById('userName').value.trim();
        const email = document.getElementById('userEmail').value.trim();
        
        if (!name) {
            this.showFieldError('name', 'Name is required');
            isValid = false;
        }

        if (!email) {
            this.showFieldError('email', 'Email is required');
            isValid = false;
        } else if (!this.isValidEmail(email)) {
            this.showFieldError('email', 'Please enter a valid email address');
            isValid = false;
        }

        // Validate passwords
        if (!this.validatePasswords()) {
            isValid = false;
        }

        return isValid;
    }

    validatePasswords() {
        const password = document.getElementById('userPassword').value;
        const confirmPassword = document.getElementById('userPasswordConfirm').value;
        const passwordError = document.getElementById('passwordError');

        // Clear previous errors
        passwordError.classList.add('hidden');
        passwordError.textContent = '';

        // For new users, password is required
        if (!this.isEditing && !password) {
            this.showFieldError('passwordError', 'Password is required');
            return false;
        }

        // If password is provided, validate it
        if (password) {
            if (password.length < 6) {
                this.showFieldError('passwordError', 'Password must be at least 6 characters');
                return false;
            }

            if (password !== confirmPassword) {
                this.showFieldError('passwordError', 'Passwords do not match');
                return false;
            }
        }

        return true;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    clearErrors() {
        document.getElementById('emailError').classList.add('hidden');
        document.getElementById('passwordError').classList.add('hidden');
    }

    showFieldError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        }
    }

    getRoleDisplayName(role) {
        const roleNames = {
            'owner': '👑 Owner',
            'admin': '⚡ Admin',
            'manager': '👔 Manager',
            'employee': '👷 Employee',
            'packer': '📦 Packer'
        };
        return roleNames[role] || role;
    }

    getStatusDisplayName(status) {
        const statusNames = {
            'active': '🟢 Active',
            'inactive': '⚪ Inactive',
            'suspended': '🔴 Suspended'
        };
        return statusNames[status] || status;
    }

    formatDate(dateString) {
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return dateString;
        }
    }

    formatDateTime(dateString) {
        try {
            return new Date(dateString).toLocaleString();
        } catch {
            return dateString;
        }
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 transform translate-x-full transition-transform duration-300`;
        toast.innerHTML = `
            <span class="text-lg">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span>${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 text-white hover:text-gray-200 transition-colors duration-200">&times;</button>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    // Handle page becoming empty after deletion
    handlePageEmptyAfterDelete() {
        const tbody = document.getElementById('usersTableBody');
        const visibleRows = tbody.querySelectorAll('tr[data-row-id]');
        
        if (visibleRows.length === 0 && this.currentPage > 1) {
            // Current page is empty and we're not on page 1
            console.log('📄 Page became empty after deletion, navigating to previous page');
            this.currentPage--;
            
            // Reload users on the previous page
            setTimeout(() => {
                this.loadUsers();
            }, 500);
        }
    }

    // Restore a deleted row (for error cases)
    restoreDeletedRow(row, deleteBtn, userId) {
        // Re-enable delete button
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<span>🗑️</span><span>Delete</span>';
        deleteBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        // Restore row to DOM
        const tbody = document.getElementById('usersTableBody');
        tbody.appendChild(row);
        
        // Restore total count
        this.totalUsers++;
        this.updateStatistics({ total: this.totalUsers, items: this.users });
        
        console.log('🔄 Restored deleted row for user:', userId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminUsers = new AdminUsers();
});
