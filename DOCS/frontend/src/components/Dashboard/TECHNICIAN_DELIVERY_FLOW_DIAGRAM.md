# Technician Delivery Tracking - Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Technician Dashboard                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Task List                                              │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │ Task: Install AquaChain-Pro-X1                   │  │    │
│  │  │ Customer: John Doe                                │  │    │
│  │  │                                                    │  │    │
│  │  │ Delivery Status:                                  │  │    │
│  │  │ ┌──────────────────────────────────────────┐     │  │    │
│  │  │ │ ⏳ Awaiting Delivery                     │     │  │    │
│  │  │ └──────────────────────────────────────────┘     │  │    │
│  │  │                                                    │  │    │
│  │  │ [Accept Task] (disabled)                         │  │    │
│  │  │ Tooltip: "Device must be delivered first"        │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    WebSocket Connection
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Services                              │
│                                                                  │
│  ┌────────────────┐    ┌──────────────────┐                    │
│  │ Shipments      │───→│ DynamoDB Streams │                    │
│  │ DynamoDB Table │    └──────────────────┘                    │
│  └────────────────┘             ↓                               │
│                                  ↓                               │
│                    ┌──────────────────────────┐                 │
│                    │ Notification Lambda      │                 │
│                    │ - Detects delivery       │                 │
│                    │ - Finds assigned tech    │                 │
│                    │ - Sends WebSocket event  │                 │
│                    └──────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    WebSocket Message
                    {
                      type: "shipment_delivered",
                      data: {
                        order_id: "ord_123",
                        destination: {
                          contact_name: "John Doe",
                          address: "123 Main St"
                        }
                      }
                    }
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Technician Dashboard                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  🎉 Delivery Notification                              │    │
│  │                                                          │    │
│  │  Device delivered to John Doe!                          │    │
│  │  Address: 123 Main St, Bangalore                        │    │
│  │                                                          │    │
│  │  [OK]  [View Details]                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Task List (Updated)                                    │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │ Task: Install AquaChain-Pro-X1                   │  │    │
│  │  │ Customer: John Doe                                │  │    │
│  │  │                                                    │  │    │
│  │  │ Delivery Status:                                  │  │    │
│  │  │ ┌──────────────────────────────────────────┐     │  │    │
│  │  │ │ ✅ Ready to Install                      │     │  │    │
│  │  │ └──────────────────────────────────────────┘     │  │    │
│  │  │                                                    │  │    │
│  │  │ [Accept Task] (enabled)                          │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Delivery Status State Machine

```
┌─────────────────┐
│  No Shipment    │
│      Info       │
│                 │
│      📦         │
└────────┬────────┘
         │
         │ Shipment Created
         ↓
┌─────────────────┐
│   Awaiting      │
│   Delivery      │
│                 │
│      ⏳         │
└────────┬────────┘
         │
         │ Device Delivered
         ↓
┌─────────────────┐
│   Ready to      │
│   Install       │
│                 │
│      ✅         │
└─────────────────┘
```

---

## Accept Button State Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Task Assigned                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │  Check Delivery       │
         │  Status               │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
┌─────────────────┐    ┌─────────────────┐
│  Not Delivered  │    │    Delivered    │
└────────┬────────┘    └────────┬────────┘
         │                       │
         ↓                       ↓
┌─────────────────┐    ┌─────────────────┐
│ Button DISABLED │    │ Button ENABLED  │
│                 │    │                 │
│ Show Tooltip:   │    │ Can Accept Task │
│ "Device must be │    │                 │
│ delivered first"│    │                 │
└─────────────────┘    └─────────────────┘
```

---

## Notification Flow

```
┌─────────────────────────────────────────────────────────┐
│              Courier Delivers Device                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Webhook Handler Updates Shipments Table         │
│         Status: in_transit → delivered                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              DynamoDB Streams Trigger                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           Notification Lambda Executes                   │
│           - Reads order_id from stream                   │
│           - Queries DeviceOrders for technician          │
│           - Sends WebSocket message                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│         WebSocket Server Broadcasts Message              │
│         Topic: technician-updates                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│      Technician Dashboard Receives Message               │
│      - Checks if task is assigned to this tech           │
│      - Shows notification modal                          │
│      - Refreshes shipment status                         │
│      - Enables Accept button                             │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌──────────────┐
│  Technician  │
│  Dashboard   │
└──────┬───────┘
       │
       │ 1. Page Load
       ↓
┌──────────────────────┐
│  Fetch Tasks         │
│  GET /api/orders     │
└──────┬───────────────┘
       │
       │ 2. For Each Task
       ↓
┌──────────────────────────────┐
│  Fetch Shipment Status       │
│  GET /api/shipments?orderId  │
└──────┬───────────────────────┘
       │
       │ 3. Store in State
       ↓
