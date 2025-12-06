
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

// Track server metrics
const serverMetrics = {
  startTime: Date.now(),
  apiCalls: 0,
  apiErrors: 0,
  endpoints: {}
};

// File path for persistent storage
const DEV_DATA_FILE = path.join(__dirname, '../../.dev-data.json');

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Logging and metrics middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  
  // Track API calls
  serverMetrics.apiCalls++;
  const endpoint = `${req.method} ${req.path}`;
  serverMetrics.endpoints[endpoint] = (serverMetrics.endpoints[endpoint] || 0) + 1;
  
  // Track response time
  const startTime = Date.now();
  
  // Capture response
  const originalSend = res.send;
  res.send = function(data) {
    const responseTime = Date.now() - startTime;
    
    // Track errors
    if (res.statusCode >= 400) {
      serverMetrics.apiErrors++;
    }
    
    return originalSend.call(this, data);
  };
  
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

// Get system metrics (Admin only)
app.get('/api/admin/metrics', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  // Calculate uptime
  const uptimeMs = Date.now() - serverMetrics.startTime;
  const uptimeHours = uptimeMs / (1000 * 60 * 60);
  const uptimeDays = uptimeHours / 24;
  
  // Calculate API success rate
  const totalCalls = serverMetrics.apiCalls;
  const successfulCalls = totalCalls - serverMetrics.apiErrors;
  const apiUptime = totalCalls > 0 ? (successfulCalls / totalCalls) * 100 : 100;
  
  res.json({
    success: true,
    metrics: {
      serverStartTime: new Date(serverMetrics.startTime).toISOString(),
      uptimeMs: uptimeMs,
      uptimeHours: uptimeHours.toFixed(2),
      uptimeDays: uptimeDays.toFixed(2),
      systemUptime: 100, // Server is running = 100% uptime
      apiUptime: apiUptime.toFixed(1),
      totalApiCalls: totalCalls,
      successfulApiCalls: successfulCalls,
      failedApiCalls: serverMetrics.apiErrors,
      topEndpoints: Object.entries(serverMetrics.endpoints)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([endpoint, count]) => ({ endpoint, count }))
    }
  });
});

// DEV ONLY: Manually verify any email
app.post('/api/dev/verify-email', (req, res) => {
  const { email } = req.body;
  
  const user = devUsers.get(email);
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  user.emailVerified = true;
  saveDevData();
  
  console.log(`✅ Manually verified email: ${email}`);
  
  res.json({ 
    success: true, 
    message: 'Email verified successfully',
    user: {
      email: user.email,
      emailVerified: user.emailVerified
    }
  });
});

// DEV ONLY: Delete a user account
app.delete('/api/dev/delete-user/:email', (req, res) => {
  const { email } = req.params;
  
  if (devUsers.has(email)) {
    devUsers.delete(email);
    saveDevData();
    console.log(`🗑️  Deleted user: ${email}`);
    res.json({ success: true, message: 'User deleted' });
  } else {
    res.status(404).json({ success: false, error: 'User not found' });
  }
});

// DEV ONLY: List all users
app.get('/api/dev/users', (req, res) => {
  const users = Array.from(devUsers.values()).map(user => ({
    email: user.email,
    name: user.name,
    role: user.role,
    emailVerified: user.emailVerified,
    createdAt: user.createdAt
  }));
  
  res.json({ 
    success: true, 
    count: users.length,
    users 
  });
});

// Mock analytics endpoint
app.post('/api/analytics', (req, res) => {
  console.log('Analytics Event:', req.body);
  res.json({ success: true });
});

// Dashboard stats endpoint
app.get('/dashboard/stats', (req, res) => {
  res.json({
    success: true,
    stats: {
      totalDevices: 3,
      activeDevices: 2,
      criticalAlerts: 1,
      averageWQI: 78,
      totalUsers: devUsers.size,
      pendingRequests: 2
    }
  });
});

// Water quality latest endpoint
app.get('/water-quality/latest', (req, res) => {
  res.json({
    success: true,
    reading: {
      deviceId: 'DEV-3421',
      timestamp: new Date().toISOString(),
      wqi: 78,
      readings: {
        pH: 7.2,
        turbidity: 1.5,
        tds: 150,
        temperature: 25.0
      },
      location: {
        latitude: 9.9312,
        longitude: 76.2673
      },
      diagnostics: {
        batteryLevel: 85,
        signalStrength: -65,
        sensorStatus: 'normal'
      },
      anomalyType: 'normal'
    }
  });
});

// Alerts endpoint
app.get('/alerts', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  
  const mockAlerts = [
    {
      id: 'alert-1',
      deviceId: 'DEV-3421',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      severity: 'warning',
      wqi: 65,
      message: 'Water quality below optimal range',
      acknowledged: false
    },
    {
      id: 'alert-2',
      deviceId: 'DEV-3422',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      severity: 'info',
      wqi: 72,
      message: 'Slight turbidity increase detected',
      acknowledged: true
    }
  ];
  
  res.json({
    success: true,
    alerts: mockAlerts.slice(0, limit),
    count: mockAlerts.length
  });
});

// Devices endpoint
app.get('/devices', (req, res) => {
  const mockDevices = [
    {
      deviceId: 'DEV-3421',
      name: 'Kitchen Sink',
      status: 'online',
      location: {
        latitude: 9.9312,
        longitude: 76.2673,
        address: '123 Main St, Kochi, Kerala'
      },
      lastReading: new Date().toISOString(),
      batteryLevel: 85,
      wqi: 78
    },
    {
      deviceId: 'DEV-3422',
      name: 'Main Water Line',
      status: 'online',
      location: {
        latitude: 9.9412,
        longitude: 76.2773,
        address: '123 Main St, Kochi, Kerala'
      },
      lastReading: new Date(Date.now() - 300000).toISOString(),
      batteryLevel: 92,
      wqi: 82
    },
    {
      deviceId: 'DEV-3423',
      name: 'Garden Tap',
      status: 'offline',
      location: {
        latitude: 9.9512,
        longitude: 76.2873,
        address: '123 Main St, Kochi, Kerala'
      },
      lastReading: new Date(Date.now() - 86400000).toISOString(),
      batteryLevel: 15,
      wqi: 0
    }
  ];
  
  res.json({
    success: true,
    devices: mockDevices,
    count: mockDevices.length
  });
});

// Device registration endpoint
app.post('/api/devices/register', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { device_id, name, location, water_source_type, pairing_code } = req.body;
  
  if (!device_id) {
    return res.status(400).json({ 
      success: false, 
      error: 'Device ID is required' 
    });
  }
  
  // Check if device already exists
  const existingDevices = devDevices.get(tokenData.userId) || [];
  if (existingDevices.some(d => d.device_id === device_id)) {
    return res.status(400).json({ 
      success: false, 
      error: 'Device with this ID already exists' 
    });
  }
  
  // Create new device
  const newDevice = {
    device_id,
    user_id: tokenData.userId,
    name: name || `Device ${device_id}`,
    location: location || 'Not specified',
    water_source_type: water_source_type || 'household',
    status: 'active',
    created_at: new Date().toISOString(),
    iot_thing_name: `iot-${device_id}`,
    certificate_arn: `arn:aws:iot:ap-south-1:123456789012:cert/${device_id}`,
    pairing_code: pairing_code || null
  };
  
  // Store device
  const userDevices = devDevices.get(tokenData.userId) || [];
  userDevices.push(newDevice);
  devDevices.set(tokenData.userId, userDevices);
  
  // Save to file
  saveDevData();
  
  console.log(`✅ Device registered: ${device_id} for user ${tokenData.email}`);
  
  // Create notification for device registration
  createNotification(
    tokenData.userId,
    'success',
    'Device Registered Successfully',
    `Your device "${name || device_id}" has been registered and is ready to use.`,
    'low'
  );
  
  res.json({
    success: true,
    message: 'Device registered successfully',
    device: newDevice
  });
});

// Get user's devices
app.get('/api/devices', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const userDevices = devDevices.get(tokenData.userId) || [];
  
  res.json({
    success: true,
    devices: userDevices,
    count: userDevices.length
  });
});

