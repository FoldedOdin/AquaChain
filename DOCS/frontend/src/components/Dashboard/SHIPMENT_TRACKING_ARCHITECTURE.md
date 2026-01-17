# Consumer Shipment Tracking - Architecture Diagram

## Component Hierarchy

```
MyOrdersPage
    │
    ├── Order List
    │   └── Order Cards
    │
    └── Order Details Modal
        ├── Order Information
        ├── Installation Details
        ├── ShipmentTracking ◄── NEW COMPONENT
        │   ├── Delivery Confirmation Banner (conditional)
        │   ├── Shipment Header
        │   │   ├── Courier Info
        │   │   ├── Tracking Number
        │   │   └── Track Package Button
        │   ├── Progress Bar
        │   │   ├── Status Message
        │   │   └── Percentage Indicator
        │   ├── Timeline Display
        │   │   └── Timeline Events
        │   │       ├── Icon
        │   │       ├── Status Label
        │   │       ├── Location
        │   │       ├── Description
        │   │       └── Timestamp
        │   ├── Courier Contact Info
        │   └── Toast Notifications
        └── Order Timeline
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Consumer Dashboard                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              MyOrdersPage                           │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │        Order Details Modal                   │ │    │
│  │  │                                              │ │    │
│  │  │  ┌────────────────────────────────────────┐ │ │    │
│  │  │  │     ShipmentTracking Component        │ │ │    │
│  │  │  │                                        │ │ │    │
│  │  │  │  Props: orderId, orderStatus          │ │ │    │
│  │  │  └────────────────────────────────────────┘ │ │    │
│  │  └──────────────────────────────────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ API Call
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Shipment Service                            │
│                                                              │
│  getShipmentByOrderId(orderId)                              │
│      ↓                                                       │
│  GET /api/shipments?orderId={orderId}                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Response
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend API                                 │
│                                                              │
│  Lambda: get_shipment_status                                │
│      ↓                                                       │
│  DynamoDB: Shipments Table                                  │
│      ↓                                                       │
│  Returns: { shipment, progress }                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ WebSocket
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              WebSocket Service                               │
│                                                              │
│  Topic: shipment-updates-{orderId}                          │
│      ↓                                                       │
│  Receives: shipment_update messages                         │
│      ↓                                                       │
│  Triggers: UI refresh + Toast notification                  │
└─────────────────────────────────────────────────────────────┘
```

## State Management

```
ShipmentTracking Component State
├── shipment: Shipment | null
│   ├── shipment_id
│   ├── tracking_number
│   ├── courier_name
│   ├── internal_status
│   ├── timeline[]
│   ├── estimated_delivery
│   └── delivered_at
├── progress: ShipmentProgress | null
│   ├── percentage
│   ├── status_message
│   ├── status_color
│   └── is_completed
├── isLoading: boolean
├── error: string | null
└── toast: Toast
    ├── message
    ├── type
    └── visible
```

## Lifecycle Flow

```
Component Mount
    ↓
Check orderStatus
    ↓
Is shipped/installing/completed?
    ├─ No → Don't render
    └─ Yes → Continue
        ↓
    Fetch shipment data
        ↓
    Display loading state
        ↓
    API call completes
        ↓
    Update state (shipment, progress)
        ↓
    Render UI
        ↓
    Connect WebSocket
        ↓
    Subscribe to topic
        ↓
    Listen for updates
        ↓
    On update received
        ├─ Refresh data
        ├─ Update UI
        └─ Show toast (if important)
        ↓
Component Unmount
    ↓
Disconnect WebSocket
    ↓
Cleanup complete
```

## WebSocket Message Flow

```
Backend Event
    ↓
Webhook received
    ↓
Status updated in DB
    ↓
DynamoDB Stream triggers
    ↓
Notification Lambda
    ↓
WebSocket message sent
    ↓
Topic: shipment-updates-{orderId}
    ↓
Consumer receives message
    ↓
handleShipmentUpdate()
    ├─ Validate message
    ├─ Check order_id match
    ├─ Refresh shipment data
    └─ Show toast notification
        ↓
UI updates automatically
```

## UI Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Shipment Tracking                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ Package Delivered!                                  │ │
│ │ Your device was successfully delivered on Dec 29, 2025 │ │
│ │                                                         │ │
│ │ ┌─────────────────────────────────────────────────┐   │ │
│ │ │ 🔧 Installation Ready                           │   │ │
│ │ │ Your device is ready for installation           │   │ │
│ │ └─────────────────────────────────────────────────┘   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 🚚 Delhivery - Surface              [Track Package →] │ │
│ │ 📦 Tracking: DELHUB123456789                          │ │
│ │                                                        │ │
│ │ Package delivered successfully              100%      │ │
│ │ ████████████████████████████████████████              │ │
│ │                                                        │ │
│ │ ✅ Delivered: Dec 29, 2025, 6:00 PM                   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Shipment Timeline                                      │ │
│ │                                                        │ │
│ │ 📦 ─┐                                                  │ │
│ │     │ Shipment Created                                │ │
│ │     │ 📍 Mumbai Warehouse                             │ │
│ │     │ Dec 28, 2025, 12:00 PM                         │ │
│ │     │                                                  │ │
│ │ 🚚 ─┤                                                  │ │
│ │     │ Picked Up                                       │ │
│ │     │ 📍 Mumbai Hub                                   │ │
│ │     │ Dec 28, 2025, 2:30 PM                          │ │
│ │     │                                                  │ │
│ │ 🛣️ ─┤                                                  │ │
│ │     │ In Transit                                      │ │
│ │     │ 📍 Pune Hub                                     │ │
│ │     │ Dec 29, 2025, 10:00 AM                         │ │
│ │     │                                                  │ │
│ │ 🚛 ─┤                                                  │ │
│ │     │ Out for Delivery                                │ │
│ │     │ 📍 Bangalore Hub                                │ │
│ │     │ Dec 29, 2025, 4:00 PM                          │ │
│ │     │                                                  │ │
│ │ ✅ ─┘                                                  │ │
│ │     Delivered                                          │ │
│ │     📍 Customer Location                               │ │
│ │     Dec 29, 2025, 6:00 PM                             │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Need Help?                                             │ │
│ │ 📞 +91-124-4646444  ✉️ support@delhivery.com          │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Status Color Mapping

