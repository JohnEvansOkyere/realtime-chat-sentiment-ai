// frontend/app.js
const API_URL = 'http://localhost:8000/api/v1';

const app = {
    currentUser: null,
    accessToken: null,
    refreshToken: null,
    ws: null,
    currentRoomId: null,
    userChats: [],
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,

    // Initialize app
    init() {
        console.log('🚀 Realtime Chat AI loaded');
        this.checkExistingSession();
        this.setupEventListeners();
    },

    // Check for existing session on page load
    checkExistingSession() {
        const token = localStorage.getItem('accessToken');
        const userStr = localStorage.getItem('currentUser');
        
        if (token && userStr) {
            try {
                this.accessToken = token;
                this.refreshToken = localStorage.getItem('refreshToken');
                this.currentUser = JSON.parse(userStr);
                this.showChatInterface();
            } catch (error) {
                console.error('Failed to restore session:', error);
                this.clearSession();
            }
        }
    },

    // Setup event listeners (only once)
    setupEventListeners() {
        const messageInput = document.getElementById('messageInput');
        if (messageInput && !messageInput.dataset.listenerAdded) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            messageInput.dataset.listenerAdded = 'true';
        }
    },

    // Auth Functions
    showRegister() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'block';
        document.getElementById('authError').style.display = 'none';
    },

    showLogin() {
        document.getElementById('registerForm').style.display = 'none';
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('authError').style.display = 'none';
    },

    showError(message) {
        const errorDiv = document.getElementById('authError');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    },

    async register() {
        const email = document.getElementById('registerEmail').value.trim();
        const username = document.getElementById('registerUsername').value.trim();
        const fullName = document.getElementById('registerFullName').value.trim();
        const password = document.getElementById('registerPassword').value;

        if (!email || !username || !password) {
            this.showError('All fields are required');
            return;
        }

        if (password.length < 8) {
            this.showError('Password must be at least 8 characters');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, username, full_name: fullName, password})
            });

            const data = await response.json();

            if (response.ok) {
                this.saveSession(data);
                this.showChatInterface();
            } else {
                this.showError(data.detail || 'Registration failed');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Register error:', error);
        }
    },

    async login() {
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;

        if (!email || !password) {
            this.showError('Email and password are required');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });

            const data = await response.json();

            if (response.ok) {
                this.saveSession(data);
                this.showChatInterface();
            } else {
                this.showError(data.detail || 'Login failed');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Login error:', error);
        }
    },

    saveSession(data) {
        this.accessToken = data.access_token;
        this.refreshToken = data.refresh_token;
        this.currentUser = data.user;
        
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        localStorage.setItem('currentUser', JSON.stringify(data.user));
    },

    clearSession() {
        this.accessToken = null;
        this.refreshToken = null;
        this.currentUser = null;
        
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('currentUser');
    },

    logout() {
        // Close WebSocket
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        // Clear session
        this.clearSession();
        
        // Reset UI
        this.currentRoomId = null;
        this.userChats = [];
        
        // Show auth screen
        document.getElementById('chatContainer').style.display = 'none';
        document.getElementById('authContainer').style.display = 'flex';
        this.showLogin();
        
        console.log('Logged out successfully');
    },

    showChatInterface() {
        document.getElementById('authContainer').style.display = 'none';
        document.getElementById('chatContainer').style.display = 'flex';
        
        const adminBadge = this.currentUser.is_admin ? 
            '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px;">ADMIN</span>' : '';
        
        document.getElementById('userInfo').innerHTML = `
            Logged in as <strong>${this.currentUser.username}</strong>${adminBadge}<br>
            <small>ID: ${this.currentUser.id}</small>
        `;
        
        // Show/hide analytics button based on admin status
        const adminButton = document.querySelector('.admin-link-btn');
        if (adminButton) {
            adminButton.style.display = this.currentUser.is_admin ? 'block' : 'none';
        }
        
        this.loadUserChats();
        this.setupEventListeners();
    },

    // API call wrapper with token refresh
    async fetchWithAuth(url, options = {}) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.accessToken}`
        };

        let response = await fetch(url, options);

        // If unauthorized, try to refresh token
        if (response.status === 401) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                // Retry with new token
                options.headers['Authorization'] = `Bearer ${this.accessToken}`;
                response = await fetch(url, options);
            } else {
                // Refresh failed, logout
                this.logout();
                throw new Error('Session expired. Please login again.');
            }
        }

        return response;
    },

    async refreshAccessToken() {
        if (!this.refreshToken) return false;

        try {
            const response = await fetch(`${API_URL}/auth/refresh`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({refresh_token: this.refreshToken})
            });

            if (response.ok) {
                const data = await response.json();
                this.saveSession(data);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        return false;
    },

    // Chat Functions
    async loadUserChats() {
        try {
            const response = await this.fetchWithAuth(`${API_URL}/chat/rooms`);

            if (response.ok) {
                this.userChats = await response.json();
                this.displayChatList();
            }
        } catch (error) {
            console.error('Failed to load chats:', error);
        }
    },

    displayChatList() {
        const chatList = document.getElementById('chatList');
        chatList.innerHTML = '';

        if (this.userChats.length === 0) {
            chatList.innerHTML = '<div class="loading">No chats yet. Create one!</div>';
            return;
        }

        this.userChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            chatItem.dataset.roomId = chat.id;
            chatItem.onclick = () => this.selectChat(chat.id, chatItem);
            
            const lastMsg = chat.last_message ? 
                this.escapeHtml(chat.last_message.content.substring(0, 50)) : 
                'No messages yet';
            
            chatItem.innerHTML = `
                <div class="chat-name">${this.escapeHtml(chat.name || 'Unnamed Chat')}</div>
                <div class="chat-preview">${lastMsg}</div>
            `;
            
            chatList.appendChild(chatItem);
        });
    },

    async selectChat(roomId, chatElement) {
        this.currentRoomId = roomId;
        
        // Update active state
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        chatElement.classList.add('active');

        const chat = this.userChats.find(c => c.id === roomId);
        document.getElementById('chatTitle').textContent = this.escapeHtml(chat.name || 'Chat');
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;

        // Load chat history
        await this.loadChatHistory(roomId);

        // Connect WebSocket
        this.connectWebSocket(roomId);
    },

    async loadChatHistory(roomId) {
        try {
            const response = await this.fetchWithAuth(
                `${API_URL}/chat/rooms/${roomId}/messages?limit=50`
            );

            if (response.ok) {
                const messages = await response.json();
                this.displayMessages(messages);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    },

    displayMessages(messages) {
        const container = document.getElementById('messagesContainer');
        container.innerHTML = '';

        if (messages.length === 0) {
            container.innerHTML = '<div class="welcome-message"><p>No messages yet. Start the conversation!</p></div>';
            return;
        }

        messages.forEach(msg => {
            this.addMessageToUI(msg);
        });

        container.scrollTop = container.scrollHeight;
    },

    addMessageToUI(message) {
        const container = document.getElementById('messagesContainer');
        
        // Remove welcome message if exists
        const welcome = container.querySelector('.welcome-message');
        if (welcome) welcome.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender_id === this.currentUser.id ? 'own' : ''}`;

        const timestamp = message.created_at || message.timestamp;
        const time = new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        messageDiv.innerHTML = `
            <div class="message-content">
                ${message.sender_id !== this.currentUser.id ? 
                    `<div class="message-sender">${this.escapeHtml(message.sender_username)}</div>` : ''}
                <div class="message-text">${this.escapeHtml(message.content)}</div>
                <div class="message-footer">
                    <span class="message-time">${time}</span>
                </div>
            </div>
        `;

        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    },

    connectWebSocket(roomId) {
        // Close existing connection
        if (this.ws) {
            this.ws.close();
        }

        const wsUrl = `ws://localhost:8000/api/v1/ws/${roomId}?token=${this.accessToken}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            document.getElementById('chatStatus').textContent = '● Connected';
            console.log('✓ WebSocket connected');
            this.reconnectAttempts = 0; // Reset on successful connection
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'message') {
                this.addMessageToUI(data);
            } else if (data.type === 'user_joined') {
                this.addSystemMessage(`${data.username} joined the chat`);
            } else if (data.type === 'user_left') {
                this.addSystemMessage(`${data.username} left the chat`);
            } else if (data.type === 'error') {
                console.error('WebSocket error:', data.message);
                this.showError(data.message);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            document.getElementById('chatStatus').textContent = '● Connection error';
        };

        this.ws.onclose = (event) => {
            document.getElementById('chatStatus').textContent = '● Disconnected';
            console.log('WebSocket disconnected');
            
            // Auto-reconnect if it was an abnormal closure
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                setTimeout(() => {
                    if (this.currentRoomId) {
                        this.connectWebSocket(this.currentRoomId);
                    }
                }, 2000 * this.reconnectAttempts); // Exponential backoff
            }
        };
    },

    addSystemMessage(text) {
        const container = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.textContent = text;
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    },

    sendMessage() {
        const input = document.getElementById('messageInput');
        const content = input.value.trim();

        if (!content) {
            return;
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showError('Not connected. Please wait...');
            return;
        }

        this.ws.send(JSON.stringify({
            content: content,
            message_type: 'text'
        }));

        input.value = '';
    },

    // Modal Functions
    showNewChatModal() {
        document.getElementById('newChatModal').classList.add('active');
    },

    closeNewChatModal() {
        document.getElementById('newChatModal').classList.remove('active');
        document.getElementById('chatType').value = 'one-to-one';
        document.getElementById('groupNameField').style.display = 'none';
        document.getElementById('groupName').value = '';
        document.getElementById('participantId').value = '';
    },

    toggleGroupFields() {
        const chatType = document.getElementById('chatType').value;
        const groupNameField = document.getElementById('groupNameField');
        groupNameField.style.display = chatType === 'group' ? 'block' : 'none';
    },

    async createNewChat() {
        const chatType = document.getElementById('chatType').value;
        const participantId = document.getElementById('participantId').value.trim();
        const groupName = document.getElementById('groupName').value.trim();

        if (!participantId) {
            alert('Please enter participant ID');
            return;
        }

        const isGroup = chatType === 'group';

        try {
            const response = await this.fetchWithAuth(`${API_URL}/chat/rooms`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: isGroup ? groupName : null,
                    is_group: isGroup,
                    participant_ids: [participantId]
                })
            });

            if (response.ok) {
                this.closeNewChatModal();
                await this.loadUserChats();
                alert('Chat created successfully!');
            } else {
                const error = await response.json();
                alert(error.detail || 'Failed to create chat');
            }
        } catch (error) {
            alert('Network error. Please try again.');
            console.error('Create chat error:', error);
        }
    },

    openAdminDashboard() {
        window.open('admin.html', '_blank');
    },

    // Utility
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    app.init();
}