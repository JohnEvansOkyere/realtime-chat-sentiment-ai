// frontend/config.js
const config = {
    // Automatically detect environment
    API_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api/v1'  // Local development
        : 'https://realtime-chat-sentiment-ai.onrender.com/api/v1',  
    
    WS_URL: window.location.hostname === 'localhost'
        ? 'ws://localhost:8000/api/v1'
        : 'wss://https://realtime-chat-sentiment-ai.onrender.com/api/v1'
};