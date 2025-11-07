# Admin Dashboard Enhancement Plan

## Overview
Enhance the Admin Dashboard with improved UI, tabbed navigation, and comprehensive management features.

## Key Features to Add

### 1. Tabbed Navigation
Add tabs for different views:
- **Overview** - System metrics and recent activity
- **Devices** - Device fleet management
- **Users** - User management
- **Analytics** - Charts and performance metrics

### 2. Enhanced Overview Tab
- System stats cards (Total Devices, Total Users, System Health, Alerts)
- Line chart showing 7-day trends (devices, users)
- Pie chart for device status distribution
- Recent activity feed
- Quick action buttons (Backup, Reports, Settings, Alerts)

### 3. Devices Management Tab
- Device list table with columns:
  - Device name
  - Type
  - Location (with MapPin icon)
  - Owner
  - Status (online/warning/offline)
  - WQI score
  - Last sync time
  - Actions (View, Edit, Delete)
- Filter dropdown (All/Online/Warning/Offline)
- Add Device button

### 4. Users Management Tab
- User list table with columns:
  - Name
  - Email
  - Role (admin/technician/consumer)
  - Number of devices
  - Status (active/inactive)
  - Joined date
  - Actions (View, Edit, Delete)
- Add User button

### 5. Analytics Tab
- User role distribution bar chart
- Alert trends line chart (7 days)
- System performance metrics:
  - Average Uptime (99.5%)
  - Data Accuracy (98.2%)
  - User Satisfaction (4.7/5.0)

## Implementation Steps

### Step 1: Add State Management
```typescript
const [selectedView, setSelectedView] = useState('overview');
const [deviceFilter, setDeviceFilter] = useState('all');
```

### Step 2: Add Mock Data (Replace with API calls later)
- devices array
- users array
- systemMetrics array
- deviceStatusData
- userRoleData
- recentActivities

### Step 3: Add Helper Functions
```typescript
const getStatusColor = (status) => {
  // Returns Tailwind classes based on status
};

const getRoleColor = (role) => {
  // Returns Tailwind classes based on role
};
```

### Step 4: Create Tab Navigation UI
```tsx
<div className="bg-white rounded-lg shadow-md mb-6">
  <div className="flex border-b">
    <button onClick={() => setSelectedView('overview')}>Overview</button>
    <button onClick={() => setSelectedView('devices')}>Devices</button>
    <button onClick={() => setSelectedView('users')}>Users</button>
    <button onClick={() => setSelectedView('analytics')}>Analytics</button>
  </div>
</div>
```

### Step 5: Implement Each Tab View
- Conditional rendering based on `selectedView`
- Use Recharts for charts (LineChart, BarChart, PieChart)
- Use Lucide icons throughout

## Required Dependencies
- recharts (already installed)
- lucide-react (already installed)
- framer-motion (already installed)

## Color Scheme
- Primary: Purple (#8b5cf6, #7c3aed)
- Success: Green (#10b981)
- Warning: Yellow/Orange (#f59e0b)
- Danger: Red (#ef4444)
- Info: Blue (#3b82f6)

## Icons to Use
- Shield - Admin/Security
- Server - Devices
- Users - User management
- Activity - System health
- AlertTriangle - Alerts
- Database - Backup
- BarChart3 - Analytics
- Settings - Configuration
- Bell - Notifications
- MapPin - Location
- Eye - View
- Edit - Edit
- Trash2 - Delete
- Plus - Add new
- UserPlus - Add user

## Next Steps
1. Backup current AdminDashboard.tsx
2. Implement tabbed navigation
3. Add Overview tab with charts
4. Add Devices management table
5. Add Users management table
6. Add Analytics tab
7. Connect to real API endpoints
8. Add action handlers for buttons
9. Test all functionality
10. Remove hardcoded data

## Notes
- Keep existing authentication and routing logic
- Maintain integration with useDashboardData hook
- Preserve NotificationCenter and DataExportModal
- Add loading states for data fetching
- Add error handling
- Make tables responsive
- Add pagination for large datasets
