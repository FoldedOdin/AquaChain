# Device Order Workflow - Simplified

## Changes Made

### Combined Provisioning + Technician Assignment
Previously, the workflow had separate steps for provisioning a device and assigning a technician. This has been combined into a single step for efficiency.

## New Workflow

1. **Pending** → Customer submits device order
2. **Quoted** → Admin sets quote amount
3. **Shipped** → Admin provisions device + assigns technician + marks as shipped (all automatic)
4. **Completed** → Technician completes installation

## What Changed

### ProvisionModal.tsx
- Added technician selection dropdown
- Fetches list of technicians from `/api/admin/users`
- Performs THREE actions in sequence:
  1. Provisions device to order
  2. Assigns technician to order
  3. Marks order as shipped
- Button text: "Provision & Ship"

### OrdersQueueTab.tsx
- Removed `AssignTechnicianModal` import and usage
- Removed "Assign Technician" button (no longer needed)
- Removed "Mark as Shipped" button (automatic now)
- Removed `handleShip` function
- Cleaned up unused state and handlers

### Backend (dev-server.js)
- Modified device creation to use "INVENTORY" userId for unassigned devices
- No changes needed to provision/assign endpoints (they work independently)

## Benefits

1. **Faster workflow** - One step instead of four
2. **Less clicks** - Admin completes everything in one modal
3. **Better UX** - All related information in one place
4. **Cleaner UI** - Fewer buttons and modals to manage
5. **Automatic shipping** - No need to manually mark as shipped

## Testing

1. Login as admin (`admin@aquachain.com` / `admin1234`)
2. Go to Orders tab
3. Find order with status "quoted"
4. Click "Provision Device"
5. Select device from dropdown (e.g., AC-INV-001)
6. Select technician from dropdown (e.g., Sidharth Lenin)
7. Click "Provision & Ship"
8. Order status changes directly to "shipped"
9. Technician can now see the order and complete installation

## Inventory Devices

Added 5 unassigned devices to inventory:
- AC-INV-001 through AC-INV-005
- All located in "Warehouse"
- Status: "online"
- consumerName: "Unassigned"

To add more inventory devices, use the script:
```bash
node add-inventory-devices.js
```