// Get single device
app.get('/api/devices/:deviceId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { deviceId } = req.params;
  const userDevices = devDevices.get(tokenData.userId) || [];
  const device = userDevices.find(d => d.device_id === deviceId);
  
  if (!device) {
    return res.status(404).json({ 
      success: false, 
      error: 'Device not found' 
    });
  }
  
  res.json({
    success: true,
    device
  });
});

// Update device
app.put('/api/devices/:deviceId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { deviceId } = req.params;
  const updates = req.body;
  
  const userDevices = devDevices.get(tokenData.userId) || [];
  const deviceIndex = userDevices.findIndex(d => d.device_id === deviceId);
  
  if (deviceIndex === -1) {
    return res.status(404).json({ 
      success: false, 
      error: 'Device not found' 
    });
  }
  
  // Update device
  userDevices[deviceIndex] = {
    ...userDevices[deviceIndex],
    ...updates,
    device_id: deviceId, // Don't allow changing device_id
    user_id: tokenData.userId, // Don't allow changing user_id
    updated_at: new Date().toISOString()
  };
  
  devDevices.set(tokenData.userId, userDevices);
  saveDevData();
  
  console.log(`✅ Device updated: ${deviceId}`);
  
  res.json({
    success: true,
    device: userDevices[deviceIndex]
  });
});

// Delete device
app.delete('/api/devices/:deviceId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { deviceId } = req.params;
  const userDevices = devDevices.get(tokenData.userId) || [];
  const filteredDevices = userDevices.filter(d => d.device_id !== deviceId);
  
  if (filteredDevices.length === userDevices.length) {
    return res.status(404).json({ 
      success: false, 
      error: 'Device not found' 
    });
  }
  
  devDevices.set(tokenData.userId, filteredDevices);
  saveDevData();
  
  console.log(`🗑️  Device deleted: ${deviceId}`);
  
  res.json({
    success: true,
    message: 'Device deleted successfully'
  });
});

// Persistent storage for development (survives server restarts)
const devUsers = new Map();
const validTokens = new Map();
const devDevices = new Map(); // Map of userId -> array of devices
const devNotifications = new Map(); // Map of userId -> array of notifications
const contactSubmissions = []; // Array of contact form submissions

// System settings storage
let systemSettings = {
  alertThresholds: {
    phMin: 6.5,
    phMax: 8.5,
    turbidityMax: 5.0,
    tdsMax: 500
  },
  notificationSettings: {
    emailEnabled: true,
    smsEnabled: true,
    pushEnabled: true
  },
  systemLimits: {
    maxDevicesPerUser: 10,
    dataRetentionDays: 90
  }
};

// System alerts storage
const systemAlerts = [];

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
      
      // Load devices
      if (data.devices) {
        Object.entries(data.devices).forEach(([userId, devices]) => {
          devDevices.set(userId, devices);
        });
        const totalDevices = Array.from(devDevices.values()).reduce((sum, devices) => sum + devices.length, 0);
        console.log(`✅ Loaded ${totalDevices} devices from storage`);
      }
      
      // Load system settings
      if (data.systemSettings) {
        systemSettings = data.systemSettings;
        console.log(`✅ Loaded system settings from storage`);
      }
      
      // Load system alerts
      if (data.systemAlerts) {
        systemAlerts.push(...data.systemAlerts);
        console.log(`✅ Loaded ${systemAlerts.length} system alerts from storage`);
      }
      
      // Load notifications
      if (data.notifications) {
        Object.entries(data.notifications).forEach(([userId, notifications]) => {
          devNotifications.set(userId, notifications);
        });
        const totalNotifications = Array.from(devNotifications.values()).reduce((sum, notifs) => sum + notifs.length, 0);
        console.log(`✅ Loaded ${totalNotifications} notifications from storage`);
      }
      
      // Load contact submissions
      if (data.contactSubmissions) {
        contactSubmissions.push(...data.contactSubmissions);
        console.log(`✅ Loaded ${contactSubmissions.length} contact submissions from storage`);
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
      devices: Object.fromEntries(devDevices),
      notifications: Object.fromEntries(devNotifications),
      contactSubmissions: contactSubmissions,
      systemSettings: systemSettings,
      systemAlerts: systemAlerts,
      lastUpdated: new Date().toISOString()
    };
    fs.writeFileSync(DEV_DATA_FILE, JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('⚠️  Error saving dev data:', error.message);
  }
}

// Load data on startup
loadDevData();

// Add sample alerts if none exist
if (systemAlerts.length === 0) {
  systemAlerts.push(
    {
      id: 'alert-1',
      message: 'System started successfully',
      priority: 'low',
      type: 'info',
      timestamp: new Date().toISOString(),
      read: false,
      createdBy: 'system'
    },
    {
      id: 'alert-2',
      message: 'High water quality detected in Device DEV-3421',
      priority: 'medium',
      type: 'warning',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      read: false,
      createdBy: 'system'
    },
    {
      id: 'alert-3',
      message: 'Critical: Device DEV-3422 offline for 2 hours',
      priority: 'high',
      type: 'error',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      read: false,
      createdBy: 'system'
    }
  );
  console.log('✅ Added sample system alerts');
}

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
  
  const newUserId = 'dev-user-' + Date.now();
  
  // Store user credentials for later login
  devUsers.set(email, {
    email,
    password,
    name,
    role,
    userId: newUserId,
    emailVerified: false, // Will be auto-verified after a short delay
    createdAt: new Date().toISOString()
  });
  
  // Save to file
  saveDevData();
  
  // Create welcome notification
  createNotification(
    newUserId,
    'success',
    'Welcome to AquaChain!',
    `Hi ${name}! Your account has been created successfully. Start by adding your first device to monitor water quality.`,
    'medium'
  );
  
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
    userId: newUserId,
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
      emailVerified: user.emailVerified,
      firstName: user.firstName || '',
      lastName: user.lastName || '',
      phone: user.phone || '',
      address: user.address || null,
      deviceIds: user.deviceIds || []
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
      emailVerified: user.emailVerified,
      profile: {
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        phone: user.phone || '',
        address: user.address || null
      }
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

// Profile management endpoints
const pendingOTPs = new Map(); // Store OTPs temporarily

// Request OTP for profile update
app.post('/api/profile/request-otp', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { email, changes } = req.body;
  const user = devUsers.get(tokenData.email);
  
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Generate 6-digit OTP
  const otp = Math.floor(100000 + Math.random() * 900000).toString();
  
  // Store OTP with expiration (5 minutes)
  pendingOTPs.set(tokenData.email, {
    otp,
    changes,
    expiresAt: Date.now() + 5 * 60 * 1000,
    attempts: 0
  });
  
  console.log(`📧 OTP for ${tokenData.email}: ${otp}`);
  console.log(`💡 Use this OTP to verify profile changes`);
  
  res.json({
    success: true,
    message: 'OTP sent to your email',
    // In dev mode, include OTP in response for testing
    devOtp: process.env.NODE_ENV === 'development' ? otp : undefined
  });
});

// Verify OTP and update profile
app.put('/api/profile/verify-and-update', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { otp, updates } = req.body;
  const user = devUsers.get(tokenData.email);
  
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Check OTP
  const pendingOTP = pendingOTPs.get(tokenData.email);
  
  if (!pendingOTP) {
    return res.status(400).json({ 
      success: false, 
      error: 'No OTP request found. Please request a new OTP.' 
    });
  }
  
  if (Date.now() > pendingOTP.expiresAt) {
    pendingOTPs.delete(tokenData.email);
    return res.status(400).json({ 
      success: false, 
      error: 'OTP expired. Please request a new one.' 
    });
  }
  
  if (pendingOTP.attempts >= 3) {
    pendingOTPs.delete(tokenData.email);
    return res.status(400).json({ 
      success: false, 
      error: 'Too many failed attempts. Please request a new OTP.' 
    });
  }
  
  if (pendingOTP.otp !== otp) {
    pendingOTP.attempts++;
    return res.status(400).json({ 
      success: false, 
      error: 'Invalid OTP. Please try again.',
      attemptsRemaining: 3 - pendingOTP.attempts
    });
  }
  
  // OTP verified, update profile
  const oldEmail = user.email;
  
  // Update user data
  if (updates.firstName) user.firstName = updates.firstName;
  if (updates.lastName) user.lastName = updates.lastName;
  if (updates.phone !== undefined) user.phone = updates.phone;
  if (updates.address !== undefined) user.address = updates.address;
  
  // Handle email change
  if (updates.email && updates.email !== oldEmail) {
    // Remove old email entry
    devUsers.delete(oldEmail);
    user.email = updates.email;
    devUsers.set(updates.email, user);
    
    // Update token data
    tokenData.email = updates.email;
    
    console.log(`✅ Email changed from ${oldEmail} to ${updates.email}`);
  }
  
  user.updatedAt = new Date().toISOString();
  
  // Clear OTP
  pendingOTPs.delete(tokenData.email);
  
  // Save to file
  saveDevData();
  
  console.log(`✅ Profile updated for ${user.email}`);
  
  // Create notification for profile update
  createNotification(
    tokenData.userId,
    'success',
    'Profile Updated',
    'Your profile information has been updated successfully.',
    'low'
  );
  
  res.json({
    success: true,
    message: 'Profile updated successfully',
    user: {
      userId: user.userId,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      phone: user.phone,
      address: user.address,
      role: user.role
    }
  });
});

