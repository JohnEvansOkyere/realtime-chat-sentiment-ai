// frontend/config.js
const config = {
    // Automatically detect environment
    API_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api/v1'
        : 'https://realtime-chat-sentiment-ai-1.onrender.com/api/v1',
    
    WS_URL: window.location.hostname === 'localhost'
        ? 'ws://localhost:8000/api/v1'
        : 'wss://realtime-chat-sentiment-ai-1.onrender.com/api/v1'  
};