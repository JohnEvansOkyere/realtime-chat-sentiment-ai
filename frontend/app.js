// frontend/app.js
const API_URL = 'http://localhost:8000/api/v1';

const app = {
    currentUser: null,
    accessToken: null,
    ws: null,
    currentRoomId: null,
    userChats: [],

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
                this.accessToken = data.access_token;
                this.currentUser = data.user;
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
                this.accessToken = data.access_token;
                this.currentUser = data.user;
                this.showChatInterface();
            } else {
                this.showError(data.detail || 'Login failed');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Login error:', error);
        }
    },

    showChatInterface() {
        document.getElementById('authContainer').style.display = 'none';
        document.getElementById('chatContainer').style.display = 'flex';
        document.getElementById('userInfo').innerHTML = `
            Logged in as <strong>${this.currentUser.username}</strong><br>
            <small>ID: ${this.currentUser.id}</small>
        `;
        this.loadUserChats();
        
        // Enable Enter key for sending messages
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    },

    // Chat Functions
    async loadUserChats() {
        try {
            const response = await fetch(`${API_URL}/chat/rooms`, {
                headers: {'Authorization': `Bearer ${this.accessToken}`}
            });

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
                chat.last_message.content.substring(0, 50) : 
                'No messages yet';
            
            chatItem.innerHTML = `
                <div class="chat-name">${chat.name || 'Unnamed Chat'}</div>
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
        document.getElementById('chatTitle').textContent = chat.name || 'Chat';
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;

        // Load chat history
        await this.loadChatHistory(roomId);

        // Connect WebSocket
        this.connectWebSocket(roomId);
    },

    async loadChatHistory(roomId) {
        try {
            const response = await fetch(`${API_URL}/chat/rooms/${roomId}/messages?limit=50`, {
                headers: {'Authorization': `Bearer ${this.accessToken}`}
            });

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

        const time = new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        const sentimentBadge = message.sentiment ? 
            `<span class="sentiment-badge sentiment-${message.sentiment}">${message.sentiment}</span>` : '';

        messageDiv.innerHTML = `
            <div class="message-content">
                ${message.sender_id !== this.currentUser.id ? 
                    `<div class="message-sender">${message.sender_username}</div>` : ''}
                <div class="message-text">${this.escapeHtml(message.content)}</div>
                <div class="message-footer">
                    <span class="message-time">${time}</span>
                    ${sentimentBadge}
                </div>
            </div>
        `;

        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    },

    connectWebSocket(roomId) {
        if (this.ws) {
            this.ws.close();
        }

        const wsUrl = `ws://localhost:8000/api/v1/ws/${roomId}?token=${this.accessToken}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            document.getElementById('chatStatus').textContent = '● Connected';
            console.log('✓ WebSocket connected');
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
                alert('Error: ' + data.message);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            document.getElementById('chatStatus').textContent = '● Connection error';
        };

        this.ws.onclose = () => {
            document.getElementById('chatStatus').textContent = '● Disconnected';
            console.log('WebSocket disconnected');
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

        if (!content || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
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
            const response = await fetch(`${API_URL}/chat/rooms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.accessToken}`
                },
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

// Initialize
console.log('🚀 Realtime Chat AI loaded');