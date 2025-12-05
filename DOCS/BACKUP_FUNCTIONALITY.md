# Backup Functionality - Complete System Backup

## 📦 What Gets Backed Up

The backup feature creates a **comprehensive snapshot** of your entire AquaChain system.

---

## 🗂️ Backup Contents

### 1. **Users Data** 👥
Complete user information including:
- User ID
- Email address
- Role (admin, technician, consumer)
- Status (active, pending, inactive)
- Profile information (name, phone)
- Account creation date
- Last login timestamp
- Device count per user

**Example:**
```json
{
  "userId": "user-123",
  "email": "john@example.com",
  "role": "consumer",
  "status": "active",
  "profile": {
    "firstName": "John",
    "lastName": "Doe",
    "phone": "+1-555-0123"
  },
  "createdAt": "2025-01-15T10:30:00Z",
  "lastLogin": "2025-12-05T08:45:00Z",
  "deviceCount": 2
}
```

---

### 2. **Devices Data** 🖥️
Complete device registry including:
- Device ID
- Status (online, warning, offline)
- Location information
- Assigned consumer name and ID
- Current Water Quality Index (WQI)
- Battery level
- Last seen timestamp

**Example:**
```json
{
  "deviceId": "DEV-3421",
  "status": "online",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "address": "123 Main St, San Francisco, CA"
  },
  "consumerName": "John Doe",
  "consumerId": "user-123",
  "currentWQI": 85,
  "batteryLevel": 92,
  "lastSeen": "2025-12-05T10:30:00Z"
}
```

---

### 3. **System Settings** ⚙️
All system configuration including:

#### Alert Thresholds:
- pH Min/Max values
- Turbidity maximum (NTU)
- TDS maximum (ppm)

#### Notification Settings:
- Email notifications (enabled/disabled)
- SMS notifications (enabled/disabled)
- Push notifications (enabled/disabled)

#### System Limits:
- Max devices per user
- Data retention period (days)

**Example:**
```json
{
  "alertThresholds": {
    "phMin": 6.5,
    "phMax": 8.5,
    "turbidityMax": 5.0,
    "tdsMax": 500
  },
  "notificationSettings": {
    "emailEnabled": true,
    "smsEnabled": true,
    "pushEnabled": true
  },
  "systemLimits": {
    "maxDevicesPerUser": 10,
    "dataRetentionDays": 90
  }
}
```

---

### 4. **System Alerts** 🔔
All system alerts including:
- Alert ID
- Message content
- Priority level (high, medium, low)
- Alert type (error, warning, info)
- Timestamp
- Read status
- Creator ID

**Example:**
```json
{
  "id": "alert-123",
  "message": "Critical: Device DEV-3422 offline for 2 hours",
  "priority": "high",
  "type": "error",
  "timestamp": "2025-12-05T08:30:00Z",
  "read": false,
  "createdBy": "system"
}
```

---

## 📊 Backup File Structure

```json
{
  "metadata": {
    "timestamp": "2025-12-05T10:30:00.000Z",
    "version": "1.0.0",
    "backupType": "full",
    "generatedBy": "admin@aquachain.com"
  },
  "statistics": {
    "totalUsers": 25,
    "totalDevices": 50,
    "totalAlerts": 15,
    "usersByRole": {
      "admin": 2,
      "technician": 5,
      "consumer": 18
    },
    "devicesByStatus": {
      "online": 45,
      "warning": 3,
      "offline": 2
    }
  },
  "data": {
    "users": [...],
    "devices": [...],
    "systemSettings": {...},
    "alerts": [...]
  }
}
```

---

## 🔄 Backup Process

### Step-by-Step:

1. **Preparing backup** (0.5s)
   - Initialize backup process
   - Validate authentication

2. **Backing up users** (0.8s)
   - Fetch all user records
   - Include profile information
   - Calculate device counts

3. **Backing up devices** (0.8s)
   - Fetch all device records
   - Include location data
   - Include status information

4. **Backing up system settings** (API call)
   - Fetch from `/api/admin/settings`
   - Include all configuration

5. **Backing up alerts** (API call)
   - Fetch from `/api/admin/alerts`
   - Include all alert history

6. **Finalizing backup** (0.5s)
   - Compile all data
   - Generate statistics
   - Create JSON file

7. **Download** (instant)
   - Create blob
   - Trigger download
   - Filename: `aquachain-backup-YYYY-MM-DD.json`

---

## 💾 File Details

### Filename Format:
```
aquachain-backup-2025-12-05.json
```

### File Type:
- **Format:** JSON
- **Encoding:** UTF-8
- **MIME Type:** application/json

