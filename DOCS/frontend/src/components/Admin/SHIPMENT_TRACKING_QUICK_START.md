# Shipment Tracking UI - Quick Start Guide

## Overview

The Admin dashboard now includes a comprehensive shipment tracking interface for managing and monitoring device deliveries.

## Accessing Shipment Tracking

1. Log in to the Admin Dashboard
2. Click on the **"Shipments"** tab in the navigation bar
3. Or use the **"Track Shipments"** button in Quick Actions

## Features

### 1. Shipments List

**View All Shipments**
- See all shipments in a table format
- Columns: Tracking Number, Order ID, Customer, Courier, Status, Est. Delivery
- Delayed shipments are highlighted in red with a ⚠️ icon

**Filter by Status**
- **All** - View all shipments
- **In Transit** - Active shipments being delivered
- **Delivered** - Successfully delivered shipments
- **Failed** - Shipments with delivery failures

**Search Functionality**
- Search by tracking number (e.g., "DELHUB123456789")
- Search by order ID (e.g., "ord_1735392000000")
- Search by customer name

**Refresh Data**
- Click the "Refresh" button to get latest shipment data

### 2. Shipment Details

**View Details**
- Click "View Details" on any shipment row
- Opens a modal with complete shipment information

**Information Displayed**
- Tracking number and order ID
- Courier name and service type
- Current status with progress bar
- Destination details (customer name, phone, address)
- Estimated delivery date
- Actual delivery/failure timestamps (if applicable)
- Retry attempt information (for failed deliveries)

**Timeline Tab**
- Complete chronological history of shipment
- Each event shows:
  - Status icon (📦 🚚 🛣️ 🚛 ✅ ❌)
  - Status description
  - Timestamp
  - Location
  - Additional notes

**Webhook History Tab**
- View all webhook events received from courier
- Event ID and timestamp
- Courier status code
- Raw payload viewer (for debugging)

