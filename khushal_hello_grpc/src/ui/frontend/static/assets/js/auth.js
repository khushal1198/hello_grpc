// Authentication JavaScript

class AuthController {
    constructor() {
        this.initializeAuth();
        this.setupEventListeners();
    }

    initializeAuth() {
        // Check if user is already logged in
        const sessionToken = localStorage.getItem('sessionToken');
        if (sessionToken) {
            // Redirect to dashboard if already logged in
            window.location.href = '/static/dashboard.html';
        }
    }

    setupEventListeners() {
        // Form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });

        // Enter key handling
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const activeForm = document.querySelector('.auth-form.active form');
                if (activeForm) {
                    activeForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }
        });
    }

    async handleLogin() {
        const form = document.getElementById('loginForm');
        const formData = new FormData(form);
        const identifier = formData.get('identifier').trim();
        const password = formData.get('password');

        // Validation
        if (!identifier || !password) {
            this.showStatus('Please fill in all fields', 'error');
            return;
        }

        const button = form.querySelector('.auth-button');
        this.setLoading(button, true);

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    identifier: identifier,
                    password: password
                })
            });

            const data = await response.json();

            if (data.success) {
                // Store session token
                localStorage.setItem('sessionToken', data.session_token);
                localStorage.setItem('userData', JSON.stringify(data.user));

                this.showStatus('Login successful! Redirecting...', 'success');
                
                // Redirect to dashboard after short delay
                setTimeout(() => {
                    window.location.href = '/static/dashboard.html';
                }, 1500);
            } else {
                this.showStatus(data.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showStatus('Login failed. Please try again.', 'error');
        } finally {
            this.setLoading(button, false);
        }
    }

    async handleRegister() {
        const form = document.getElementById('registerForm');
        const formData = new FormData(form);
        const username = formData.get('username').trim();
        const email = formData.get('email').trim();
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');

        // Validation
        if (!username || !email || !password || !confirmPassword) {
            this.showStatus('Please fill in all fields', 'error');
            return;
        }

        if (password !== confirmPassword) {
            this.showStatus('Passwords do not match', 'error');
            return;
        }

        if (password.length < 6) {
            this.showStatus('Password must be at least 6 characters long', 'error');
            return;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showStatus('Please enter a valid email address', 'error');
            return;
        }

        const button = form.querySelector('.auth-button');
        this.setLoading(button, true);

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showStatus('Registration successful! Please login.', 'success');
                
                // Switch to login tab after short delay
                setTimeout(() => {
                    showTab('login');
                    // Pre-fill the login form
                    document.getElementById('loginIdentifier').value = username;
                }, 1500);
            } else {
                this.showStatus(data.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showStatus('Registration failed. Please try again.', 'error');
        } finally {
            this.setLoading(button, false);
        }
    }

    showStatus(message, type = 'info') {
        const status = document.getElementById('authStatus');
        status.textContent = message;
        status.className = `status ${type}`;
        status.style.display = 'block';
        
        // Auto-hide after 5 seconds for non-success messages
        if (type !== 'success') {
            setTimeout(() => {
                status.style.display = 'none';
            }, 5000);
        }
    }

    setLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.classList.add('loading');
            button.dataset.originalText = button.textContent;
            button.textContent = 'Processing...';
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            button.textContent = button.dataset.originalText || button.textContent;
        }
    }
}

// Tab switching functionality
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    
    // Hide all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    
    // Activate corresponding button
    event.target.classList.add('active');
    
    // Clear status messages
    document.getElementById('authStatus').style.display = 'none';
    
    // Focus on first input
    const activeForm = document.querySelector('.auth-form.active');
    const firstInput = activeForm.querySelector('input[type="text"], input[type="email"]');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

// Utility functions
function clearForm(formId) {
    const form = document.getElementById(formId);
    form.reset();
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
}

// Initialize authentication controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AuthController();
    
    // Focus on first input of active tab
    const activeForm = document.querySelector('.auth-form.active');
    const firstInput = activeForm.querySelector('input[type="text"], input[type="email"]');
    if (firstInput) {
        firstInput.focus();
    }
});

// Export for potential use in other scripts
window.AuthController = AuthController; 