# Consumer Dashboard Multi-Device Implementation

## Changes Required

### 1. Add State for Selected Device
```typescript
const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
```

### 2. Auto-Select First Device
```typescript
// Auto-select first device when devices load
useEffect(() => {
  if (dashboardData && 'devices' in dashboardData && dashboardData.devices?.length > 0) {
    if (!selectedDeviceId) {
      setSelectedDeviceId(dashboardData.devices[0].device_id);
    }
  }
}, [dashboardData, selectedDeviceId]);
```

### 3. Get Devices List
```typescript
const devices = useMemo(() => {
  if (dashboardData && 'devices' in dashboardData) {
    return dashboardData.devices || [];
  }
  return [];
}, [dashboardData]);
```

### 4. Get Selected Device Data
```typescript
const selectedDevice = useMemo(() => {
  return devices.find(d => d.device_id === selectedDeviceId) || devices[0] || null;
}, [devices, selectedDeviceId]);
```

### 5. Device Tabs Component
Add before the main dashboard content:
```tsx
{/* Device Selector Tabs */}
{devices.length > 0 && (
  <div className="bg-white border-b border-gray-200 px-6 py-4 mb-6">
    <div className="flex items-center justify-between mb-3">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
        My Devices ({devices.length})
      </h3>
      <button
        onClick={toggleAddDevice}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add Device
      </button>
    </div>
    
    <div className="flex gap-3 overflow-x-auto pb-2">
      {devices.map((device: any) => {
        const isSelected = device.device_id === selectedDeviceId;
        const isOnline = device.status === 'active' || device.status === 'online';
        
        return (
          <button
            key={device.device_id}
            onClick={() => setSelectedDeviceId(device.device_id)}
            className={`
              flex-shrink-0 px-4 py-3 rounded-lg border-2 transition-all min-w-[200px]
              ${isSelected 
                ? 'border-cyan-500 bg-cyan-50 shadow-md' 
                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex items-center gap-3">
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center
                ${isOnline ? 'bg-green-100' : 'bg-gray-100'}
              `}>
                <Activity className={`w-5 h-5 ${isOnline ? 'text-green-600' : 'text-gray-400'}`} />
              </div>
              <div className="text-left">
                <div className={`font-semibold ${isSelected ? 'text-cyan-900' : 'text-gray-900'}`}>
                  {device.name || device.device_id}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`
                    inline-block w-2 h-2 rounded-full
                    ${isOnline ? 'bg-green-500' : 'bg-gray-400'}
                  `} />
                  <span className="text-xs text-gray-600">
                    {isOnline ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  </div>
)}
```

### 6. Update Dashboard Content
Replace aggregated data with selected device data:

```tsx
{/* Device Header */}
{selectedDevice && (
  <div className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-4 mb-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-bold">{selectedDevice.name || selectedDevice.device_id}</h2>
        <p className="text-cyan-100 mt-1">
          📍 {selectedDevice.location || 'Location not set'}
        </p>
      </div>
      <div className="text-right">
        <div className={`
          inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium
          ${selectedDevice.status === 'active' || selectedDevice.status === 'online'
            ? 'bg-green-500 bg-opacity-20 border border-green-300'
            : 'bg-gray-500 bg-opacity-20 border border-gray-300'
          }
        `}>
          <span className={`w-2 h-2 rounded-full ${
            selectedDevice.status === 'active' || selectedDevice.status === 'online'
              ? 'bg-green-300'
              : 'bg-gray-300'
          }`} />
          {selectedDevice.status === 'active' || selectedDevice.status === 'online' ? 'Online' : 'Offline'}
        </div>
        <p className="text-xs text-cyan-200 mt-2">
          Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  </div>
)}
```

### 7. Empty State
When no devices:
```tsx
{devices.length === 0 && !isLoading && (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="text-center max-w-md">
      <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <Activity className="w-12 h-12 text-gray-400" />
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-3">
        No Devices Yet
      </h3>
      <p className="text-gray-600 mb-6">
        Get started by adding your first water quality monitoring device to track your water parameters in real-time.
      </p>
      <button
        onClick={toggleAddDevice}
        className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors font-medium"
      >
        <Plus className="w-5 h-5" />
        Add Your First Device
      </button>
    </div>
  </div>
)}
```

## File to Modify
- `frontend/src/components/Dashboard/ConsumerDashboard.tsx`

## Testing Steps
1. Login as consumer with multiple devices
2. See device tabs at top
3. Click different tabs to switch devices
4. Verify data updates for selected device
5. Add new device - should appear in tabs
6. Test with 0 devices - should show empty state
7. Test with 1 device - should auto-select
8. Test mobile responsive view

## Benefits
✅ Clean device switching
✅ Clear data attribution  
✅ Scalable design
✅ Better UX
✅ Professional look