// Update profile without OTP (for non-sensitive fields)
app.put('/api/profile/update', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const updates = req.body;
  const user = devUsers.get(tokenData.email);
  
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Only allow non-sensitive updates
  if (updates.firstName) user.firstName = updates.firstName;
  if (updates.lastName) user.lastName = updates.lastName;
  if (updates.address !== undefined) user.address = updates.address;
  
  user.updatedAt = new Date().toISOString();
  
  // Save to file
  saveDevData();
  
  console.log(`✅ Profile updated for ${user.email}`);
  
  res.json({
    success: true,
    message: 'Profile updated successfully',
    user: {
      userId: user.userId,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      phone: user.phone,
      address: user.address,
      role: user.role
    }
  });
});

// Notification endpoints
// Get user notifications
app.get('/api/notifications', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Get notifications for user (no default generation)
  const userNotifications = devNotifications.get(tokenData.userId) || [];
  
  res.json({
    success: true,
    notifications: userNotifications
  });
});

// Mark notification as read
app.put('/api/notifications/:notificationId/read', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { notificationId } = req.params;
  const userNotifications = devNotifications.get(tokenData.userId) || [];
  
  const notification = userNotifications.find(n => n.id === notificationId);
  if (notification) {
    notification.read = true;
    devNotifications.set(tokenData.userId, userNotifications);
    saveDevData();
  }
  
  res.json({
    success: true,
    message: 'Notification marked as read'
  });
});

// Mark all notifications as read
app.put('/api/notifications/read-all', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const userNotifications = devNotifications.get(tokenData.userId) || [];
  userNotifications.forEach(n => n.read = true);
  devNotifications.set(tokenData.userId, userNotifications);
  saveDevData();
  
  res.json({
    success: true,
    message: 'All notifications marked as read'
  });
});

// Delete notification
app.delete('/api/notifications/:notificationId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const { notificationId } = req.params;
  const userNotifications = devNotifications.get(tokenData.userId) || [];
  const filteredNotifications = userNotifications.filter(n => n.id !== notificationId);
  
  devNotifications.set(tokenData.userId, filteredNotifications);
  saveDevData();
  
  res.json({
    success: true,
    message: 'Notification deleted'
  });
});

// Get unread count
app.get('/api/notifications/unread-count', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const userNotifications = devNotifications.get(tokenData.userId) || [];
  const unreadCount = userNotifications.filter(n => !n.read).length;
  
  res.json({
    success: true,
    count: unreadCount
  });
});

// Helper function to create a notification
function createNotification(userId, type, title, message, priority = 'medium') {
  const notification = {
    id: `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type,
    title,
    message,
    timestamp: new Date().toISOString(),
    read: false,
    priority,
    userId
  };
  
  const userNotifications = devNotifications.get(userId) || [];
  userNotifications.unshift(notification); // Add to beginning
  devNotifications.set(userId, userNotifications);
  saveDevData();
  
  console.log(`📬 Notification created for user ${userId}: ${title}`);
  return notification;
}

// Contact form submission endpoint
app.post('/contact', (req, res) => {
  const { name, email, phone, message, inquiryType } = req.body;
  
  console.log('📧 Contact form submission received:');
  console.log(`   Name: ${name}`);
  console.log(`   Email: ${email}`);
  console.log(`   Phone: ${phone || 'Not provided'}`);
  console.log(`   Type: ${inquiryType}`);
  console.log(`   Message: ${message}`);
  
  // Generate submission ID
  const submissionId = `contact_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  
  // Store submission
  const submission = {
    id: submissionId,
    name,
    email,
    phone: phone || null,
    message,
    inquiryType,
    timestamp: new Date().toISOString(),
    status: 'new',
    read: false
  };
  
  contactSubmissions.unshift(submission); // Add to beginning
  saveDevData();
  
  console.log(`✅ Contact submission saved with ID: ${submissionId}`);
  
  res.json({
    message: 'Thank you for contacting us! We will get back to you soon.',
    submissionId
  });
});

// Create new user (Admin only)
app.post('/api/admin/users', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const adminUser = devUsers.get(tokenData.email);
  
  if (!adminUser || adminUser.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { firstName, lastName, email, phone, password, role, status } = req.body;
  
  // Validation
  if (!firstName || !lastName || !email || !password) {
    return res.status(400).json({ 
      success: false, 
      error: 'First name, last name, email, and password are required' 
    });
  }
  
  if (password.length < 8) {
    return res.status(400).json({ 
      success: false, 
      error: 'Password must be at least 8 characters' 
    });
  }
  
  // Check if email already exists
  if (devUsers.has(email)) {
    return res.status(400).json({ 
      success: false, 
      error: 'Email already exists' 
    });
  }
  
  // Create new user
  const userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  const newUser = {
    userId,
    email,
    password,
    firstName,
    lastName,
    phone: phone || '',
    role: role || 'consumer',
    status: status || 'active',
    emailVerified: true, // Admin-created users are pre-verified
    createdAt: new Date().toISOString(),
    createdBy: tokenData.userId
  };
  
  devUsers.set(email, newUser);
  saveDevData();
  
  console.log(`✅ Admin created new user: ${email} (${role || 'consumer'})`);
  
  // Create welcome notification
  createNotification(
    userId,
    'info',
    'Welcome to AquaChain!',
    `Your account has been created by an administrator. You can now log in and start using the system.`,
    'medium'
  );
  
  res.json({
    success: true,
    message: 'User created successfully',
    user: {
      userId: newUser.userId,
      email: newUser.email,
      firstName: newUser.firstName,
      lastName: newUser.lastName,
      phone: newUser.phone,
      role: newUser.role,
      status: newUser.status,
      createdAt: newUser.createdAt
    }
  });
});

// Get all users (Admin only)
app.get('/api/admin/users', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  // Get all users with device counts
  const allUsers = Array.from(devUsers.values()).map(u => {
    const userDevices = devDevices.get(u.userId) || [];
    return {
      userId: u.userId,
      email: u.email,
      name: u.name,
      firstName: u.firstName,
      lastName: u.lastName,
      phone: u.phone,
      role: u.role,
      emailVerified: u.emailVerified,
      createdAt: u.createdAt,
      lastLogin: u.lastLogin,
      deviceCount: userDevices.length
    };
  });
  
  res.json({
    success: true,
    users: allUsers,
    count: allUsers.length
  });
});