┌──────────────────────┐
│  shipmentStatuses    │
│  {                   │
│    "ord_123": {...}, │
│    "ord_456": {...}  │
│  }                   │
└──────┬───────────────┘
       │
       │ 4. Render UI
       ↓
┌──────────────────────┐
│  Display Badges      │
│  Enable/Disable      │
│  Buttons             │
└──────────────────────┘

       ┌─────────────────┐
       │  WebSocket      │
       │  Connection     │
       └────────┬────────┘
                │
                │ 5. Real-time Update
                ↓
       ┌─────────────────┐
       │  Delivery Event │
       │  Received       │
       └────────┬────────┘
                │
                │ 6. Update State
                ↓
       ┌─────────────────┐
       │  Show           │
       │  Notification   │
       └────────┬────────┘
                │
                │ 7. Refresh Status
                ↓
       ┌─────────────────┐
       │  Enable Button  │
       └─────────────────┘
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                  TechnicianDashboard                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  State Management                                   │    │
│  │  - shipmentStatuses: Record<string, Shipment>      │    │
│  │  - successModal: { show, message, orderId }        │    │
│  │  - selectedTask: Task | null                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Hooks                                              │    │
│  │  - useDashboardData('technician')                  │    │
│  │  - useRealTimeUpdates('technician-updates')        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Helper Functions                                   │    │
│  │  - getDeliveryStatusBadge(orderId)                 │    │
│  │  - isDeliveryConfirmed(orderId)                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Effects                                            │    │
│  │  - Fetch shipment statuses on mount                │    │
│  │  - Listen for delivery notifications                │    │
│  │  - Refresh status on delivery                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  UI Components                                      │    │
│  │  - Task Cards with Delivery Badges                 │    │
│  │  - Accept Button (conditional enable)              │    │
│  │  - Success Modal (with View Details)               │    │
│  │  - Task Details Modal                               │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│              API Call / WebSocket Event                  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
┌─────────────────┐    ┌─────────────────┐
│    Success      │    │     Error       │
└────────┬────────┘    └────────┬────────┘
         │                       │
         ↓                       ↓
┌─────────────────┐    ┌─────────────────┐
│ Update State    │    │ Log Error       │
│ Show Badge      │    │ Show Fallback   │
│ Enable Button   │    │ Retry Logic     │
└─────────────────┘    └─────────────────┘

Error Scenarios:
1. Shipment Not Found → Show "No Shipment Info" badge
2. WebSocket Disconnect → Show connection warning banner
3. API Timeout → Retry with exponential backoff
4. Invalid Data → Log error, show generic message
```

---

## User Journey Map

```
Step 1: Login
┌─────────────────┐
│ Technician logs │
│ into dashboard  │
└────────┬────────┘
         │
         ↓
Step 2: View Tasks
┌─────────────────┐
│ Sees task list  │
│ with delivery   │
│ status badges   │
└────────┬────────┘
         │
         ↓
Step 3: Check Status
┌─────────────────┐
│ Identifies      │
│ "Ready to       │
│ Install" tasks  │
└────────┬────────┘
         │
         ↓
Step 4: Accept Task
┌─────────────────┐
│ Clicks enabled  │
│ Accept button   │
└────────┬────────┘
         │
         ↓
Step 5: Start Work
┌─────────────────┐
│ Begins          │
│ installation    │
│ process         │
└─────────────────┘

Alternative Path: Awaiting Delivery
┌─────────────────┐
│ Sees "Awaiting  │
│ Delivery" badge │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Hovers over     │
│ disabled button │
│ (sees tooltip)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Waits for       │
│ notification    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Receives        │
│ delivery alert  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Views details   │
│ and accepts     │
└─────────────────┘
```

---

## Performance Optimization

```
Initial Load:
┌─────────────────┐
│ Fetch 10 tasks  │
│ (100ms)         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Fetch shipment  │
│ status for each │
│ (10 x 150ms)    │
│ = 1.5s total    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Render UI       │
│ (50ms)          │
└─────────────────┘

Total: ~1.65s

Optimized (Future):
┌─────────────────┐
│ Fetch 10 tasks  │
│ (100ms)         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Batch fetch all │
│ shipment status │
│ (200ms)         │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Render UI       │
│ (50ms)          │
└─────────────────┘

Total: ~350ms (78% faster!)
```

---

## Summary

This implementation provides:
- ✅ Real-time delivery visibility
- ✅ Smart task acceptance control
- ✅ Instant delivery notifications
- ✅ Seamless user experience
- ✅ Robust error handling
- ✅ Scalable architecture

The flow ensures technicians always have accurate delivery information and can only accept tasks when devices are ready for installation.
