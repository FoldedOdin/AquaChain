# Local Development Guide - Run Without AWS Deployment

This guide shows you how to run AquaChain locally for development and testing **without deploying to AWS**.

---

## ✅ What You CAN Run Locally

| Component | Status | How to Run |
|-----------|--------|------------|
| **Frontend UI** | ✅ Fully Local | `npm start` in frontend folder |
| **Frontend (Docker)** | ✅ Fully Local | `docker-compose up` |
| **IoT Simulator** | ✅ Fully Local | Python simulator (mock data) |
| **ML Models** | ✅ Fully Local | Load from local files |
| **Unit Tests** | ✅ Fully Local | `npm test` / `pytest` |
| **Storybook** | ✅ Fully Local | Component development |

## ❌ What REQUIRES AWS Deployment

| Component | Why AWS Required |
|-----------|------------------|
| **Lambda Functions** | Serverless compute (can use SAM Local for testing) |
| **DynamoDB** | Managed database (can use DynamoDB Local) |
| **API Gateway** | Managed API service |
| **IoT Core** | Managed MQTT broker |
| **Cognito** | Authentication service |
| **S3** | Object storage |

---

## 🚀 Quick Start Options

### Option 1: Frontend Only (Fastest - 2 minutes)

**Best for:** UI development, design work, component testing

```bash
cd frontend
npm install
npm start
```

**Access:** http://localhost:3000

**Features Available:**
- ✅ Full UI/UX
- ✅ Component interactions
- ✅ Routing and navigation
- ✅ Mock data visualization
- ❌ Real authentication (uses mock)
- ❌ Real API calls (uses mock)
- ❌ Real-time updates

---

### Option 2: Frontend with Docker (5 minutes)

**Best for:** Production-like environment testing

```bash
cd frontend
docker-compose -f docker/docker-compose.yml up -d
```

**Access:** http://localhost:3000

**Features:**
- ✅ Production build
- ✅ Nginx web server
- ✅ Health checks
- ✅ Container orchestration
- ❌ Backend services

**Stop:**
```bash
docker-compose -f docker/docker-compose.yml down
```

---

### Option 3: Frontend + IoT Simulator (10 minutes)

**Best for:** Testing sensor data flow, data visualization

#### Step 1: Start Frontend
```bash
cd frontend
npm install
npm start
```

#### Step 2: Run IoT Simulator (in new terminal)
```bash
cd iot-simulator
pip install -r requirements.txt
python simulator.py --mode local
```

**Features:**
- ✅ Frontend UI
- ✅ Simulated sensor data
- ✅ Data visualization
- ✅ Mock device management
- ❌ Cloud storage
- ❌ Real authentication

---

### Option 4: Full Local Stack with Mocks (15 minutes)

**Best for:** Full-stack development without AWS costs

This requires setting up local alternatives:

#### 1. DynamoDB Local
```bash
# Download and run DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local
```

#### 2. LocalStack (AWS Services Emulator)
```bash
# Run LocalStack for S3, Lambda, etc.
docker run -p 4566:4566 localstack/localstack
```

#### 3. Frontend with Mock Backend
```bash
cd frontend
npm run start:full  # Starts dev server + mock backend
```

**Access:** http://localhost:3000

---

## 📋 Detailed Setup Instructions

### Frontend Development Setup

