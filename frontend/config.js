// frontend/config.js
const config = {
    // Simple: localhost uses local backend, Vercel uses production
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000/api/v1'
        : 'https://realtime-chat-sentiment-ai-1.onrender.com/api/v1',
    
    WS_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'ws://localhost:8000/api/v1'
        : 'wss://realtime-chat-sentiment-ai-1.onrender.com/api/v1'
};