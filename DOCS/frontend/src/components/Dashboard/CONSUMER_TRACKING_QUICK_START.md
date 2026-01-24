# Consumer Shipment Tracking - Quick Start Guide

## Overview

This guide helps you quickly integrate and use the Consumer shipment tracking UI component.

## Installation

The component is already integrated into the Consumer dashboard. No additional installation required.

## Basic Usage

### 1. Import the Component

```typescript
import ShipmentTracking from './ShipmentTracking';
```

### 2. Use in Your Component

```typescript
<ShipmentTracking 
  orderId="ord_1735392000000" 
  orderStatus="shipped" 
/>
```

### 3. Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `orderId` | string | Yes | The order ID to fetch shipment data for |
| `orderStatus` | string | Yes | Current order status (shipped, installing, completed) |

## Features

### 📦 Shipment Information
- Courier name and service type
- Tracking number with monospace font
- Direct link to courier tracking page

### 📊 Progress Tracking
- Animated progress bar (0-100%)
- Color-coded status indicators
- Status message and percentage

### 📅 Timeline Display
- Chronological event list
- Emoji icons for each status
- Location and description
- Formatted timestamps

### ✅ Delivery Confirmation
- Prominent green banner when delivered
- Actual delivery timestamp
- "Installation Ready" message

### 🔔 Real-time Updates
- WebSocket connection for live updates
- Toast notifications for important changes
- Automatic UI refresh

## Status Flow

```
📦 Shipment Created
    ↓
🚚 Picked Up
    ↓
🛣️ In Transit
    ↓
🚛 Out for Delivery
    ↓
✅ Delivered
```

## Example Integration

### In Order Details Modal

```typescript
const OrderDetailsModal = ({ order }) => {
  return (
    <div className="modal">
      <h2>Order Details</h2>
      
      {/* Order Information */}
      <OrderInfo order={order} />
      
      {/* Shipment Tracking */}
      <ShipmentTracking 
        orderId={order.orderId} 
        orderStatus={order.status} 
      />
      
      {/* Other sections */}
    </div>
  );
};
```

### In Consumer Dashboard

```typescript
const ConsumerDashboard = () => {
  const [selectedOrder, setSelectedOrder] = useState(null);
  
  return (
    <div>
      <OrdersList onSelectOrder={setSelectedOrder} />
      
      {selectedOrder && (
        <ShipmentTracking 
          orderId={selectedOrder.orderId} 
          orderStatus={selectedOrder.status} 
        />
      )}
    </div>
  );
};
```

## API Requirements

### Endpoint
```
GET /api/shipments?orderId={orderId}
```

### Response Format
```json
{
  "success": true,
  "shipment": {
    "shipment_id": "ship_xxx",
    "order_id": "ord_xxx",
    "tracking_number": "DELHUB123456789",
    "courier_name": "Delhivery",
    "internal_status": "in_transit",
    "timeline": [...],
    "estimated_delivery": "2025-12-31T18:00:00Z"
  },
  "progress": {
    "percentage": 60,
    "status_message": "Package is on the way",
    "status_color": "blue"
  }
}
```

## WebSocket Setup

### Topic Pattern
```
shipment-updates-{orderId}
```

### Message Format
```json
{
  "type": "shipment_update",
  "order_id": "ord_xxx",
  "shipment_id": "ship_xxx",
  "new_status": "delivered",
  "timestamp": "2025-12-29T18:00:00Z"
}
```

### Connection Example
```typescript
import { websocketService } from '../../services/websocketService';

// Connect
websocketService.connect(
  `shipment-updates-${orderId}`,
  (data) => {
    console.log('Update received:', data);
  }
);

// Disconnect
websocketService.disconnect(`shipment-updates-${orderId}`);
```

## Styling

The component uses Tailwind CSS classes. Key color schemes:

- **Primary**: Cyan/Blue gradient
- **Success**: Green (delivered)
- **Warning**: Yellow (out for delivery)
- **Error**: Red (failed)
- **Info**: Purple (in transit)

## Customization

### Change Progress Bar Colors

Edit the `getStatusColor()` function:

```typescript
const getStatusColor = () => {
  switch (progress.status_color) {
    case 'blue': return 'bg-blue-500';
    case 'green': return 'bg-green-500';
    // Add your custom colors
    default: return 'bg-cyan-500';
  }
};
```

### Modify Timeline Icons

Edit `STATUS_ICONS` in `types/shipment.ts`:

```typescript
export const STATUS_ICONS = {
  shipment_created: '📦',
  picked_up: '🚚',
  // Add your custom icons
};
```

### Customize Toast Messages

Edit the `handleShipmentUpdate` function:

