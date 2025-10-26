# 🎯 Dashboard Quick Reference

## 🏠 Consumer Dashboard

**Purpose:** Monitor personal water quality

**Key Metrics:**
- Water Quality Index (0-100)
- pH, Turbidity, TDS, Temperature
- Device status
- Alert count

**Main Actions:**
- View real-time readings
- Check alerts
- Export data
- Manage settings

**Access:** `/dashboard/consumer`

---

## 🔧 Technician Dashboard

**Purpose:** Manage maintenance tasks

**Key Metrics:**
- Total tasks
- Completed tasks
- Pending tasks

**Main Actions:**
- Accept tasks
- Complete tasks
- Add notes
- Create maintenance reports
- Call customers
- Get directions

**Access:** `/dashboard/technician`

---

## 👨‍💼 Admin Dashboard

**Purpose:** System oversight and management

**Key Metrics:**
- Total devices
- Total users
- System health
- Active alerts

**Main Actions:**
- Manage users
- View device fleet
- Access analytics
- Export system data
- Configure settings

**Access:** `/dashboard/admin`

---

## 🎨 Color Themes

| Role | Primary Color | Badge Color |
|------|--------------|-------------|
| Consumer | Aqua (#06B6D4) | Green |
| Technician | Blue (#3B82F6) | Blue |
| Admin | Purple (#9333EA) | Purple |

---

## 🔐 Access Control

| Feature | Consumer | Technician | Admin |
|---------|----------|------------|-------|
| Own Water Quality | ✅ | ❌ | ✅ |
| All Water Quality | ❌ | ❌ | ✅ |
| Tasks | ❌ | ✅ | ⚠️ |
| Users | ❌ | ❌ | ✅ |
| System Settings | ❌ | ❌ | ✅ |

---

## 📊 Data Refresh Rates

- **Real-time Updates:** Instant (WebSocket)
- **Dashboard Data:** 60 seconds
- **Alerts:** 30 seconds
- **Devices:** 120 seconds

---

## 🚀 Quick Start

1. **Login** at `/`
2. **Auto-redirect** to role-specific dashboard
3. **View data** on main screen
4. **Click settings** for profile/preferences
5. **Click export** for data download

---

**Full Documentation:** `DASHBOARD_FEATURES_GUIDE.md`