// Update user (Admin only)
app.put('/api/admin/users/:userId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const adminUser = devUsers.get(tokenData.email);
  
  if (!adminUser || adminUser.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { userId } = req.params;
  const { firstName, lastName, email, phone, role, status } = req.body;
  
  // Find user by userId
  let userToUpdate = null;
  let oldEmail = null;
  
  for (const [userEmail, userData] of devUsers.entries()) {
    if (userData.userId === userId) {
      userToUpdate = userData;
      oldEmail = userEmail;
      break;
    }
  }
  
  if (!userToUpdate) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Check if email is being changed and if new email already exists
  if (email && email !== oldEmail) {
    if (devUsers.has(email)) {
      return res.status(400).json({ 
        success: false, 
        error: 'Email already in use by another user' 
      });
    }
  }
  
  // Update user data
  if (firstName) userToUpdate.firstName = firstName;
  if (lastName) userToUpdate.lastName = lastName;
  if (phone !== undefined) userToUpdate.phone = phone;
  if (role) userToUpdate.role = role;
  if (status) userToUpdate.status = status;
  
  // Handle email change
  if (email && email !== oldEmail) {
    devUsers.delete(oldEmail);
    userToUpdate.email = email;
    devUsers.set(email, userToUpdate);
    
    // Update tokens
    for (const [token, data] of validTokens.entries()) {
      if (data.email === oldEmail) {
        data.email = email;
      }
    }
  }
  
  userToUpdate.updatedAt = new Date().toISOString();
  
  saveDevData();
  
  console.log(`✅ Admin updated user: ${userToUpdate.email} (${userId})`);
  
  res.json({
    success: true,
    message: 'User updated successfully',
    user: {
      userId: userToUpdate.userId,
      email: userToUpdate.email,
      firstName: userToUpdate.firstName,
      lastName: userToUpdate.lastName,
      phone: userToUpdate.phone,
      role: userToUpdate.role,
      status: userToUpdate.status
    }
  });
});

// Delete user (Admin only)
app.delete('/api/admin/users/:userId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { userId } = req.params;
  
  // Find user by userId
  let userToDelete = null;
  let userEmail = null;
  
  for (const [email, userData] of devUsers.entries()) {
    if (userData.userId === userId) {
      userToDelete = userData;
      userEmail = email;
      break;
    }
  }
  
  if (!userToDelete) {
    return res.status(404).json({ 
      success: false, 
      error: 'User not found' 
    });
  }
  
  // Prevent deleting yourself
  if (userId === tokenData.userId) {
    return res.status(400).json({ 
      success: false, 
      error: 'Cannot delete your own account' 
    });
  }
  
  // Delete user's devices
  devDevices.delete(userId);
  
  // Delete user's notifications
  devNotifications.delete(userId);
  
  // Delete user
  devUsers.delete(userEmail);
  
  // Invalidate user's tokens
  for (const [token, data] of validTokens.entries()) {
    if (data.userId === userId) {
      validTokens.delete(token);
    }
  }
  
  saveDevData();
  
  console.log(`🗑️  Admin deleted user: ${userEmail} (${userId})`);
  
  res.json({
    success: true,
    message: 'User deleted successfully'
  });
});

// Get all devices (Admin only)
app.get('/api/admin/devices', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  // Get all devices from all users
  const allDevices = [];
  for (const [userId, devices] of devDevices.entries()) {
    allDevices.push(...devices);
  }
  
  res.json({
    success: true,
    devices: allDevices,
    count: allDevices.length
  });
});

// Create new device (Admin only)
app.post('/api/admin/devices', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const adminUser = devUsers.get(tokenData.email);
  
  if (!adminUser || adminUser.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { deviceId, location, consumerId, consumerName, status } = req.body;
  
  // Validation
  if (!deviceId) {
    return res.status(400).json({ 
      success: false, 
      error: 'Device ID is required' 
    });
  }
  
  // Check if device ID already exists
  for (const [userId, devices] of devDevices.entries()) {
    if (devices.some(d => d.device_id === deviceId)) {
      return res.status(400).json({ 
        success: false, 
        error: 'Device ID already exists' 
      });
    }
  }
  
  // Determine which user to assign device to
  const assignToUserId = consumerId || tokenData.userId;
  
  // Get consumer name if consumerId provided
  let finalConsumerName = consumerName || 'Unassigned';
  if (consumerId) {
    // Find consumer user
    for (const [email, userData] of devUsers.entries()) {
      if (userData.userId === consumerId) {
        finalConsumerName = `${userData.firstName || ''} ${userData.lastName || ''}`.trim() || userData.name || email;
        break;
      }
    }
  }
  
  // Create new device
  const newDevice = {
    device_id: deviceId,
    user_id: assignToUserId,
    name: deviceId,
    location: location || '',
    consumerName: finalConsumerName,
    status: status || 'online',
    created_at: new Date().toISOString(),
    created_by: tokenData.userId
  };
  
  // Add device to the assigned user's devices
  const userDevices = devDevices.get(assignToUserId) || [];
  userDevices.push(newDevice);
  devDevices.set(assignToUserId, userDevices);
  
  saveDevData();
  
  console.log(`✅ Admin created new device: ${deviceId}`);
  
  res.json({
    success: true,
    message: 'Device created successfully',
    device: {
      deviceId: newDevice.device_id,
      location: newDevice.location,
      consumerName: newDevice.consumerName,
      status: newDevice.status,
      createdAt: newDevice.created_at
    }
  });
});

// Update device (Admin only)
app.put('/api/admin/devices/:deviceId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { deviceId } = req.params;
  const { status, location, consumerName } = req.body;
  
  // Find and update device
  let deviceUpdated = false;
  let updatedDevice = null;
  
  for (const [userId, devices] of devDevices.entries()) {
    const deviceIndex = devices.findIndex(d => d.device_id === deviceId);
    if (deviceIndex !== -1) {
      const device = devices[deviceIndex];
      
      // Update device fields
      if (status) device.status = status;
      if (location) device.location = location;
      if (consumerName) device.consumerName = consumerName;
      device.updated_at = new Date().toISOString();
      
      devices[deviceIndex] = device;
      devDevices.set(userId, devices);
      updatedDevice = device;
      deviceUpdated = true;
      break;
    }
  }
  
  if (!deviceUpdated) {
    return res.status(404).json({ 
      success: false, 
      error: 'Device not found' 
    });
  }
  
  saveDevData();
  
  console.log(`✅ Admin updated device: ${deviceId}`);
  
  res.json({
    success: true,
    message: 'Device updated successfully',
    device: updatedDevice
  });
});

// Delete device (Admin only)
app.delete('/api/admin/devices/:deviceId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { deviceId } = req.params;
  
  // Find and delete device from all users
  let deviceDeleted = false;
  for (const [userId, devices] of devDevices.entries()) {
    const filteredDevices = devices.filter(d => d.device_id !== deviceId);
    if (filteredDevices.length < devices.length) {
      devDevices.set(userId, filteredDevices);
      deviceDeleted = true;
    }
  }
  
  if (!deviceDeleted) {
    return res.status(404).json({ 
      success: false, 
      error: 'Device not found' 
    });
  }
  
  saveDevData();
  
  console.log(`🗑️  Admin deleted device: ${deviceId}`);
  
  res.json({
    success: true,
    message: 'Device deleted successfully'
  });
});

// Get system settings (Admin only)
app.get('/api/admin/settings', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  res.json({
    success: true,
    settings: systemSettings
  });
});

// Update system settings (Admin only)
app.put('/api/admin/settings', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const updates = req.body;
  
  // Update settings
  if (updates.alertThresholds) {
    systemSettings.alertThresholds = {
      ...systemSettings.alertThresholds,
      ...updates.alertThresholds
    };
  }
  
  if (updates.notificationSettings) {
    systemSettings.notificationSettings = {
      ...systemSettings.notificationSettings,
      ...updates.notificationSettings
    };
  }
  
  if (updates.systemLimits) {
    systemSettings.systemLimits = {
      ...systemSettings.systemLimits,
      ...updates.systemLimits
    };
  }
  
  saveDevData();
  
  console.log(`⚙️  Admin updated system settings`);
  
  res.json({
    success: true,
    message: 'Settings updated successfully',
    settings: systemSettings
  });
});

// Get system alerts (Admin only)
app.get('/api/admin/alerts', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  // Get alerts with statistics
  const criticalCount = systemAlerts.filter(a => a.priority === 'high').length;
  const warningCount = systemAlerts.filter(a => a.priority === 'medium').length;
  const infoCount = systemAlerts.filter(a => a.priority === 'low').length;
  
  res.json({
    success: true,
    alerts: systemAlerts,
    statistics: {
      critical: criticalCount,
      warning: warningCount,
      info: infoCount,
      total: systemAlerts.length
    }
  });
});

