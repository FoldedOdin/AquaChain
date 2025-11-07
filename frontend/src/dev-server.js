
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
      
      // Load notifications
      if (data.notifications) {
        Object.entries(data.notifications).forEach(([userId, notifications]) => {
          devNotifications.set(userId, notifications);
        });
        const totalNotifications = Array.from(devNotifications.values()).reduce((sum, notifs) => sum + notifs.length, 0);
        console.log(`✅ Loaded ${totalNotifications} notifications from storage`);
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
        latitude: 37.7749,
        longitude: -122.4194,
        address: '123 Main St, San Francisco, CA 94102'
      },
      estimatedArrival: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Pro v2.1',
        serialNumber: 'AC-2024-3421'
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
        latitude: 37.7849,
        longitude: -122.4094,
        address: '456 Oak Ave, San Francisco, CA 94103'
      },
      estimatedArrival: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Standard v1.8',
        serialNumber: 'AC-2023-3422'
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
        latitude: 37.7649,
        longitude: -122.4294,
        address: '789 Pine St, San Francisco, CA 94104'
      },
      estimatedArrival: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(),
      assignedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
      deviceInfo: {
        model: 'AquaChain Lite v1.5',
        serialNumber: 'AC-2023-3423'
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
      devUsers.set(user.email, {
        userId: `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        email: user.email,
        password: user.password,
        name: user.name,
        role: user.role,
        emailVerified: true,
        createdAt: new Date().toISOString()
      });
    }
  });

  console.log(`👥 Demo users available:`);
  console.log(`   - demo@aquachain.com / demo1234 (Admin)`);
  console.log(`   - admin@aquachain.com / admin1234 (Admin)`);
  console.log(`   - tech@aquachain.com / tech1234 (Technician)`);
  console.log(`   - user@aquachain.com / user1234 (Consumer)`);
}

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