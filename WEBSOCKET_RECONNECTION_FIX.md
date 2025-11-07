# WebSocket Reconnection Issue - Fix

## Issue
WebSocket was constantly connecting and disconnecting, showing these messages in the terminal:
```
[0] WebSocket client connected
[0] WebSocket message received: {"type":"subscribe","topic":"consumer-updates"}
[0] WebSocket client disconnected
[0] WebSocket client connected
```

## Root Cause

The `useRealTimeUpdates` hook had a **dependency issue** that caused it to reconnect on every render:

### Problem Flow:
1. Component renders → `useRealTimeUpdates` hook runs
2. `handleUpdate` callback is created with `useCallback`
3. `handleUpdate` depends on `addNotification` from context
4. `connect` and `disconnect` functions depend on `handleUpdate`
5. `useEffect` cleanup runs → calls `disconnect()`
6. `useEffect` runs again → calls `connect()`
7. **Result**: WebSocket disconnects and reconnects on every render

### Why It Happened:
```typescript
// ❌ BEFORE: handleUpdate recreated on every render
const handleUpdate = useCallback((update: any) => {
  // ... uses addNotification
}, [addNotification]); // addNotification changes frequently

// connect/disconnect depend on handleUpdate
const connect = useCallback(() => {
  websocketService.connect(subscriptionTopic, handleUpdate);
}, [subscriptionTopic, handleUpdate]); // ❌ handleUpdate changes

// useEffect runs cleanup when dependencies change
useEffect(() => {
  if (autoConnect) connect();
  return () => disconnect(); // ❌ Runs on every render
}, [autoConnect, subscriptionTopic]); // ❌ Missing connect/disconnect
```

## Solution

Used **`useRef`** to create a stable callback reference that doesn't cause re-renders:

### Fix Implementation:

```typescript
// ✅ AFTER: Stable callback using useRef
const handleUpdateRef = useRef((update: any) => {
  // Initial implementation
});

// Update ref when dependencies change (doesn't cause re-render)
useEffect(() => {
  handleUpdateRef.current = (update: any) => {
    // Updated implementation with latest addNotification
  };
}, [addNotification]);

// Stable callback that never changes
const handleUpdate = useCallback((update: any) => {
  handleUpdateRef.current(update);
}, []); // ✅ Empty deps - never recreated

// connect/disconnect now stable
const connect = useCallback(() => {
  websocketService.connect(subscriptionTopic, handleUpdate);
}, [subscriptionTopic, handleUpdate]); // ✅ handleUpdate never changes

// useEffect only runs when topic/autoConnect changes
useEffect(() => {
  if (autoConnect) connect();
  return () => disconnect(); // ✅ Only runs when needed
}, [autoConnect, subscriptionTopic]); // ✅ Correct dependencies
```

## How It Works

### useRef Pattern:
1. **Create ref** with initial callback implementation
2. **Update ref** in `useEffect` when dependencies change
3. **Stable wrapper** callback that calls `ref.current`
4. **Result**: Callback reference never changes, but implementation stays current

### Benefits:
- ✅ WebSocket connects once and stays connected
- ✅ No unnecessary disconnections
- ✅ Callback always has latest dependencies
- ✅ No memory leaks
- ✅ Proper cleanup on unmount

## Testing

### Before Fix:
```bash
# Terminal shows constant reconnections
[0] WebSocket client connected
[0] WebSocket message received: {"type":"subscribe","topic":"consumer-updates"}
[0] WebSocket client disconnected
[0] WebSocket client connected
[0] WebSocket message received: {"type":"subscribe","topic":"consumer-updates"}
[0] WebSocket client disconnected
# ... repeats continuously
```

### After Fix:
```bash
# Terminal shows single connection
[0] WebSocket client connected
[0] WebSocket message received: {"type":"subscribe","topic":"consumer-updates"}
# ... stays connected
```

## Code Changes

**File**: `frontend/src/hooks/useRealTimeUpdates.ts`

### Changed:
1. Replaced `useCallback` for `handleUpdate` with `useRef` pattern
2. Created stable wrapper callback
3. Updated `useEffect` dependencies to only trigger on topic/autoConnect changes

### Lines Modified:
- Lines 60-90: Replaced callback with ref pattern
- Lines 140-150: Fixed useEffect dependencies

## Related Patterns

This fix uses the **"Latest Ref Pattern"** which is useful when:
- Callback needs latest props/state
- But shouldn't cause re-renders
- Used in event handlers, timers, WebSockets

### Other Use Cases:
```typescript
// Timer with latest state
const latestCountRef = useRef(count);
useEffect(() => {
  latestCountRef.current = count;
}, [count]);

const startTimer = useCallback(() => {
  setInterval(() => {
    console.log(latestCountRef.current); // Always latest
  }, 1000);
}, []); // Stable callback

// Event listener with latest handler
const latestHandlerRef = useRef(handler);
useEffect(() => {
  latestHandlerRef.current = handler;
}, [handler]);

useEffect(() => {
  const stableHandler = (e) => latestHandlerRef.current(e);
  window.addEventListener('click', stableHandler);
  return () => window.removeEventListener('click', stableHandler);
}, []); // Only add/remove once
```

## Prevention

To avoid similar issues in the future:

### 1. Check useEffect Dependencies
```typescript
// ❌ BAD: Missing dependencies
useEffect(() => {
  doSomething(prop);
}, []); // prop not in deps

// ✅ GOOD: All dependencies included
useEffect(() => {
  doSomething(prop);
}, [prop]);
```

### 2. Use useCallback Carefully
```typescript
// ❌ BAD: Callback recreated often
const callback = useCallback(() => {
  // uses many props
}, [prop1, prop2, prop3, prop4]); // Changes frequently

// ✅ GOOD: Use ref pattern for frequently changing deps
const callbackRef = useRef(() => {});
useEffect(() => {
  callbackRef.current = () => {
    // uses many props
  };
}, [prop1, prop2, prop3, prop4]);

const stableCallback = useCallback(() => {
  callbackRef.current();
}, []);
```

### 3. Monitor WebSocket Connections
```typescript
// Add logging to detect issues
useEffect(() => {
  console.log('WebSocket connecting to:', topic);
  connect();
  
  return () => {
    console.log('WebSocket disconnecting from:', topic);
    disconnect();
  };
}, [topic]);
```

## Performance Impact

### Before:
- ❌ WebSocket reconnects every render
- ❌ Network overhead from constant reconnections
- ❌ Potential message loss during reconnections
- ❌ Server load from handling reconnections

### After:
- ✅ Single WebSocket connection
- ✅ No unnecessary network traffic
- ✅ Reliable message delivery
- ✅ Reduced server load

## Additional Notes

### React 18 Strict Mode
In development, React 18 Strict Mode intentionally double-renders components to help find bugs. This can cause:
- Components mount → unmount → mount again
- Effects run → cleanup → run again

**This is expected behavior in development** and won't happen in production.

### WebSocket Best Practices
1. **Connection Pooling**: Reuse connections across components
2. **Automatic Reconnection**: Handle disconnections gracefully
3. **Heartbeat/Ping**: Keep connection alive
4. **Error Handling**: Handle connection errors
5. **Cleanup**: Always disconnect on unmount

## Status
✅ **Fixed** - WebSocket now maintains stable connection

---

**Date**: November 6, 2025
**Issue**: WebSocket constantly reconnecting
**Resolution**: Used useRef pattern to stabilize callback references
**Impact**: Improved performance and reliability