// Create system alert (Admin only)
app.post('/api/admin/alerts', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { message, priority, type } = req.body;
  
  const newAlert = {
    id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    message: message || 'System alert',
    priority: priority || 'low',
    type: type || 'info',
    timestamp: new Date().toISOString(),
    read: false,
    createdBy: tokenData.userId
  };
  
  systemAlerts.unshift(newAlert);
  
  // Keep only last 100 alerts
  if (systemAlerts.length > 100) {
    systemAlerts.splice(100);
  }
  
  saveDevData();
  
  console.log(`🔔 Admin created alert: ${message}`);
  
  res.json({
    success: true,
    message: 'Alert created successfully',
    alert: newAlert
  });
});

// Mark alert as read (Admin only)
app.put('/api/admin/alerts/:alertId/read', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { alertId } = req.params;
  const alert = systemAlerts.find(a => a.id === alertId);
  
  if (!alert) {
    return res.status(404).json({ 
      success: false, 
      error: 'Alert not found' 
    });
  }
  
  alert.read = true;
  saveDevData();
  
  res.json({
    success: true,
    message: 'Alert marked as read'
  });
});

// Mark all alerts as read (Admin only)
app.put('/api/admin/alerts/read-all', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  systemAlerts.forEach(alert => {
    alert.read = true;
  });
  
  saveDevData();
  
  console.log(`✅ Admin marked all alerts as read`);
  
  res.json({
    success: true,
    message: 'All alerts marked as read',
    count: systemAlerts.length
  });
});

// Delete alert (Admin only)
app.delete('/api/admin/alerts/:alertId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { alertId } = req.params;
  const alertIndex = systemAlerts.findIndex(a => a.id === alertId);
  
  if (alertIndex === -1) {
    return res.status(404).json({ 
      success: false, 
      error: 'Alert not found' 
    });
  }
  
  systemAlerts.splice(alertIndex, 1);
  saveDevData();
  
  console.log(`🗑️  Admin deleted alert: ${alertId}`);
  
  res.json({
    success: true,
    message: 'Alert deleted successfully'
  });
});

// Get all contact submissions (Admin only)
app.get('/api/admin/contact-submissions', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  res.json({
    success: true,
    submissions: contactSubmissions,
    count: contactSubmissions.length,
    unreadCount: contactSubmissions.filter(s => !s.read).length
  });
});

// Mark contact submission as read (Admin only)
app.put('/api/admin/contact-submissions/:submissionId/read', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { submissionId } = req.params;
  const submission = contactSubmissions.find(s => s.id === submissionId);
  
  if (!submission) {
    return res.status(404).json({ 
      success: false, 
      error: 'Submission not found' 
    });
  }
  
  submission.read = true;
  submission.status = 'read';
  saveDevData();
  
  res.json({
    success: true,
    message: 'Submission marked as read'
  });
});

// Delete contact submission (Admin only)
app.delete('/api/admin/contact-submissions/:submissionId', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }
  
  const user = devUsers.get(tokenData.email);
  
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ 
      success: false, 
      error: 'Admin access required' 
    });
  }
  
  const { submissionId } = req.params;
  const index = contactSubmissions.findIndex(s => s.id === submissionId);
  
  if (index === -1) {
    return res.status(404).json({ 
      success: false, 
      error: 'Submission not found' 
    });
  }
  
  contactSubmissions.splice(index, 1);
  saveDevData();
  
  res.json({
    success: true,
    message: 'Submission deleted'
  });
});

// Technician Tasks Endpoint
app.get('/api/v1/technician/tasks', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }

  // Mock technician tasks data
  const mockTasks = [
    {
      taskId: 'TASK-001',
      serviceRequestId: 'SR-001',
      deviceId: 'DEV-3421',
      consumerId: tokenData.userId,
      priority: 'high',
      status: 'assigned',
      title: 'pH sensor showing erratic readings',
      description: 'pH sensor showing erratic readings, possible calibration issue',
      location: {
        address: '123 Main St, San Francisco, CA 94102',
        coordinates: {
          lat: 37.7749,
          lng: -122.4194
        }
      },
      estimatedArrival: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Pro v2.1',
        serialNumber: 'AC-2024-3421'
      },
      consumer: {
        name: 'Jane Smith',
        phone: '+1-555-0123',
        email: 'jane.smith@email.com'
      },
      customerInfo: {
        name: 'Jane Smith',
        phone: '+1-555-0123',
        email: 'jane.smith@email.com'
      },
      notes: []
    },
    {
      taskId: 'TASK-002',
      serviceRequestId: 'SR-002',
      deviceId: 'DEV-3422',
      consumerId: tokenData.userId,
      priority: 'medium',
      status: 'accepted',
      title: 'Routine maintenance and calibration check',
      description: 'Routine maintenance and calibration check',
      location: {
        address: '456 Oak Ave, San Francisco, CA 94103',
        coordinates: {
          lat: 37.7849,
          lng: -122.4094
        }
      },
      estimatedArrival: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Standard v1.8',
        serialNumber: 'AC-2023-3422'
      },
      consumer: {
        name: 'Bob Johnson',
        phone: '+1-555-0456',
        email: 'bob.johnson@email.com'
      },
      customerInfo: {
        name: 'Bob Johnson',
        phone: '+1-555-0456',
        email: 'bob.johnson@email.com'
      },
      notes: []
    },
    {
      taskId: 'TASK-003',
      serviceRequestId: 'SR-003',
      deviceId: 'DEV-3423',
      consumerId: tokenData.userId,
      priority: 'low',
      status: 'in_progress',
      title: 'Temperature sensor calibration',
      description: 'Regular calibration check for temperature sensor',
      location: {
        address: '789 Pine St, San Francisco, CA 94104',
        coordinates: {
          lat: 37.7649,
          lng: -122.4294
        }
      },
      estimatedArrival: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Lite v1.5',
        serialNumber: 'AC-2023-3423'
      },
      consumer: {
        name: 'Alice Williams',
        phone: '+1-555-0789',
        email: 'alice.williams@email.com'
      },
      customerInfo: {
        name: 'Alice Williams',
        phone: '+1-555-0789',
        email: 'alice.williams@email.com'
      },
      notes: []
    }
  ];

  // Mock recent activities
  const recentActivities = [
    {
      id: 'activity-1',
      action: 'Completed task',
      task: 'Turbidity sensor cleaning',
      time: '2 hours ago'
    },
    {
      id: 'activity-2',
      action: 'Accepted task',
      task: 'Routine maintenance check',
      time: '5 hours ago'
    },
    {
      id: 'activity-3',
      action: 'Updated status',
      task: 'pH calibration',
      time: '1 day ago'
    }
  ];

  res.json({
    success: true,
    tasks: mockTasks,
    recentActivities: recentActivities,
    count: mockTasks.length
  });
});

// Update task status endpoint
app.put('/api/v1/technician/tasks/:taskId/status', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const { taskId } = req.params;
  const { status, note } = req.body;
  
  console.log(`Task ${taskId} status updated to: ${status}`);
  
  res.json({
    success: true,
    message: `Task status updated to ${status}`,
    taskId,
    status,
    note
  });
});

// Add task note endpoint
app.post('/api/v1/technician/tasks/:taskId/notes', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const { taskId } = req.params;
  const { content, type } = req.body;
  
  console.log(`Note added to task ${taskId}: ${content}`);
  
  res.json({
    success: true,
    message: 'Note added successfully',
    note: {
      id: `note-${Date.now()}`,
      taskId,
      content,
      type,
      timestamp: new Date().toISOString()
    }
  });
});

// Complete task endpoint
app.post('/api/v1/technician/tasks/:taskId/complete', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const { taskId } = req.params;
  const completionData = req.body;
  
  console.log(`Task ${taskId} completed:`, completionData.workPerformed);
  
  res.json({
    success: true,
    message: 'Task completed successfully',
    taskId,
    completedAt: new Date().toISOString()
  });
});

// NOTE: Catch-all moved to end of file after all route definitions

// Error handler (keeping here for now, will move to end)
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// WebSocket server for development
const wss = new WebSocket.Server({ server, path: '/ws' });

// Toggle to suppress WebSocket connection logs (useful in development with React StrictMode)
const SUPPRESS_WS_LOGS = true; // Set to false to see all WebSocket logs