```
Status              Color       Progress    Icon
─────────────────────────────────────────────────
shipment_created    Blue        0%          📦
picked_up           Indigo      20%         🚚
in_transit          Purple      60%         🛣️
out_for_delivery    Yellow      80%         🚛
delivered           Green       100%        ✅
delivery_failed     Red         N/A         ❌
returned            Gray        N/A         ↩️
cancelled           Gray        N/A         🚫
lost                Red         N/A         ❓
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend                                  │
│                                                              │
│  Components                                                  │
│  ├── MyOrdersPage.tsx ◄─────────────┐                      │
│  │   └── ShipmentTracking.tsx       │                      │
│  │                                   │                      │
│  Services                            │                      │
│  ├── shipmentService.ts ─────────────┤                      │
│  │   ├── getShipmentByOrderId()     │                      │
│  │   └── API calls                  │                      │
│  │                                   │                      │
│  ├── websocketService.ts ────────────┤                      │
│  │   ├── connect()                  │                      │
│  │   ├── disconnect()               │                      │
│  │   └── Connection management      │                      │
│  │                                   │                      │
│  Types                               │                      │
│  └── shipment.ts ────────────────────┘                      │
│      ├── Shipment                                           │
│      ├── ShipmentProgress                                   │
│      ├── STATUS_ICONS                                       │
│      ├── STATUS_LABELS                                      │
│      └── COURIER_CONTACTS                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/WebSocket
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend                                   │
│                                                              │
│  API Gateway                                                 │
│  └── GET /api/shipments?orderId={id}                        │
│                                                              │
│  Lambda Functions                                            │
│  ├── get_shipment_status.py                                 │
│  └── notification_handler.py (WebSocket)                    │
│                                                              │
│  DynamoDB                                                    │
│  └── Shipments Table                                         │
│                                                              │
│  WebSocket API                                               │
│  └── Topic: shipment-updates-{orderId}                      │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
API Call
    ↓
Try fetch
    ├─ Success → Update state
    └─ Error
        ↓
    Catch error
        ↓
    Log to console
        ↓
    Set error state
        ↓
    Display error UI
        ↓
    Show yellow alert
        ↓
    Provide explanation
        ↓
    User can retry
```

## Responsive Design Breakpoints

```
Mobile (< 640px)
├── Single column layout
├── Stacked elements
├── Full-width buttons
└── Compact timeline

Tablet (640px - 1024px)
├── Two column layout
├── Side-by-side elements
├── Medium buttons
└── Expanded timeline

Desktop (> 1024px)
├── Multi-column layout
├── Horizontal elements
├── Large buttons
└── Full timeline with details
```

## Performance Optimization

```
Component Lifecycle
├── Mount
│   ├── Check order status (fast)
│   ├── Conditional render (fast)
│   └── Fetch data (async)
├── Update
│   ├── WebSocket message (fast)
│   ├── State update (fast)
│   └── Re-render (optimized)
└── Unmount
    ├── Disconnect WebSocket (fast)
    └── Cleanup (fast)

Optimizations
├── Lazy loading (only when needed)
├── Memoization (prevent re-renders)
├── Debouncing (limit API calls)
├── Connection pooling (reuse WebSocket)
└── Cleanup (prevent memory leaks)
```

## Security Architecture

```
Authentication Flow
    ↓
User logs in
    ↓
JWT token stored
    ↓
Token included in API calls
    ↓
Backend validates token
    ↓
Checks user permissions
    ↓
Returns data if authorized
    ↓
WebSocket connection
    ↓
Token sent on connect
    ↓
Backend validates
    ↓
Subscribes to allowed topics
```

## Deployment Architecture

```
Development
├── Local API (localhost:3002)
├── Local WebSocket (localhost:3001)
└── Mock data

Staging
├── Staging API (staging.api.aquachain.com)
├── Staging WebSocket (staging.ws.aquachain.com)
└── Test data

Production
├── Production API (api.aquachain.com)
├── Production WebSocket (ws.aquachain.com)
└── Real data
```

## Monitoring & Logging

```
Component Events
├── Mount → Log component loaded
├── API Call → Log request/response
├── WebSocket Connect → Log connection
├── WebSocket Message → Log update
├── Error → Log error details
└── Unmount → Log cleanup

Metrics
├── Load time
├── API response time
├── WebSocket latency
├── Error rate
└── User interactions
```

## Conclusion

This architecture provides:
- **Modular Design**: Reusable components
- **Real-time Updates**: WebSocket integration
- **Error Handling**: Graceful degradation
- **Performance**: Optimized rendering
- **Security**: Token-based auth
- **Scalability**: Connection pooling
- **Maintainability**: Clear structure