**Courier Contact**
- Phone number and email
- "Call Courier" button (opens phone dialer)
- "Track on Courier Site" button (opens courier's tracking page)

### 3. Create Shipment

**From Order Management** (Future Integration)
- Navigate to an approved order
- Click "Mark as Shipped" button
- Fill in shipment details modal

**Shipment Creation Form**
- **Courier Details**
  - Select courier (Delhivery, BlueDart, DTDC)
  - Select service type (Surface, Express)
  
- **Destination Details**
  - Contact name
  - Contact phone (format: +919876543210)
  - Full address
  - Pincode (6 digits)
  
- **Package Details**
  - Weight in kg (e.g., 0.5)
  - Declared value in ₹ (e.g., 5000)
  - Insurance checkbox

**After Creation**
- Success message displays tracking number
- Shipment appears in the list immediately
- Customer receives notification with tracking info

### 4. Stale Shipments Alert

**What are Stale Shipments?**
- Shipments with no updates for 7+ days
- Excludes delivered, returned, or cancelled shipments

**Alert Display**
- Yellow warning banner at top of page
- Shows count of stale shipments
- Click to expand and view list

**Stale Shipment Details**
- Tracking number with "X days stale" badge
- Order ID and customer information
- Courier name
- Last update timestamp
- "Investigate" button to view full details

**Auto-Refresh**
- Stale shipments check refreshes every 5 minutes
- Manual refresh available via button

## Status Indicators

### Status Colors and Icons

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| Shipment Created | 📦 | Blue | Shipment registered with courier |
| Picked Up | 🚚 | Indigo | Package collected from warehouse |
| In Transit | 🛣️ | Purple | Package in transit to destination |
| Out for Delivery | 🚛 | Yellow | Package out for final delivery |
| Delivered | ✅ | Green | Successfully delivered |
| Delivery Failed | ❌ | Red | Delivery attempt failed |
| Returned | ↩️ | Gray | Returned to sender |
| Cancelled | 🚫 | Gray | Shipment cancelled |
| Lost | ❓ | Red | Package lost/missing |

### Progress Bar

The progress bar shows delivery completion percentage:
- **0-20%** - Shipment Created / Picked Up
- **20-60%** - In Transit
- **60-80%** - Out for Delivery
- **100%** - Delivered

## Common Workflows

### Workflow 1: Create New Shipment

1. Navigate to Shipments tab
2. (Future) Click "Create Shipment" or mark order as shipped
3. Select courier and service type
4. Enter destination details
5. Enter package details
6. Click "Create Shipment"
7. Note the tracking number from success message
8. Shipment appears in list with "Shipment Created" status

### Workflow 2: Track Shipment Progress

1. Navigate to Shipments tab
2. Find shipment using search or filters
3. Click "View Details"
4. View current status and progress bar
5. Check timeline for detailed history
6. Monitor estimated delivery date

### Workflow 3: Investigate Delayed Shipment

1. Check for red highlighted rows in shipments list
2. Or check Stale Shipments Alert banner
3. Click "View Details" or "Investigate"
4. Review timeline for last known status
5. Check webhook history for courier updates
6. Contact courier using provided phone/email
7. Or track on courier's website

### Workflow 4: Handle Delivery Failure

1. Shipment status changes to "Delivery Failed"
2. View details to see failure reason
3. Check retry count (max 3 attempts)
4. If retries available: System schedules redelivery
5. If max retries exceeded: Admin task created
6. Contact customer to verify address
7. Contact courier to reschedule

## Troubleshooting

### Shipment Not Showing

**Check:**
- Refresh the page
- Clear status filters (set to "All")
- Clear search query
- Verify shipment was created successfully

### Delayed Shipment

**Actions:**
1. View shipment details
2. Check last update timestamp
3. Review timeline for issues
4. Contact courier directly
5. Verify customer address is correct

### Webhook History Empty

**Possible Causes:**
- Courier hasn't sent updates yet
- Webhook integration issue
- Check with DevOps team

### Can't Create Shipment

**Check:**
- All required fields filled
- Phone number format (+91XXXXXXXXXX)
- Pincode is 6 digits
- Valid authentication token
- API endpoint is accessible

## API Endpoints Used

- `GET /api/shipments` - List all shipments
- `GET /api/shipments/:shipmentId` - Get shipment details
- `GET /api/shipments?orderId=:orderId` - Get by order ID
- `POST /api/shipments` - Create new shipment

## Supported Couriers

### Delhivery
- Phone: +91-124-4646444
- Email: support@delhivery.com
- Tracking: https://www.delhivery.com/track/package/

### BlueDart
- Phone: +91-22-28394444
- Email: customercare@bluedart.com
- Tracking: https://www.bluedart.com/tracking/

### DTDC
- Phone: +91-22-30916000
- Email: care@dtdc.com
- Tracking: https://www.dtdc.in/tracking.asp

## Tips and Best Practices

### For Admins

1. **Monitor Stale Shipments Daily**
   - Check the alert banner each morning
   - Investigate any shipments over 7 days old
   - Contact courier proactively

2. **Use Filters Effectively**
   - Filter by "In Transit" to see active deliveries
   - Filter by "Failed" to handle issues quickly
   - Use search for specific customer inquiries

3. **Document Issues**
   - Use webhook history for debugging
   - Note timeline events for reference
   - Keep courier contact info handy

4. **Proactive Communication**
   - Contact customers for delayed shipments
   - Update customers on delivery failures
   - Coordinate with technicians on delivery confirmations

### For Developers

1. **Error Handling**
   - Check browser console for API errors
   - Verify authentication token is valid
   - Ensure API endpoints are accessible

2. **Performance**
   - Use filters to reduce data load
   - Refresh only when needed
   - Monitor network requests

3. **Testing**
   - Test with various shipment statuses
   - Verify webhook payload parsing
   - Check edge cases (empty states, errors)

## Future Enhancements

Coming soon:
- Real-time WebSocket updates
- Bulk shipment operations
- Export to CSV/PDF
- Advanced analytics dashboard
- Push notifications
- Integration with order management
- Automated retry scheduling UI

## Support

For issues or questions:
1. Check this guide first
2. Review the detailed summary document
3. Contact the development team
4. Check API endpoint documentation

## Version History

- **v1.0** (Current) - Initial release
  - Shipments list with filters and search
  - Shipment details modal
  - Stale shipments alert
  - Create shipment modal (ready for integration)
  - Support for 3 couriers (Delhivery, BlueDart, DTDC)