wss.on('connection', (ws) => {
  if (!SUPPRESS_WS_LOGS) {
    console.log('WebSocket client connected');
  }
  
  // Send welcome message
  ws.send(JSON.stringify({ 
    type: 'welcome', 
    message: 'Connected to AquaChain Development WebSocket Server' 
  }));
  
  ws.on('message', (message) => {
    if (!SUPPRESS_WS_LOGS) {
      console.log('WebSocket message received:', message.toString());
    }
    // Echo back for testing
    ws.send(JSON.stringify({ 
      type: 'echo', 
      data: message.toString() 
    }));
  });
  
  ws.on('close', () => {
    if (!SUPPRESS_WS_LOGS) {
      console.log('WebSocket client disconnected');
    }
  });
});

// Initialize demo users if they don't exist
function initializeDemoUsers() {
  const demoUsers = [
    {
      email: 'demo@aquachain.com',
      password: 'demo1234',
      name: 'Demo Admin',
      role: 'admin'
    },
    {
      email: 'admin@aquachain.com',
      password: 'admin1234',
      name: 'Admin User',
      role: 'admin'
    },
    {
      email: 'tech@aquachain.com',
      password: 'tech1234',
      name: 'Demo Technician',
      role: 'technician'
    },
    {
      email: 'user@aquachain.com',
      password: 'user1234',
      name: 'Demo Consumer',
      role: 'consumer'
    }
  ];

  demoUsers.forEach(user => {
    if (!devUsers.has(user.email)) {
      const userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      devUsers.set(user.email, {
        userId,
        email: user.email,
        password: user.password,
        name: user.name,
        role: user.role,
        emailVerified: true,
        createdAt: new Date().toISOString()
      });
      
      // Create welcome notification for demo users
      if (user.role === 'admin') {
        createNotification(
          userId,
          'info',
          'Welcome to AquaChain Admin Dashboard',
          'You have full access to manage users, devices, and system settings.',
          'medium'
        );
      }
    }
  });

  console.log(`👥 Demo users available:`);
  console.log(`   - demo@aquachain.com / demo1234 (Admin)`);
  console.log(`   - admin@aquachain.com / admin1234 (Admin)`);
  console.log(`   - tech@aquachain.com / tech1234 (Technician)`);
  console.log(`   - user@aquachain.com / user1234 (Consumer)`);
}

// Technician Inventory Endpoints
// Get inventory
app.get('/api/v1/technician/inventory', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }

  // Mock inventory data (same as admin endpoint)
  const mockInventory = [
    // Sensors
    { partId: 'PART-001', name: 'pH Sensor', category: 'Sensors', quantity: 15, location: 'Warehouse A - Shelf 3', status: 'available', description: 'High-precision pH sensor for water quality monitoring', unitPrice: 3850, minQuantity: 5, lastRestocked: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-002', name: 'Turbidity Sensor', category: 'Sensors', quantity: 8, location: 'Warehouse A - Shelf 3', status: 'available', description: 'Optical turbidity sensor for measuring water clarity', unitPrice: 4400, minQuantity: 5, lastRestocked: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-003', name: 'TDS Sensor', category: 'Sensors', quantity: 12, location: 'Warehouse A - Shelf 3', status: 'available', description: 'Total Dissolved Solids sensor', unitPrice: 3250, minQuantity: 5, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-004', name: 'Temperature Sensor', category: 'Sensors', quantity: 20, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Digital temperature sensor (-40°C to 125°C)', unitPrice: 1340, minQuantity: 10, lastRestocked: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-013', name: 'Conductivity Sensor', category: 'Sensors', quantity: 10, location: 'Warehouse A - Shelf 3', status: 'available', description: 'EC sensor for measuring water conductivity', unitPrice: 4200, minQuantity: 5, lastRestocked: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-014', name: 'Dissolved Oxygen Sensor', category: 'Sensors', quantity: 6, location: 'Warehouse A - Shelf 3', status: 'available', description: 'DO sensor for oxygen level monitoring', unitPrice: 5500, minQuantity: 5, lastRestocked: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-015', name: 'Flow Sensor', category: 'Sensors', quantity: 14, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Water flow rate sensor (1-30 L/min)', unitPrice: 2800, minQuantity: 8, lastRestocked: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-016', name: 'Pressure Sensor', category: 'Sensors', quantity: 18, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Water pressure transducer (0-10 bar)', unitPrice: 3600, minQuantity: 10, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Filters
    { partId: 'PART-005', name: 'Sediment Filter', category: 'Filters', quantity: 25, location: 'Warehouse B - Shelf 1', status: 'available', description: '5-micron sediment filter cartridge', unitPrice: 1050, minQuantity: 10, lastRestocked: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-006', name: 'Carbon Filter', category: 'Filters', quantity: 18, location: 'Warehouse B - Shelf 1', status: 'available', description: 'Activated carbon filter for chlorine removal', unitPrice: 1590, minQuantity: 8, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-017', name: 'RO Membrane', category: 'Filters', quantity: 12, location: 'Warehouse B - Shelf 2', status: 'available', description: 'Reverse osmosis membrane 75 GPD', unitPrice: 2200, minQuantity: 6, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-018', name: 'UV Filter', category: 'Filters', quantity: 8, location: 'Warehouse B - Shelf 2', status: 'available', description: 'UV sterilization filter cartridge', unitPrice: 3200, minQuantity: 5, lastRestocked: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-019', name: 'Pre-Filter', category: 'Filters', quantity: 30, location: 'Warehouse B - Shelf 1', status: 'available', description: '20-micron pre-filter cartridge', unitPrice: 650, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Chemicals
    { partId: 'PART-007', name: 'Calibration Solution pH 7', category: 'Chemicals', quantity: 30, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 7.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-008', name: 'Calibration Solution pH 4', category: 'Chemicals', quantity: 28, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 4.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-020', name: 'Calibration Solution pH 10', category: 'Chemicals', quantity: 25, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 10.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-021', name: 'Cleaning Solution', category: 'Chemicals', quantity: 20, location: 'Warehouse C - Cabinet 3', status: 'available', description: 'Sensor cleaning solution (1L)', unitPrice: 950, minQuantity: 10, lastRestocked: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-022', name: 'Storage Solution', category: 'Chemicals', quantity: 22, location: 'Warehouse C - Cabinet 3', status: 'available', description: 'Electrode storage solution (250ml)', unitPrice: 550, minQuantity: 12, lastRestocked: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-023', name: 'Disinfectant', category: 'Chemicals', quantity: 15, location: 'Warehouse C - Cabinet 4', status: 'available', description: 'System disinfectant solution (2L)', unitPrice: 1200, minQuantity: 8, lastRestocked: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Tools
    { partId: 'PART-009', name: 'Multimeter', category: 'Tools', quantity: 5, location: 'Tool Room - Drawer 1', status: 'available', description: 'Digital multimeter for electrical testing', unitPrice: 3750, minQuantity: 3, lastRestocked: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-010', name: 'Screwdriver Set', category: 'Tools', quantity: 8, location: 'Tool Room - Drawer 2', status: 'available', description: 'Professional screwdriver set (12 pieces)', unitPrice: 2170, minQuantity: 5, lastRestocked: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-024', name: 'Wrench Set', category: 'Tools', quantity: 6, location: 'Tool Room - Drawer 3', status: 'available', description: 'Adjustable wrench set (3 pieces)', unitPrice: 1850, minQuantity: 4, lastRestocked: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-025', name: 'Pliers Set', category: 'Tools', quantity: 10, location: 'Tool Room - Drawer 2', status: 'available', description: 'Professional pliers set (5 pieces)', unitPrice: 1650, minQuantity: 5, lastRestocked: new Date(Date.now() - 18 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-026', name: 'Wire Stripper', category: 'Tools', quantity: 7, location: 'Tool Room - Drawer 1', status: 'available', description: 'Automatic wire stripper tool', unitPrice: 950, minQuantity: 5, lastRestocked: new Date(Date.now() - 22 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-027', name: 'Soldering Iron', category: 'Tools', quantity: 4, location: 'Tool Room - Drawer 4', status: 'available', description: 'Temperature controlled soldering station', unitPrice: 2800, minQuantity: 3, lastRestocked: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-028', name: 'Drill Set', category: 'Tools', quantity: 3, location: 'Tool Room - Cabinet 1', status: 'available', description: 'Cordless drill with bit set', unitPrice: 4500, minQuantity: 2, lastRestocked: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Parts
    { partId: 'PART-011', name: 'O-Ring Kit', category: 'Parts', quantity: 3, location: 'Warehouse A - Shelf 5', status: 'available', description: 'Assorted O-rings for sealing (100 pieces)', unitPrice: 1300, minQuantity: 5, lastRestocked: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-012', name: 'Replacement Gasket', category: 'Parts', quantity: 0, location: 'Warehouse A - Shelf 5', status: 'out_of_stock', description: 'Rubber gasket for filter housing', unitPrice: 500, minQuantity: 10, lastRestocked: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-029', name: 'Pipe Fittings', category: 'Parts', quantity: 45, location: 'Warehouse A - Shelf 6', status: 'available', description: 'Assorted pipe fittings (50 pieces)', unitPrice: 850, minQuantity: 20, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-030', name: 'Valve Assembly', category: 'Parts', quantity: 12, location: 'Warehouse A - Shelf 6', status: 'available', description: 'Solenoid valve assembly 12V DC', unitPrice: 1800, minQuantity: 6, lastRestocked: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-031', name: 'Power Supply', category: 'Parts', quantity: 8, location: 'Warehouse A - Shelf 7', status: 'available', description: '12V 2A power adapter', unitPrice: 650, minQuantity: 5, lastRestocked: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-032', name: 'Cable Kit', category: 'Parts', quantity: 20, location: 'Warehouse A - Shelf 7', status: 'available', description: 'Sensor cable kit with connectors (5m)', unitPrice: 450, minQuantity: 10, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-033', name: 'Mounting Bracket', category: 'Parts', quantity: 25, location: 'Warehouse A - Shelf 8', status: 'available', description: 'Universal sensor mounting bracket', unitPrice: 350, minQuantity: 15, lastRestocked: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-034', name: 'Battery Pack', category: 'Parts', quantity: 2, location: 'Warehouse A - Shelf 7', status: 'available', description: 'Rechargeable Li-ion battery pack', unitPrice: 2200, minQuantity: 5, lastRestocked: new Date(Date.now() - 50 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-035', name: 'Display Module', category: 'Parts', quantity: 6, location: 'Warehouse A - Shelf 8', status: 'available', description: 'LCD display module 16x2', unitPrice: 850, minQuantity: 5, lastRestocked: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString() }
  ];

  res.json({
    success: true,
    inventory: mockInventory,
    count: mockInventory.length
  });
});

// Checkout inventory item
app.post('/api/v1/technician/inventory/checkout', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }

  const { partId, quantity, taskId } = req.body;
  
  if (!partId || !quantity || quantity <= 0) {
    return res.status(400).json({
      success: false,
      error: 'Invalid checkout request'
    });
  }

  console.log(`✅ Checkout: ${quantity}x ${partId} by ${tokenData.email}${taskId ? ` for task ${taskId}` : ''}`);
  
  res.json({
    success: true,
    message: `Successfully checked out ${quantity} item(s)`,
    checkout: {
      partId,
      quantity,
      taskId,
      technicianId: tokenData.userId,
      timestamp: new Date().toISOString()
    }
  });
});

// Return inventory item
app.post('/api/v1/technician/inventory/return', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }

  const { partId, quantity } = req.body;
  
  if (!partId || !quantity || quantity <= 0) {
    return res.status(400).json({
      success: false,
      error: 'Invalid return request'
    });
  }

  console.log(`✅ Return: ${quantity}x ${partId} by ${tokenData.email}`);
  
  res.json({
    success: true,
    message: `Successfully returned ${quantity} item(s)`,
    return: {
      partId,
      quantity,
      technicianId: tokenData.userId,
      timestamp: new Date().toISOString()
    }
  });
});