### File Size:
Varies based on data volume:
- Small system (10 users, 20 devices): ~50 KB
- Medium system (100 users, 200 devices): ~500 KB
- Large system (1000 users, 2000 devices): ~5 MB

---

## 🎯 Use Cases

### 1. **Disaster Recovery**
- Restore system after failure
- Recover from data corruption
- Migrate to new server

### 2. **System Migration**
- Move to new infrastructure
- Upgrade to new version
- Clone production to staging

### 3. **Compliance & Auditing**
- Regulatory compliance
- Data retention requirements
- Audit trail documentation

### 4. **Testing & Development**
- Create test datasets
- Populate development environments
- Performance testing

### 5. **Regular Maintenance**
- Scheduled backups
- Before major updates
- Pre-deployment snapshots

---

## 🔒 Security Considerations

### What's Included:
- ✅ User profiles (names, emails, roles)
- ✅ Device information
- ✅ System configuration
- ✅ Alert history

### What's NOT Included:
- ❌ User passwords (security)
- ❌ Authentication tokens
- ❌ API keys
- ❌ Sensitive credentials

### Best Practices:
1. **Store securely** - Encrypt backup files
2. **Access control** - Limit who can download
3. **Regular backups** - Schedule automated backups
4. **Test restores** - Verify backup integrity
5. **Retention policy** - Keep multiple versions

---

## 📈 Statistics Included

The backup includes comprehensive statistics:

### User Statistics:
- Total users
- Users by role (admin, technician, consumer)
- Active vs inactive users

### Device Statistics:
- Total devices
- Devices by status (online, warning, offline)
- Devices per user

### Alert Statistics:
- Total alerts
- Alerts by priority
- Unread alerts

---

## 🚀 Future Enhancements

### Planned Features:
- [ ] **Incremental backups** - Only changed data
- [ ] **Scheduled backups** - Automatic daily/weekly
- [ ] **Cloud storage** - Upload to S3/Azure
- [ ] **Backup encryption** - AES-256 encryption
- [ ] **Restore functionality** - Import backup files
- [ ] **Backup history** - Track all backups
- [ ] **Compression** - Reduce file size
- [ ] **Email delivery** - Send backup via email

---

## 📝 Example Backup File

```json
{
  "metadata": {
    "timestamp": "2025-12-05T10:30:00.000Z",
    "version": "1.0.0",
    "backupType": "full",
    "generatedBy": "admin@aquachain.com"
  },
  "statistics": {
    "totalUsers": 3,
    "totalDevices": 2,
    "totalAlerts": 3,
    "usersByRole": {
      "admin": 1,
      "technician": 0,
      "consumer": 2
    },
    "devicesByStatus": {
      "online": 1,
      "warning": 0,
      "offline": 1
    }
  },
  "data": {
    "users": [
      {
        "userId": "user-001",
        "email": "admin@aquachain.com",
        "role": "admin",
        "status": "active",
        "profile": {
          "firstName": "Admin",
          "lastName": "User",
          "phone": "+1-555-0100"
        },
        "createdAt": "2025-01-01T00:00:00Z",
        "lastLogin": "2025-12-05T10:00:00Z",
        "deviceCount": 0
      }
    ],
    "devices": [
      {
        "deviceId": "DEV-3421",
        "status": "online",
        "location": {
          "address": "123 Main St"
        },
        "consumerName": "John Doe",
        "currentWQI": 85,
        "batteryLevel": 92,
        "lastSeen": "2025-12-05T10:30:00Z"
      }
    ],
    "systemSettings": {
      "alertThresholds": {
        "phMin": 6.5,
        "phMax": 8.5,
        "turbidityMax": 5.0,
        "tdsMax": 500
      },
      "notificationSettings": {
        "emailEnabled": true,
        "smsEnabled": true,
        "pushEnabled": true
      },
      "systemLimits": {
        "maxDevicesPerUser": 10,
        "dataRetentionDays": 90
      }
    },
    "alerts": [
      {
        "id": "alert-1",
        "message": "System started successfully",
        "priority": "low",
        "type": "info",
        "timestamp": "2025-12-05T10:00:00Z",
        "read": false,
        "createdBy": "system"
      }
    ]
  }
}
```

---

## ✅ Verification

After backup, verify:
1. ✅ File downloaded successfully
2. ✅ File size is reasonable
3. ✅ JSON is valid (can be opened in text editor)
4. ✅ All sections present (metadata, statistics, data)
5. ✅ User count matches dashboard
6. ✅ Device count matches dashboard

---

**Last Updated:** December 5, 2025
**Status:** ✅ Production Ready - Full System Backup
