// Dashboard JavaScript

class DashboardController {
    constructor() {
        this.sessionToken = null;
        this.userData = null;
        this.initializeDashboard();
    }

    initializeDashboard() {
        // Check authentication
        this.sessionToken = localStorage.getItem('sessionToken');
        const userDataString = localStorage.getItem('userData');

        if (!this.sessionToken || !userDataString) {
            // Redirect to login if not authenticated
            window.location.href = '/static/login.html';
            return;
        }

        try {
            this.userData = JSON.parse(userDataString);
            this.loadUserProfile();
        } catch (error) {
            console.error('Error parsing user data:', error);
            this.logout();
        }
    }

    loadUserProfile() {
        if (!this.userData) return;

        // Update header username
        const usernameElement = document.getElementById('username');
        if (usernameElement) {
            usernameElement.textContent = this.userData.username;
        }

        // Update profile details
        this.updateProfileField('profileUsername', this.userData.username);
        this.updateProfileField('profileEmail', this.userData.email);
        this.updateProfileField('profileUserId', this.userData.user_id);
        
        // Format and display creation date
        if (this.userData.created_at) {
            const createdDate = new Date(this.userData.created_at);
            const formattedDate = createdDate.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            this.updateProfileField('profileCreatedAt', formattedDate);
        }

        // Update name input with username as default
        const nameInput = document.getElementById('nameInput');
        if (nameInput && nameInput.value === 'World') {
            nameInput.value = this.userData.username;
        }
    }

    updateProfileField(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value || 'Not available';
        }
    }

    async refreshProfile() {
        try {
            const response = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.sessionToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.userData = data.user;
                    localStorage.setItem('userData', JSON.stringify(this.userData));
                    this.loadUserProfile();
                    this.showStatus('Profile refreshed', 'success');
                } else {
                    throw new Error(data.message || 'Failed to refresh profile');
                }
            } else {
                throw new Error('Failed to refresh profile');
            }
        } catch (error) {
            console.error('Profile refresh error:', error);
            this.showStatus('Failed to refresh profile', 'error');
            
            // If unauthorized, logout
            if (error.message.includes('401') || error.message.includes('unauthorized')) {
                this.logout();
            }
        }
    }

    logout() {
        // Clear local storage
        localStorage.removeItem('sessionToken');
        localStorage.removeItem('userData');

        // Call logout API (optional, fire and forget)
        if (this.sessionToken) {
            fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.sessionToken}`,
                    'Content-Type': 'application/json'
                }
            }).catch(error => {
                console.log('Logout API call failed:', error);
            });
        }

        // Redirect to login
        window.location.href = '/static/login.html';
    }

    showStatus(message, type = 'info') {
        // Create status element if it doesn't exist
        let status = document.querySelector('.dashboard-status');
        if (!status) {
            status = document.createElement('div');
            status.className = 'dashboard-status';
            document.body.appendChild(status);
        }

        status.textContent = message;
        status.className = `dashboard-status ${type}`;
        status.style.display = 'block';

        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (status.parentNode) {
                status.parentNode.removeChild(status);
            }
        }, 4000);
    }

    // Method to check if user is authenticated (for use by other scripts)
    isAuthenticated() {
        return !!(this.sessionToken && this.userData);
    }

    // Method to get current user data
    getCurrentUser() {
        return this.userData;
    }
}

// Enhanced Hello Service functions with authentication context
function sendHelloRequest() {
    if (window.uiController) {
        // Use the authenticated user's name if available
        const nameInput = document.getElementById('nameInput');
        if (nameInput && window.dashboardController && window.dashboardController.userData) {
            if (nameInput.value === 'World') {
                nameInput.value = window.dashboardController.userData.username;
            }
        }
        window.uiController.sendHelloRequest();
    }
}

function checkHealth() {
    if (window.uiController) {
        window.uiController.checkHealth();
    }
}

function clearResponse() {
    if (window.uiController) {
        window.uiController.clearResponse();
    }
}

function logout() {
    if (window.dashboardController) {
        window.dashboardController.logout();
    }
}

function refreshProfile() {
    if (window.dashboardController) {
        window.dashboardController.refreshProfile();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initialize dashboard controller
    window.dashboardController = new DashboardController();

    // Initialize the existing UI controller for Hello service
    if (window.UIController) {
        window.uiController = new UIController();
    }

    // Add refresh profile button functionality if it exists
    const refreshButton = document.getElementById('refreshProfileButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshProfile);
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+R or Cmd+R for refresh profile
        if ((e.ctrlKey || e.metaKey) && e.key === 'r' && e.shiftKey) {
            e.preventDefault();
            refreshProfile();
        }
        
        // Ctrl+L or Cmd+L for logout
        if ((e.ctrlKey || e.metaKey) && e.key === 'l' && e.shiftKey) {
            e.preventDefault();
            logout();
        }
    });
});

// Export for potential use in other scripts
window.DashboardController = DashboardController; 