// Request restock
app.post('/api/v1/technician/inventory/request-restock', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      error: 'Authentication required' 
    });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ 
      success: false, 
      error: 'Invalid or expired token' 
    });
  }

  const { partId, partName, quantity, reason, currentStock } = req.body;
  
  if (!partId || !quantity || quantity <= 0) {
    return res.status(400).json({
      success: false,
      error: 'Invalid restock request'
    });
  }

  const user = devUsers.get(tokenData.email);
  const technicianName = user ? `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.email : tokenData.email;

  console.log(`📦 Restock Request: ${quantity}x ${partName} (${partId}) by ${technicianName}`);
  console.log(`   Reason: ${reason}`);
  console.log(`   Current Stock: ${currentStock}`);
  
  // Create notification for all admins
  devUsers.forEach((user, email) => {
    if (user.role === 'admin') {
      createNotification(
        user.userId,
        'warning',
        'Inventory Restock Request',
        `${technicianName} requested ${quantity}x ${partName}. Current stock: ${currentStock}. Reason: ${reason}`,
        'high'
      );
    }
  });
  
  res.json({
    success: true,
    message: `Restock request sent to admin`,
    request: {
      partId,
      partName,
      quantity,
      reason,
      currentStock,
      technicianId: tokenData.userId,
      technicianName,
      timestamp: new Date().toISOString()
    }
  });
});

// Admin Inventory Management Endpoints
// Get all inventory (admin)
app.get('/api/admin/inventory', (req, res) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  
  if (!tokenData) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Admin access required' });
  }

  // Return same mock inventory as technician endpoint
  const mockInventory = [
    // Sensors
    { partId: 'PART-001', name: 'pH Sensor', category: 'Sensors', quantity: 15, location: 'Warehouse A - Shelf 3', status: 'available', description: 'High-precision pH sensor for water quality monitoring', unitPrice: 3850, minQuantity: 5, lastRestocked: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-002', name: 'Turbidity Sensor', category: 'Sensors', quantity: 8, location: 'Warehouse A - Shelf 3', status: 'available', description: 'Optical turbidity sensor for measuring water clarity', unitPrice: 4400, minQuantity: 5, lastRestocked: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-003', name: 'TDS Sensor', category: 'Sensors', quantity: 12, location: 'Warehouse A - Shelf 3', status: 'available', description: 'Total Dissolved Solids sensor', unitPrice: 3250, minQuantity: 5, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-004', name: 'Temperature Sensor', category: 'Sensors', quantity: 20, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Digital temperature sensor (-40°C to 125°C)', unitPrice: 1340, minQuantity: 10, lastRestocked: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-013', name: 'Conductivity Sensor', category: 'Sensors', quantity: 10, location: 'Warehouse A - Shelf 3', status: 'available', description: 'EC sensor for measuring water conductivity', unitPrice: 4200, minQuantity: 5, lastRestocked: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-014', name: 'Dissolved Oxygen Sensor', category: 'Sensors', quantity: 6, location: 'Warehouse A - Shelf 3', status: 'available', description: 'DO sensor for oxygen level monitoring', unitPrice: 5500, minQuantity: 5, lastRestocked: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-015', name: 'Flow Sensor', category: 'Sensors', quantity: 14, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Water flow rate sensor (1-30 L/min)', unitPrice: 2800, minQuantity: 8, lastRestocked: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-016', name: 'Pressure Sensor', category: 'Sensors', quantity: 18, location: 'Warehouse A - Shelf 4', status: 'available', description: 'Water pressure transducer (0-10 bar)', unitPrice: 3600, minQuantity: 10, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Filters
    { partId: 'PART-005', name: 'Sediment Filter', category: 'Filters', quantity: 25, location: 'Warehouse B - Shelf 1', status: 'available', description: '5-micron sediment filter cartridge', unitPrice: 1050, minQuantity: 10, lastRestocked: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-006', name: 'Carbon Filter', category: 'Filters', quantity: 18, location: 'Warehouse B - Shelf 1', status: 'available', description: 'Activated carbon filter for chlorine removal', unitPrice: 1590, minQuantity: 8, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-017', name: 'RO Membrane', category: 'Filters', quantity: 12, location: 'Warehouse B - Shelf 2', status: 'available', description: 'Reverse osmosis membrane 75 GPD', unitPrice: 2200, minQuantity: 6, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-018', name: 'UV Filter', category: 'Filters', quantity: 8, location: 'Warehouse B - Shelf 2', status: 'available', description: 'UV sterilization filter cartridge', unitPrice: 3200, minQuantity: 5, lastRestocked: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-019', name: 'Pre-Filter', category: 'Filters', quantity: 30, location: 'Warehouse B - Shelf 1', status: 'available', description: '20-micron pre-filter cartridge', unitPrice: 650, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Chemicals
    { partId: 'PART-007', name: 'Calibration Solution pH 7', category: 'Chemicals', quantity: 30, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 7.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-008', name: 'Calibration Solution pH 4', category: 'Chemicals', quantity: 28, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 4.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-020', name: 'Calibration Solution pH 10', category: 'Chemicals', quantity: 25, location: 'Warehouse C - Cabinet 2', status: 'available', description: 'pH 10.0 calibration buffer solution (500ml)', unitPrice: 750, minQuantity: 15, lastRestocked: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-021', name: 'Cleaning Solution', category: 'Chemicals', quantity: 20, location: 'Warehouse C - Cabinet 3', status: 'available', description: 'Sensor cleaning solution (1L)', unitPrice: 950, minQuantity: 10, lastRestocked: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-022', name: 'Storage Solution', category: 'Chemicals', quantity: 22, location: 'Warehouse C - Cabinet 3', status: 'available', description: 'Electrode storage solution (250ml)', unitPrice: 550, minQuantity: 12, lastRestocked: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-023', name: 'Disinfectant', category: 'Chemicals', quantity: 15, location: 'Warehouse C - Cabinet 4', status: 'available', description: 'System disinfectant solution (2L)', unitPrice: 1200, minQuantity: 8, lastRestocked: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Tools
    { partId: 'PART-009', name: 'Multimeter', category: 'Tools', quantity: 5, location: 'Tool Room - Drawer 1', status: 'available', description: 'Digital multimeter for electrical testing', unitPrice: 3750, minQuantity: 3, lastRestocked: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-010', name: 'Screwdriver Set', category: 'Tools', quantity: 8, location: 'Tool Room - Drawer 2', status: 'available', description: 'Professional screwdriver set (12 pieces)', unitPrice: 2170, minQuantity: 5, lastRestocked: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-024', name: 'Wrench Set', category: 'Tools', quantity: 6, location: 'Tool Room - Drawer 3', status: 'available', description: 'Adjustable wrench set (3 pieces)', unitPrice: 1850, minQuantity: 4, lastRestocked: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-025', name: 'Pliers Set', category: 'Tools', quantity: 10, location: 'Tool Room - Drawer 2', status: 'available', description: 'Professional pliers set (5 pieces)', unitPrice: 1650, minQuantity: 5, lastRestocked: new Date(Date.now() - 18 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-026', name: 'Wire Stripper', category: 'Tools', quantity: 7, location: 'Tool Room - Drawer 1', status: 'available', description: 'Automatic wire stripper tool', unitPrice: 950, minQuantity: 5, lastRestocked: new Date(Date.now() - 22 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-027', name: 'Soldering Iron', category: 'Tools', quantity: 4, location: 'Tool Room - Drawer 4', status: 'available', description: 'Temperature controlled soldering station', unitPrice: 2800, minQuantity: 3, lastRestocked: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-028', name: 'Drill Set', category: 'Tools', quantity: 3, location: 'Tool Room - Cabinet 1', status: 'available', description: 'Cordless drill with bit set', unitPrice: 4500, minQuantity: 2, lastRestocked: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString() },
    
    // Parts
    { partId: 'PART-011', name: 'O-Ring Kit', category: 'Parts', quantity: 3, location: 'Warehouse A - Shelf 5', status: 'available', description: 'Assorted O-rings for sealing (100 pieces)', unitPrice: 1300, minQuantity: 5, lastRestocked: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-012', name: 'Replacement Gasket', category: 'Parts', quantity: 0, location: 'Warehouse A - Shelf 5', status: 'out_of_stock', description: 'Rubber gasket for filter housing', unitPrice: 500, minQuantity: 10, lastRestocked: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-029', name: 'Pipe Fittings', category: 'Parts', quantity: 45, location: 'Warehouse A - Shelf 6', status: 'available', description: 'Assorted pipe fittings (50 pieces)', unitPrice: 850, minQuantity: 20, lastRestocked: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-030', name: 'Valve Assembly', category: 'Parts', quantity: 12, location: 'Warehouse A - Shelf 6', status: 'available', description: 'Solenoid valve assembly 12V DC', unitPrice: 1800, minQuantity: 6, lastRestocked: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-031', name: 'Power Supply', category: 'Parts', quantity: 8, location: 'Warehouse A - Shelf 7', status: 'available', description: '12V 2A power adapter', unitPrice: 650, minQuantity: 5, lastRestocked: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-032', name: 'Cable Kit', category: 'Parts', quantity: 20, location: 'Warehouse A - Shelf 7', status: 'available', description: 'Sensor cable kit with connectors (5m)', unitPrice: 450, minQuantity: 10, lastRestocked: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-033', name: 'Mounting Bracket', category: 'Parts', quantity: 25, location: 'Warehouse A - Shelf 8', status: 'available', description: 'Universal sensor mounting bracket', unitPrice: 350, minQuantity: 15, lastRestocked: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-034', name: 'Battery Pack', category: 'Parts', quantity: 2, location: 'Warehouse A - Shelf 7', status: 'available', description: 'Rechargeable Li-ion battery pack', unitPrice: 2200, minQuantity: 5, lastRestocked: new Date(Date.now() - 50 * 24 * 60 * 60 * 1000).toISOString() },
    { partId: 'PART-035', name: 'Display Module', category: 'Parts', quantity: 6, location: 'Warehouse A - Shelf 8', status: 'available', description: 'LCD display module 16x2', unitPrice: 850, minQuantity: 5, lastRestocked: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString() }
  ];

  res.json({ success: true, inventory: mockInventory, count: mockInventory.length });
});

// Add inventory item (admin)
app.post('/api/admin/inventory', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  if (!tokenData) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Admin access required' });
  }

  const item = req.body;
  console.log(`✅ Admin ${user.email} added inventory item: ${item.name}`);
  
  res.json({ success: true, message: 'Item added successfully', item });
});

// Update inventory item (admin)
app.put('/api/admin/inventory/:partId', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  if (!tokenData) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Admin access required' });
  }

  const { partId } = req.params;
  const updates = req.body;
  console.log(`✅ Admin ${user.email} updated inventory item: ${partId}`);
  
  res.json({ success: true, message: 'Item updated successfully', partId, updates });
});

// Restock inventory item (admin)
app.post('/api/admin/inventory/:partId/restock', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  if (!tokenData) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Admin access required' });
  }

  const { partId } = req.params;
  const { quantity } = req.body;
  console.log(`✅ Admin ${user.email} restocked ${quantity}x ${partId}`);
  
  res.json({ success: true, message: `Restocked ${quantity} items`, partId, quantity });
});

// Delete inventory item (admin)
app.delete('/api/admin/inventory/:partId', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authentication required' });
  }
  
  const token = authHeader.substring(7);
  const tokenData = validTokens.get(token);
  if (!tokenData) {
    return res.status(401).json({ success: false, error: 'Invalid token' });
  }
  
  const user = devUsers.get(tokenData.email);
  if (!user || user.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Admin access required' });
  }

  const { partId } = req.params;
  console.log(`✅ Admin ${user.email} deleted inventory item: ${partId}`);
  
  res.json({ success: true, message: 'Item deleted successfully', partId });
});

// Catch-all for missing endpoints (MUST BE LAST!)
app.use('*', (req, res) => {
  console.log(`Missing endpoint: ${req.method} ${req.originalUrl}`);
  res.status(404).json({ 
    error: 'Endpoint not found', 
    method: req.method, 
    path: req.originalUrl,
    message: 'This is a development server - endpoint not implemented'
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 AquaChain Development Server running on http://localhost:${PORT}`);
  console.log(`📊 RUM endpoint: http://localhost:${PORT}/api/rum`);
  console.log(`🔍 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📈 Analytics: http://localhost:${PORT}/api/analytics`);
  console.log(`🔌 WebSocket: ws://localhost:${PORT}/ws`);
  console.log('');
  
  // Initialize demo users
  initializeDemoUsers();
  
  // Save initial state
  saveDevData();
});

module.exports = app;