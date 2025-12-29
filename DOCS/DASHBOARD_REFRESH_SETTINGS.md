# Dashboard Auto-Refresh Settings

## Current Configuration ✅

**Refresh Interval:** 60 seconds (1 minute)

**Changed from:** 10 seconds (too frequent)  
**Changed to:** 60 seconds (more reasonable)

---

## Why It Refreshes

The dashboard automatically refreshes to:
- ✅ Show latest water quality readings
- ✅ Update device status
- ✅ Display new alerts
- ✅ Sync with backend changes
- ✅ Keep data fresh

This is **intentional** and **good for user experience**.

---

## Refresh Intervals Explained

| Interval | Frequency | Use Case |
|----------|-----------|----------|
| 5 seconds | Very fast | Real-time monitoring (production systems) |
| 10 seconds | Fast | **Previous setting** - Too frequent for dev |
| 30 seconds | Moderate | Good balance |
| 60 seconds | Slow | **Current setting** - Better for development |
| 120 seconds | Very slow | Minimal updates |
| Disabled | Never | Manual refresh only |

---

## Current Settings by Dashboard

### Consumer Dashboard
- **Interval:** 60 seconds
- **What refreshes:**
  - Water quality readings
  - Device list
  - Alerts
  - Statistics

### Technician Dashboard
- **Interval:** 60 seconds
- **What refreshes:**
  - Assigned tasks/orders
  - Task status updates
  - Recent activities

### Admin Dashboard
- **Interval:** 60 seconds
- **What refreshes:**
  - System health metrics
  - Device fleet status
  - Performance metrics
  - Alert analytics

---

## How to Change Refresh Interval

### Make it Faster (More Frequent)
Edit `frontend/src/hooks/useDashboardData.ts`:

```typescript
const interval = setInterval(fetchData, 30000); // 30 seconds
```

### Make it Slower (Less Frequent)
```typescript
const interval = setInterval(fetchData, 120000); // 2 minutes
```

### Disable Auto-Refresh (Manual Only)
```typescript
// Comment out the interval
// const interval = setInterval(fetchData, 60000);
```

Then users can manually refresh using the refresh button.

---

## Manual Refresh Button

All dashboards have a manual refresh button:
- **Location:** Top right corner
- **Icon:** Circular arrow
- **Action:** Immediately fetches latest data
- **Use:** When you want fresh data without waiting

---

## Performance Impact

### Fast Refresh (10 seconds)
- ✅ Very fresh data
- ❌ More API calls
- ❌ More network traffic
- ❌ Higher server load
- ❌ Can feel "jumpy"

### Moderate Refresh (60 seconds) ✅ **Current**
- ✅ Fresh enough data
- ✅ Reasonable API calls
- ✅ Low network traffic
- ✅ Low server load
- ✅ Smooth experience

### No Auto-Refresh
- ✅ No background traffic
- ✅ Minimal server load
- ❌ Stale data
- ❌ Users must remember to refresh

---

## Recommended Settings

### Development
```typescript
const interval = setInterval(fetchData, 60000); // 1 minute
```
**Why:** Less distracting, easier to debug

### Production
```typescript
const interval = setInterval(fetchData, 30000); // 30 seconds
```
**Why:** Balance between freshness and performance

### Real-time Monitoring
```typescript
const interval = setInterval(fetchData, 5000); // 5 seconds
```
**Why:** Critical systems need instant updates

---

## What Happens During Refresh

1. **Fetch latest data** from backend
2. **Update state** in React
3. **Re-render components** with new data
4. **Smooth transition** (no page reload)

**Note:** Only data changes, not the entire page!

---

## Troubleshooting

### Dashboard feels "jumpy"
**Solution:** Increase interval to 60-120 seconds

### Data seems stale
**Solution:** Decrease interval to 30 seconds or use manual refresh

### Too many API calls
**Solution:** Increase interval or disable auto-refresh

### Want instant updates
**Solution:** Use WebSocket (already implemented via `useRealTimeUpdates`)

---

## WebSocket vs Polling

### Polling (Current Method)
- Checks for updates every X seconds
- Simple to implement
- Works everywhere
- Can be inefficient

### WebSocket (Also Available)
- Server pushes updates instantly
- More efficient
- Real-time
- Already implemented in your app!

**Your app uses BOTH:**
- Polling: Regular data refresh
- WebSocket: Instant notifications

---

## Summary

**Current setting:** Dashboard refreshes every **60 seconds**

**Benefits:**
- ✅ Data stays reasonably fresh
- ✅ Not too frequent (less distracting)
- ✅ Good for development
- ✅ Low server load

**If you want to change it:**
- Edit `frontend/src/hooks/useDashboardData.ts`
- Change the number in `setInterval(fetchData, 60000)`
- Restart app

**Restart required:** Yes, after changing the interval

---

## Quick Reference

```typescript
// File: frontend/src/hooks/useDashboardData.ts
// Line: ~115

const interval = setInterval(fetchData, 60000); // ← Change this number

// Common values:
// 5000   = 5 seconds
// 10000  = 10 seconds
// 30000  = 30 seconds
// 60000  = 1 minute (current)
// 120000 = 2 minutes
// 300000 = 5 minutes
```

---

**Status:** ✅ Changed from 10s to 60s  
**Impact:** Dashboard refreshes less frequently  
**User Experience:** Smoother, less distracting
