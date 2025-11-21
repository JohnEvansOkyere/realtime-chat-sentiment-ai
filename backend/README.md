# Realtime Chat AI - Technical Interview Project

A production-grade real-time chat application with AI-powered message analytics, built using FastAPI, WebSockets, and MLOps best practices.

## Business Value

### Problem Solved
- **For Managers**: Understand team sentiment without reading thousands of messages
- **For HR Teams**: Early conflict detection through sentiment trend analysis
- **For Support Teams**: Auto-prioritize urgent/negative customer messages

### Key Features
- ✅ Real-time one-to-one and group chat
- ✅ JWT-based authentication with refresh tokens
- ✅ AI-powered sentiment analysis on messages
- ✅ Message categorization (question/announcement/discussion/action-item)
- ✅ Analytics dashboard with visual insights
- ✅ MLOps pipeline (MLflow + Evidently AI)
- ✅ Docker containerization
- ✅ CI/CD with GitHub Actions

## 🏗️ Architecture
```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Frontend  │ ←─────────────────→ │   FastAPI   │
│  (HTML/JS)  │     REST API        │   Backend   │
└─────────────┘                     └─────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
              ┌──────────┐          ┌───────────┐         ┌──────────┐
              │ Supabase │          │  MLflow   │         │ Evidently│
              │    DB    │          │ Tracking  │         │    AI    │
              └──────────┘          └───────────┘         └──────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Supabase account

### Setup

1. **Clone repository**
```bash
git clone <your-repo>
cd realtime-chat-ai
git checkout evans-implementation
```

2. **Configure environment**
```bash
cd backend
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. **Set up Supabase**
- Create a new Supabase project
- Run the SQL schema from `/docs/database_schema.sql`
- Copy URL and keys to `.env`

4. **Run with Docker**
```bash
docker-compose up --build
```

5. **Access services**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow UI: http://localhost:5000
- Frontend: http://localhost:3000

## 📊 Day 1 Completion Status

### ✅ Completed
- [x] Project structure setup
- [x] Authentication system (Register, Login, JWT tokens)
- [x] Database models (Users, Chat Rooms, Messages)
- [x] WebSocket foundation for real-time chat
- [x] Docker containerization
- [x] CI/CD pipeline (GitHub Actions)
- [x] Basic tests
- [x] API documentation

### 📝 API Endpoints

**Authentication**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

**WebSocket**
- `WS /api/v1/ws/{room_id}?token=<jwt_token>` - Real-time chat

## 🧪 Testing
```bash
cd backend
pytest tests/ -v
```

## 📈 Complexity Analysis

All functions are documented with time and space complexity:
- Authentication operations: O(1) - single DB queries
- WebSocket broadcast: O(n) where n = room participants
- Message storage: O(1) - single DB insert

## 👨‍💻 Author

Evans - AI/ML Specialist & Full-Stack Developer

## 📄 License

MIT License