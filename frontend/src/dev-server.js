/**
 * Development Server for Missing API Endpoints
 * This handles the RUM API and other missing endpoints during development
 */

const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3002;

// File path for persistent storage
const DEV_DATA_FILE = path.join(__dirname, '../../.dev-data.json');

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// RUM API endpoint
app.post('/api/rum', (req, res) => {
  const { session, events } = req.body;
  
  // Log RUM data in development
  console.log('RUM Data Received:');
  console.log('Session:', session?.sessionId);
  console.log('Events:', events?.length || 0);
  
  // In development, just acknowledge receipt
  res.json({ 
    success: true, 
    message: 'RUM data received',
    sessionId: session?.sessionId,
    eventsProcessed: events?.length || 0
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    service: 'aquachain-dev-server'
  });
});

// Mock analytics endpoint
app.post('/api/analytics', (req, res) => {
  console.log('Analytics Event:', req.body);
  res.json({ success: true });
});

// Persistent storage for development (survives server restarts)
const devUsers = new Map();
const validTokens = new Map();

// Load existing users from file
function loadDevData() {
  try {
    if (fs.existsSync(DEV_DATA_FILE)) {
      const data = JSON.parse(fs.readFileSync(DEV_DATA_FILE, 'utf8'));
      
      // Load users
      if (data.users) {
        Object.entries(data.users).forEach(([email, user]) => {
          devUsers.set(email, user);
        });
        console.log(`✅ Loaded ${devUsers.size} existing users from storage`);
      }
      
      // Load tokens
      if (data.tokens) {
        Object.entries(data.tokens).forEach(([token, tokenData]) => {
          validTokens.set(token, tokenData);
        });
        console.log(`✅ Loaded ${validTokens.size} active tokens from storage`);
      }
    } else {
      console.log('📝 No existing dev data found - starting fresh');
    }
  } catch (error) {
    console.error('⚠️  Error loading dev data:', error.message);
  }
}

// Save users to file
function saveDevData() {
  try {
    const data = {
      users: Object.fromEntries(devUsers),
      tokens: Object.fromEntries(validTokens),
      lastUpdated: new Date().toISOString()
    };
    fs.writeFileSync(DEV_DATA_FILE, JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('⚠️  Error saving dev data:', error.message);
  }
}

// Load data on startup
loadDevData();

// Mock auth endpoints
app.post('/api/auth/signup', (req, res) => {
  const { email, password, name, role } = req.body;
  console.log('Signup attempt:', email);
  
  // Check if user already exists
  if (devUsers.has(email)) {
    return res.status(400).json({ 
      success: false, 
      error: 'User already exists. Please sign in instead.' 
    });
  }
  
  // Store user credentials for later login
  devUsers.set(email, {
    email,
    password,
    name,
    role,
    userId: 'dev-user-' + Date.now(),
    emailVerified: false, // Will be auto-verified after a short delay
    createdAt: new Date().toISOString()
  });
  
  // Save to file
  saveDevData();
  
  // Auto-verify email after 2 seconds (simulate email verification)
  setTimeout(() => {
    if (devUsers.has(email)) {
      devUsers.get(email).emailVerified = true;
      console.log(`Auto-verified email for: ${email}`);
      saveDevData();
    }
  }, 2000);
  
  res.json({ 
    success: true, 
    message: 'Account created! Please check your email for verification.',
    userId: devUsers.get(email).userId,
    confirmationRequired: true
  });
});

app.post('/api/auth/signin', (req, res) => {
  const { email, password } = req.body;
  console.log('Signin attempt:', email);
  
  const user = devUsers.get(email);
  
  if (!user) {
    return res.status(401).json({ 
      success: false, 
      error: 'User not found. Please sign up first.' 
    });
  }
  
  if (user.password !== password) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid password.' 
    });
  }
  
  if (!user.emailVerified) {
    return res.status(401).json({ 
      success: false, 
      error: 'Please verify your email before signing in. Check your inbox.' 
    });
  }
  
  // Update last login
  user.lastLogin = new Date().toISOString();
  
  // Generate and store token
  const token = 'dev-token-' + Date.now() + '-' + Math.random().toString(36).substring(2);
  validTokens.set(token, {
    email: user.email,
    userId: user.userId,
    createdAt: new Date().toISOString()
  });
  
  // Save to file
  saveDevData();
  
  res.json({ 
    success: true, 
    message: 'Sign in successful!',
    user: {
      userId: user.userId,
      email: user.email,
      name: user.name,
      role: user.role,
      emailVerified: user.emailVerified
    },
    token: token
  });
});

// Email verification status endpoint
app.get('/api/auth/verification-status/:email', (req, res) => {
  const { email } = req.params;
  const user = devUsers.get(email);
  
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  res.json({
    success: true,
    emailVerified: user.emailVerified,
    email: user.email
  });
});

// Validate user session endpoint
app.post('/api/auth/validate', (req, res) => {
  const { email } = req.body;
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'No valid token provided' 
    });
  }
  
  const token = authHeader.substring(7); // Remove 'Bearer ' prefix
  
  // Check if token is valid and matches the user
  const tokenData = validTokens.get(token);
  if (!tokenData || tokenData.email !== email) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(email);
  
  if (!user) {
    return res.status(401).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  if (!user.emailVerified) {
    return res.status(401).json({ 
      success: false, 
      error: 'Email not verified' 
    });
  }
  
  res.json({
    success: true,
    user: {
      userId: user.userId,
      email: user.email,
      name: user.name,
      role: user.role,
      emailVerified: user.emailVerified
    }
  });
});

// List all dev users (for debugging)
app.get('/api/auth/dev-users', (req, res) => {
  const users = Array.from(devUsers.values()).map(user => ({
    email: user.email,
    name: user.name,
    role: user.role,
    emailVerified: user.emailVerified,
    createdAt: user.createdAt,
    lastLogin: user.lastLogin
  }));
  
  res.json({ 
    success: true, 
    users,
    count: users.length 
  });
});

// Catch-all for missing endpoints
app.use('*', (req, res) => {
  console.log(`Missing endpoint: ${req.method} ${req.originalUrl}`);
  res.status(404).json({ 
    error: 'Endpoint not found', 
    method: req.method, 
    path: req.originalUrl,
    message: 'This is a development server - endpoint not implemented'
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// WebSocket server for development
const wss = new WebSocket.Server({ server, path: '/ws' });

wss.on('connection', (ws) => {
  console.log('WebSocket client connected');
  
  // Send welcome message
  ws.send(JSON.stringify({ 
    type: 'welcome', 
    message: 'Connected to AquaChain Development WebSocket Server' 
  }));
  
  ws.on('message', (message) => {
    console.log('WebSocket message received:', message.toString());
    // Echo back for testing
    ws.send(JSON.stringify({ 
      type: 'echo', 
      data: message.toString() 
    }));
  });
  
  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 AquaChain Development Server running on http://localhost:${PORT}`);
  console.log(`📊 RUM endpoint: http://localhost:${PORT}/api/rum`);
  console.log(`🔍 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📈 Analytics: http://localhost:${PORT}/api/analytics`);
  console.log(`🔌 WebSocket: ws://localhost:${PORT}/ws`);
});

module.exports = app;