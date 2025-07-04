// Home page authentication handling

class HomeController {
    constructor() {
        this.checkAuthenticationStatus();
    }

    checkAuthenticationStatus() {
        const sessionToken = localStorage.getItem('sessionToken');
        const userDataString = localStorage.getItem('userData');

        const authStatus = document.getElementById('authStatus');
        const authLink = document.getElementById('authLink');

        if (sessionToken && userDataString) {
            try {
                const userData = JSON.parse(userDataString);
                
                // User is logged in
                authStatus.innerHTML = `<span class="user-welcome">Welcome, ${userData.username}!</span>`;
                authLink.textContent = 'Dashboard';
                authLink.href = '/static/dashboard.html';
                authLink.className = 'dashboard-link';

                // Pre-fill name input with username
                const nameInput = document.getElementById('nameInput');
                if (nameInput && nameInput.value === 'World') {
                    nameInput.value = userData.username;
                }

            } catch (error) {
                console.error('Error parsing user data:', error);
                this.clearAuthenticationState();
            }
        } else {
            // User is not logged in
            authStatus.textContent = 'Not logged in';
            authLink.textContent = 'Login / Register';
            authLink.href = '/static/login.html';
            authLink.className = 'auth-link';
        }
    }

    clearAuthenticationState() {
        localStorage.removeItem('sessionToken');
        localStorage.removeItem('userData');
        this.checkAuthenticationStatus();
    }

    logout() {
        this.clearAuthenticationState();
        // Optionally show a message
        const status = document.getElementById('status');
        if (status) {
            status.textContent = 'Logged out successfully';
            status.className = 'status success';
            status.style.display = 'block';
            
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }
    }
}

// Initialize home controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.homeController = new HomeController();
    
    // Check for logout parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('logout') === 'true') {
        window.homeController.logout();
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// Export for potential use in other scripts
window.HomeController = HomeController; 