```typescript
const statusMessages = {
  out_for_delivery: '🚛 Your package is out for delivery!',
  delivered: '✅ Your package has been delivered!',
  // Add your custom messages
};
```

## Troubleshooting

### Component Not Rendering

**Check:**
1. Order status is 'shipped', 'installing', or 'completed'
2. API endpoint is accessible
3. Authentication token is valid

### WebSocket Not Connecting

**Check:**
1. WebSocket endpoint in environment variables
2. Network connectivity
3. CORS settings

### Timeline Not Showing

**Check:**
1. Shipment data has timeline array
2. Timeline events have required fields
3. API response format matches expected structure

## Testing

### Unit Test Example

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import ShipmentTracking from './ShipmentTracking';

test('displays shipment tracking', async () => {
  render(
    <ShipmentTracking 
      orderId="ord_123" 
      orderStatus="shipped" 
    />
  );
  
  await waitFor(() => {
    expect(screen.getByText(/Shipment Tracking/i)).toBeInTheDocument();
  });
});
```

### Integration Test Example

```typescript
test('updates on WebSocket message', async () => {
  const { rerender } = render(
    <ShipmentTracking orderId="ord_123" orderStatus="shipped" />
  );
  
  // Simulate WebSocket update
  act(() => {
    websocketService.simulateMessage('shipment-updates-ord_123', {
      type: 'shipment_update',
      new_status: 'delivered'
    });
  });
  
  await waitFor(() => {
    expect(screen.getByText(/Delivered/i)).toBeInTheDocument();
  });
});
```

## Environment Variables

Required environment variables:

```env
REACT_APP_API_ENDPOINT=http://localhost:3002
REACT_APP_WEBSOCKET_ENDPOINT=ws://localhost:3001/ws
```

## Dependencies

- React 18+
- framer-motion (animations)
- lucide-react (icons)
- Tailwind CSS (styling)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Tips

1. **Lazy Load**: Component only fetches when needed
2. **Memoization**: Use React.memo for optimization
3. **Debounce**: Limit API calls on rapid updates
4. **Cleanup**: Always disconnect WebSocket on unmount

## Security Best Practices

1. Always validate authentication token
2. Sanitize all user input
3. Use HTTPS for external links
4. Validate WebSocket messages
5. Implement rate limiting

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the implementation summary
3. Check API endpoint logs
4. Verify WebSocket connection

## Next Steps

1. Test the component with real data
2. Customize styling to match your brand
3. Add additional features as needed
4. Monitor performance and errors
5. Gather user feedback

## Quick Reference

### Component Location
```
frontend/src/components/Dashboard/ShipmentTracking.tsx
```

### Service Files
```
frontend/src/services/shipmentService.ts
frontend/src/services/websocketService.ts
```

### Type Definitions
```
frontend/src/types/shipment.ts
```

### Integration Point
```
frontend/src/components/Dashboard/MyOrdersPage.tsx
```

## Example Output

When rendered, the component displays:

```
┌─────────────────────────────────────────┐
│ Shipment Tracking                       │
├─────────────────────────────────────────┤
│ ✅ Package Delivered!                   │
│ Your device was successfully delivered  │
│ on Dec 29, 2025, 6:00 PM               │
│                                         │
│ 🔧 Installation Ready                   │
│ Your device is ready for installation   │
├─────────────────────────────────────────┤
│ 🚚 Delhivery - Surface      [Delivered] │
│ 📦 Tracking: DELHUB123456789           │
│ [Track Package →]                       │
│                                         │
│ ████████████████████ 100%              │
│ Package delivered successfully          │
├─────────────────────────────────────────┤
│ Shipment Timeline                       │
│                                         │
│ 📦 Shipment Created                     │
│    📍 Mumbai Warehouse                  │
│    Dec 28, 2025, 12:00 PM              │
│                                         │
│ 🚚 Picked Up                            │
│    📍 Mumbai Hub                        │
│    Dec 28, 2025, 2:30 PM               │
│                                         │
│ 🛣️ In Transit                           │
│    📍 Pune Hub                          │
│    Dec 29, 2025, 10:00 AM              │
│                                         │
│ 🚛 Out for Delivery                     │
│    📍 Bangalore Hub                     │
│    Dec 29, 2025, 4:00 PM               │
│                                         │
│ ✅ Delivered                             │
│    📍 Customer Location                 │
│    Dec 29, 2025, 6:00 PM               │
├─────────────────────────────────────────┤
│ Need Help?                              │
│ 📞 +91-124-4646444                      │
│ ✉️ support@delhivery.com                │
└─────────────────────────────────────────┘
```

## Conclusion

You're now ready to use the Consumer shipment tracking component! The component provides a complete tracking experience with real-time updates, delivery confirmation, and a user-friendly interface.
