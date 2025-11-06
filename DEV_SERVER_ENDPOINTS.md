# Development Server API Endpoints

**Server:** http://localhost:3002  
**Status:** ✅ All endpoints implemented

---

## 🔐 Authentication Endpoints

### POST /api/auth/signup
Create a new user account

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "role": "consumer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account created!",
  "userId": "dev-user-1234567890",
  "confirmationRequired": true
}
```

### POST /api/auth/signin
Sign in with email and password

**Request:**
```json
{
  "email": "demo@aquachain.com",
  "password": "demo123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sign in successful!",
  "user": {
    "userId": "user_xxx",
    "email": "demo@aquachain.com",
    "name": "Demo Admin",
    "role": "admin",
    "emailVerified": true
  },
  "token": "dev-token-xxx"
}
```

### POST /api/auth/validate
Validate user session

**Headers:**
```
Authorization: Bearer dev-token-xxx
```

**Request:**
```json
{
  "email": "demo@aquachain.com"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "userId": "user_xxx",
    "email": "demo@aquachain.com",
    "name": "Demo Admin",
    "role": "admin",
    "emailVerified": true
  }
}
```

### GET /api/auth/verification-status/:email
Check email verification status

**Response:**
```json
{
  "success": true,
  "emailVerified": true,
  "email": "demo@aquachain.com"
}
```

---

## 📊 Dashboard Endpoints

### GET /dashboard/stats
Get dashboard statistics

**Response:**
```json
{
  "success": true,
  "stats": {
    "totalDevices": 3,
    "activeDevices": 2,
    "criticalAlerts": 1,
    "averageWQI": 78,
    "totalUsers": 5,
    "pendingRequests": 2
  }
}
```

---

## 💧 Water Quality Endpoints

### GET /water-quality/latest
Get latest water quality reading

**Response:**
```json
{
  "success": true,
  "reading": {
    "deviceId": "DEV-3421",
    "timestamp": "2025-11-05T16:00:00.000Z",
    "wqi": 78,
    "readings": {
      "pH": 7.2,
      "turbidity": 1.5,
      "tds": 150,
      "temperature": 25.0
    },
    "location": {
      "latitude": 9.9312,
      "longitude": 76.2673
    },
    "diagnostics": {
      "batteryLevel": 85,
      "signalStrength": -65,
      "sensorStatus": "normal"
    },
    "anomalyType": "normal"
  }
}
```

---

## 🚨 Alerts Endpoints

### GET /alerts?limit=20
Get recent alerts

**Query Parameters:**
- `limit` (optional): Number of alerts to return (default: 20)

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "id": "alert-1",
      "deviceId": "DEV-3421",
      "timestamp": "2025-11-05T15:00:00.000Z",
      "severity": "warning",
      "wqi": 65,
      "message": "Water quality below optimal range",
      "acknowledged": false
    }
  ],
  "count": 2
}
```

---

## 🔌 Devices Endpoints

### GET /devices
Get all devices

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "deviceId": "DEV-3421",
      "name": "Kitchen Sink",
      "status": "online",
      "location": {
        "latitude": 9.9312,
        "longitude": 76.2673,
        "address": "123 Main St, Kochi, Kerala"
      },
      "lastReading": "2025-11-05T16:00:00.000Z",
      "batteryLevel": 85,
      "wqi": 78
    }
  ],
  "count": 3
}
```

---

## 📈 Analytics Endpoints

### POST /api/analytics
Send analytics event

**Request:**
```json
{
  "event": "page_view",
  "page": "/dashboard",
  "timestamp": "2025-11-05T16:00:00.000Z"
}
```

**Response:**
```json
{
  "success": true
}
```

### POST /api/rum
Send Real User Monitoring data

**Request:**
```json
{
  "session": {
    "sessionId": "session-xxx"
  },
  "events": [
    {
      "type": "page_load",
      "duration": 1234
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "RUM data received",
  "sessionId": "session-xxx",
  "eventsProcessed": 1
}
```

---

## 🔧 Development Endpoints

### GET /api/health
Health check

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-05T16:00:00.000Z",
  "service": "aquachain-dev-server"
}
```

### GET /api/auth/dev-users
List all development users

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "email": "demo@aquachain.com",
      "name": "Demo Admin",
      "role": "admin",
      "emailVerified": true,
      "createdAt": "2025-11-05T10:00:00.000Z",
      "lastLogin": "2025-11-05T16:00:00.000Z"
    }
  ],
  "count": 3
}
```

### POST /api/dev/verify-email
Manually verify an email (dev only)

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "user": {
    "email": "user@example.com",
    "emailVerified": true
  }
}
```

### DELETE /api/dev/delete-user/:email
Delete a user account (dev only)

**Response:**
```json
{
  "success": true,
  "message": "User deleted"
}
```

### GET /api/dev/users
List all users with full details (dev only)

**Response:**
```json
{
  "success": true,
  "count": 3,
  "users": [...]
}
```

---

## 🔌 WebSocket

### ws://localhost:3002/ws
WebSocket connection for real-time updates

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:3002/ws');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Welcome Message:**
```json
{
  "type": "welcome",
  "message": "Connected to AquaChain Development WebSocket Server"
}
```

---

## 👥 Demo Users

Pre-configured users for testing:

| Email | Password | Role | Status |
|-------|----------|------|--------|
| demo@aquachain.com | demo123 | admin | ✅ Verified |
| tech@aquachain.com | demo123 | technician | ✅ Verified |
| user@aquachain.com | demo123 | consumer | ✅ Verified |

---

## 🚀 Quick Start

### Start Server
```bash
cd frontend
node src/dev-server.js
```

### Test Endpoints
```bash
# Health check
curl http://localhost:3002/api/health

# Get dashboard stats
curl http://localhost:3002/dashboard/stats

# Get latest water quality
curl http://localhost:3002/water-quality/latest

# Get alerts
curl http://localhost:3002/alerts?limit=5

# Get devices
curl http://localhost:3002/devices

# Sign in
curl -X POST http://localhost:3002/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@aquachain.com","password":"demo123"}'
```

---

## 📝 Notes

### Data Persistence
- User data is stored in `.dev-data.json`
- Data persists across server restarts
- Delete `.dev-data.json` to reset

### Auto Email Verification
- New signups are auto-verified after 2 seconds
- Simulates email verification flow
- Can manually verify with `/api/dev/verify-email`

### Mock Data
- All endpoints return realistic mock data
- Data is static but consistent
- Suitable for frontend development and testing

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :3002
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3002 | xargs kill -9
```

### Server Not Starting
```bash
# Check dependencies
cd frontend
npm install express cors ws

# Start server
node src/dev-server.js
```

### Endpoints Not Working
- Check server is running on port 3002
- Verify frontend .env has correct API endpoint
- Check browser console for errors

---

**Last Updated:** November 5, 2025  
**Status:** ✅ All endpoints implemented  
**Server:** http://localhost:3002
