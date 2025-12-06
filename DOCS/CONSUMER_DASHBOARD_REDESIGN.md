# Consumer Dashboard Redesign - Multi-Device Support

## Current Issues
- Dashboard shows aggregated data from all devices
- No clear way to view individual device data
- Clunky when consumer has multiple devices
- Hard to distinguish which data belongs to which device

## Proposed Solution

### Design Approach: Device Tabs + Individual Views

```
┌─────────────────────────────────────────────────────────────┐
│  Consumer Dashboard                          [Profile] [🔔]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  My Devices (3)                                              │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ 🏠 Kitchen   │ 🚿 Bathroom  │ 🏡 Living    │  [+ Add]   │
│  │   Online     │   Online     │   Offline    │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Kitchen Device - ESAPI23                            │   │
│  │  📍 Home - Kitchen Area                              │   │
│  │  ✅ Online • Last updated: 2 mins ago                │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                       │   │
│  │  Water Quality Index: 85 (Good)                      │   │
│  │  ████████████████░░░░                                │   │
│  │                                                       │   │
│  │  ┌──────────┬──────────┬──────────┬──────────┐     │   │
│  │  │ pH       │ Turbidity│   TDS    │   Temp   │     │   │
│  │  │  7.2     │  2.1 NTU │ 180 ppm  │  24°C    │     │   │
│  │  └──────────┴──────────┴──────────┴──────────┘     │   │
│  │                                                       │   │
│  │  📊 7-Day Trend                                      │   │
│  │  [Chart showing water quality over time]             │   │
│  │                                                       │   │
│  │  ⚠️ Recent Alerts (2)                                │   │
│  │  • High TDS detected - 2 hours ago                   │   │
│  │  • pH slightly elevated - 5 hours ago                │   │
│  │                                                       │   │
│  │  [View Full Report] [Export Data] [Device Settings]  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Device Selector Tabs
- Horizontal scrollable tabs for all devices
- Shows device name, icon, and status
- Active tab highlighted
- Quick visual status indicators (color-coded)

### 2. Individual Device View
Each device gets its own dedicated view with:
- **Device Header**
  - Device name and ID
  - Location
  - Online/Offline status
  - Last update time
  - Quick actions (settings, export, alerts)

- **Water Quality Overview**
  - Large WQI score with color coding
  - Visual progress bar
  - Status message (Excellent/Good/Fair/Poor)

- **Parameter Cards**
  - pH, Turbidity, TDS, Temperature
  - Current values with units
  - Trend indicators (↑↓→)
  - Color-coded status

- **Historical Chart**
  - 7-day/30-day trend
  - Interactive chart
  - Multiple parameters toggle

- **Recent Alerts**
  - Device-specific alerts only
  - Timestamp and severity
  - Quick action buttons

- **Quick Actions**
  - View full report
  - Export device data
  - Device settings
  - Report issue

### 3. Empty State
When no devices:
```
┌─────────────────────────────────────┐
│  No Devices Yet                     │
│                                     │
│  📱 Get started by adding your      │
│     first water quality device      │
│                                     │
│  [+ Add Your First Device]          │
└─────────────────────────────────────┘
```

### 4. Mobile Responsive
- Tabs become dropdown on mobile
- Cards stack vertically
- Touch-friendly interactions

## Implementation Plan

### Phase 1: Device Selector
- Create device tab component
- Add device switching logic
- Store selected device in state

### Phase 2: Individual Device View
- Refactor dashboard to show single device data
- Filter data by selected device
- Update charts and metrics

### Phase 3: Polish
- Add animations
- Improve loading states
- Add empty states
- Mobile optimization

## Benefits
✅ Clean, organized interface
✅ Easy to switch between devices
✅ Clear data attribution
✅ Scalable (works with 1 or 100 devices)
✅ Better user experience
✅ Reduced cognitive load
