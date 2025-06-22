// gRPC Web Client
class GrpcWebClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.connected = false;
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            if (response.ok) {
                this.connected = true;
                return true;
            }
        } catch (error) {
            console.error('Connection check failed:', error);
            this.connected = false;
        }
        return false;
    }

    async sendHelloRequest(name) {
        try {
            const response = await fetch(`${this.baseUrl}/api/hello`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Hello request failed:', error);
            throw error;
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    }
}

// UI Controller
class UIController {
    constructor() {
        this.client = new GrpcWebClient();
        this.initializeUI();
        this.checkConnectionStatus();
    }

    initializeUI() {
        // Get DOM elements
        this.nameInput = document.getElementById('nameInput');
        this.sendButton = document.getElementById('sendButton');
        this.healthButton = document.getElementById('healthButton');
        this.clearButton = document.getElementById('clearButton');
        this.responseContent = document.getElementById('responseContent');
        this.status = document.getElementById('status');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectionText = document.getElementById('connectionText');

        // Add event listeners
        this.nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendHelloRequest();
            }
        });
    }

    async checkConnectionStatus() {
        const isConnected = await this.client.checkConnection();
        this.updateConnectionStatus(isConnected);
        
        // Retry connection every 5 seconds if not connected
        if (!isConnected) {
            setTimeout(() => this.checkConnectionStatus(), 5000);
        }
    }

    updateConnectionStatus(connected) {
        this.client.connected = connected;
        
        if (connected) {
            this.connectionStatus.className = 'connection-status connected';
            this.connectionText.textContent = 'Connected to gRPC server';
            this.sendButton.disabled = false;
            this.healthButton.disabled = false;
        } else {
            this.connectionStatus.className = 'connection-status disconnected';
            this.connectionText.textContent = 'Disconnected from gRPC server';
            this.sendButton.disabled = true;
            this.healthButton.disabled = true;
        }
    }

    showStatus(message, type = 'info') {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
        this.status.style.display = 'block';
        
        // Hide status after 5 seconds
        setTimeout(() => {
            this.status.style.display = 'none';
        }, 5000);
    }

    updateResponse(content) {
        this.responseContent.textContent = content;
    }

    async sendHelloRequest() {
        if (!this.client.connected) {
            this.showStatus('Not connected to server', 'error');
            return;
        }

        const name = this.nameInput.value.trim() || 'World';
        
        try {
            this.sendButton.disabled = true;
            this.showStatus('Sending request...', 'info');
            
            const response = await this.client.sendHelloRequest(name);
            
            const responseText = `✅ Request successful!
📤 Sent: HelloRequest(name="${name}")
📥 Received: HelloReply(message="${response.message}")
⏰ Timestamp: ${new Date().toISOString()}`;
            
            this.updateResponse(responseText);
            this.showStatus('Request completed successfully!', 'success');
            
        } catch (error) {
            const errorText = `❌ Request failed!
📤 Sent: HelloRequest(name="${name}")
❌ Error: ${error.message}
⏰ Timestamp: ${new Date().toISOString()}`;
            
            this.updateResponse(errorText);
            this.showStatus('Request failed: ' + error.message, 'error');
        } finally {
            this.sendButton.disabled = false;
        }
    }

    async checkHealth() {
        if (!this.client.connected) {
            this.showStatus('Not connected to server', 'error');
            return;
        }

        try {
            this.healthButton.disabled = true;
            this.showStatus('Checking server health...', 'info');
            
            const response = await this.client.checkHealth();
            
            const responseText = `🏥 Health Check Result:
📊 Status: ${response.status}
💬 Message: ${response.message}
⏰ Timestamp: ${new Date().toISOString()}`;
            
            this.updateResponse(responseText);
            this.showStatus('Health check completed!', 'success');
            
        } catch (error) {
            const errorText = `❌ Health check failed!
❌ Error: ${error.message}
⏰ Timestamp: ${new Date().toISOString()}`;
            
            this.updateResponse(errorText);
            this.showStatus('Health check failed: ' + error.message, 'error');
        } finally {
            this.healthButton.disabled = false;
        }
    }

    clearResponse() {
        this.updateResponse('No response yet. Click a button to make a request.');
        this.status.style.display = 'none';
    }
}

// Global functions for button clicks
let uiController;

function sendHelloRequest() {
    if (!uiController) {
        uiController = new UIController();
    }
    uiController.sendHelloRequest();
}

function checkHealth() {
    if (!uiController) {
        uiController = new UIController();
    }
    uiController.checkHealth();
}

function clearResponse() {
    if (!uiController) {
        uiController = new UIController();
    }
    uiController.clearResponse();
}

// Initialize UI when page loads
document.addEventListener('DOMContentLoaded', () => {
    uiController = new UIController();
    
    // Check connection status periodically
    setInterval(() => {
        if (uiController) {
            uiController.checkConnectionStatus();
        }
    }, 10000); // Check every 10 seconds
}); 