#### Prerequisites
- Node.js 18+ ([Download](https://nodejs.org))
- npm or yarn

#### Installation
```bash
cd frontend
npm install
```

#### Environment Configuration

Create `.env.local` for local development:

```bash
# Frontend .env.local
REACT_APP_ENV=local
REACT_APP_API_ENDPOINT=http://localhost:3001
REACT_APP_WEBSOCKET_ENDPOINT=ws://localhost:3001/ws

# Mock authentication (no real Cognito)
REACT_APP_USE_MOCK_AUTH=true
REACT_APP_MOCK_USER_EMAIL=demo@aquachain.local
REACT_APP_MOCK_USER_ROLE=consumer

# Feature flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_RECAPTCHA=false
```

#### Available Scripts

```bash
# Development server
npm start                    # Start at http://localhost:3000

# With mock backend
npm run start:full          # Frontend + mock API server

# Testing
npm test                    # Run unit tests
npm run test:coverage       # With coverage report
npm run test:a11y          # Accessibility tests

# Code quality
npm run lint               # Check code quality
npm run lint:fix           # Auto-fix issues
npm run format             # Format code

# Component development
npm run storybook          # Start Storybook at http://localhost:6006

# Build
npm run build              # Production build
npm run build:analyze      # Analyze bundle size
```

---

### IoT Simulator Setup

#### Prerequisites
- Python 3.11+
- pip

#### Installation
```bash
cd iot-simulator
pip install -r requirements.txt
```

#### Run Simulator (Local Mode)

```bash
# Generate mock sensor data
python simulator.py --mode local --devices 5 --interval 60

# Options:
#   --mode local          : Run without AWS IoT Core
#   --devices N           : Number of simulated devices
#   --interval SECONDS    : Data generation interval
#   --output FILE         : Save data to JSON file
```

#### Sample Output
```json
{
  "device_id": "AquaChain-Sim-001",
  "timestamp": "2025-11-01T10:30:00Z",
  "readings": {
    "pH": 7.2,
    "turbidity": 1.5,
    "tds": 150,
    "temperature": 22.5
  }
}
```

---

### ML Model Testing (Local)

#### Prerequisites
```bash
pip install -r requirements-dev.txt
```

#### Load and Test Models Locally

```python
# Example: Test WQI prediction locally
import pickle
import numpy as np

# Load model from local backup
with open('ml_models_backup/wqi-model-vcustom.pkl', 'rb') as f:
    model = pickle.load(f)

# Test prediction
sample_data = np.array([[7.2, 1.5, 150, 22.5]])  # pH, turbidity, TDS, temp
wqi_prediction = model.predict(sample_data)
print(f"Predicted WQI: {wqi_prediction[0]}")
```

#### Run ML Tests
```bash
cd lambda/ml_inference
pytest test_local_inference.py -v
```

---

## 🧪 Testing Without AWS

### Unit Tests (No AWS Required)

```bash
# Frontend tests
cd frontend
npm test

# Backend tests (with mocks)
cd lambda
pytest tests/unit/ -v

# All tests
python -m pytest tests/ -v --cov
```

### Integration Tests (Mock AWS Services)

```bash
# Uses moto library to mock AWS services
pytest tests/integration/ -v
```

### End-to-End Tests (Frontend Only)

```bash
cd frontend
npm run test:comprehensive
```

---

## 🐳 Docker Development

### Build Frontend Container

```bash
cd frontend
docker build -f docker/Dockerfile -t aquachain-frontend:local .
```

### Run with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### View Logs

```bash
docker-compose -f docker/docker-compose.yml logs -f
```

### Stop Containers

```bash
docker-compose -f docker/docker-compose.yml down
```

---

## 🎨 Component Development with Storybook

**Best for:** Isolated component development and testing

```bash
cd frontend
npm run storybook
```

**Access:** http://localhost:6006

**Features:**
- ✅ Component library
- ✅ Interactive props
- ✅ Accessibility testing
- ✅ Visual regression testing
- ✅ Documentation

---

## 🔧 Mock Backend Server

The frontend includes a mock backend for local development:

```bash
cd frontend
npm run dev-server
```

**Provides:**
- Mock authentication endpoints
- Mock device data API
- Mock sensor readings
- WebSocket simulation

**Endpoints:**
```
POST   /api/auth/login
GET    /api/devices
GET    /api/devices/:id/readings
GET    /api/alerts
WS     ws://localhost:3001/ws
```

---

## 📊 What Works Without AWS

### ✅ Fully Functional Locally

1. **UI/UX Development**
   - All React components
   - Routing and navigation
   - Forms and validation
   - Charts and visualizations
   - Responsive design

2. **Component Testing**
   - Unit tests
   - Integration tests
   - Accessibility tests
   - Visual regression tests

3. **Data Visualization**
   - Mock sensor data
   - Chart rendering
   - Dashboard layouts
   - Real-time updates (simulated)

4. **ML Model Testing**
   - Load models from local files
   - Run predictions
   - Test accuracy
   - Performance benchmarking

### ⚠️ Limited Functionality

1. **Authentication**
   - Can use mock authentication
   - No real Cognito integration
   - Session management simulated

2. **Data Persistence**
   - In-memory storage only
   - No DynamoDB
   - Data lost on restart

3. **Real-Time Updates**
   - Simulated WebSocket
   - No actual IoT Core
   - Polling instead of push

### ❌ Requires AWS Deployment

1. **Production Features**
   - Real authentication (Cognito)
   - Persistent storage (DynamoDB)
   - IoT device connectivity
   - Email notifications (SES)
   - SMS alerts (SNS)
   - CDN delivery (CloudFront)

---

## 🎯 Development Workflows

### Workflow 1: UI Development

```bash
# Terminal 1: Start frontend
cd frontend
npm start

# Terminal 2: Run Storybook
npm run storybook

# Terminal 3: Watch tests
npm test -- --watch
```

### Workflow 2: Full-Stack Development

```bash
# Terminal 1: Start DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Terminal 2: Start mock backend
cd frontend
npm run dev-server

# Terminal 3: Start frontend
npm start

# Terminal 4: Run IoT simulator
cd iot-simulator
python simulator.py --mode local
```

### Workflow 3: Testing & QA

```bash
# Run all tests
npm run test:comprehensive

# Check accessibility
npm run test:a11y

# Performance testing
npm run lighthouse

# Security audit
npm audit
```

---

## 💡 Tips for Local Development

### 1. Use Mock Data

Create `frontend/src/mocks/mockData.ts`:

```typescript
export const mockDevices = [
  {
    device_id: 'AquaChain-Local-001',
    name: 'Kitchen Sink',
    status: 'online',
    last_reading: {
      pH: 7.2,
      turbidity: 1.5,
      tds: 150,
      temperature: 22.5,
      timestamp: new Date().toISOString()
    }
  }
];
```

### 2. Enable Hot Reload

Frontend automatically reloads on file changes. For backend:

```bash
# Use nodemon for auto-restart
npm install -g nodemon
nodemon src/dev-server.js
```

### 3. Debug with Browser DevTools

- React DevTools extension
- Redux DevTools (if using Redux)
- Network tab for API calls
- Console for errors

### 4. Use Environment Variables

Switch between local and AWS easily:

```bash
# Local development
npm run switch-to-dev

# AWS deployment
npm run switch-to-aws
```

---

## 🚨 Common Issues & Solutions

### Issue: Port Already in Use

```bash
# Find process using port 3000
netstat -ano | findstr :3000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
PORT=3001 npm start
```

### Issue: Module Not Found

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: Docker Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose build --no-cache
docker-compose up
```

---

## 📚 Additional Resources

- **Frontend README:** `frontend/README.md`
- **IoT Simulator:** `iot-simulator/README.md`
- **Testing Guide:** `tests/PHASE3_TEST_GUIDE.md`
- **Deployment Guide:** `docs/SETUP_GUIDE.md`

---

## 🎓 Learning Path

### Beginner: Start Here
1. Run frontend: `cd frontend && npm start`
2. Explore UI at http://localhost:3000
3. Check Storybook: `npm run storybook`
4. Run tests: `npm test`

### Intermediate: Add Complexity
1. Start mock backend: `npm run start:full`
2. Run IoT simulator: `python simulator.py --mode local`
3. Test with mock data
4. Modify components

### Advanced: Full Local Stack
1. Set up DynamoDB Local
2. Configure LocalStack
3. Run integration tests
4. Deploy to AWS when ready

---

## ✅ Summary

**You CAN run locally:**
- ✅ Frontend UI (React app)
- ✅ Component development (Storybook)
- ✅ Unit & integration tests
- ✅ IoT data simulation
- ✅ ML model testing
- ✅ Docker containers

**You NEED AWS for:**
- ❌ Real authentication (Cognito)
- ❌ Persistent storage (DynamoDB)
- ❌ Real IoT devices (IoT Core)
- ❌ Production APIs (API Gateway + Lambda)
- ❌ Notifications (SNS/SES)
- ❌ CDN (CloudFront)

**Recommendation:**
- Start with **Option 1** (Frontend only) for UI work
- Use **Option 3** (Frontend + Simulator) for data testing
- Deploy to AWS when you need production features

**Cost:** $0 for local development! 🎉

---

**Last Updated:** November 1, 2025  
**Status:** ✅ Ready for Local Development
