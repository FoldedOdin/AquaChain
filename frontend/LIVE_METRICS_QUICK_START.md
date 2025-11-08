# Live Metrics - Quick Start

## ✅ What's Been Set Up

Your landing page metrics system is now ready for live data! Here's what's available:

### 📁 New Files Created

1. **`src/services/metricsService.ts`** - Fetches metrics from APIs
2. **`src/hooks/useLiveMetrics.ts`** - React hook for components
3. **`src/config/landingPageMetrics.ts`** - Configuration file
4. **`LIVE_METRICS_SETUP.md`** - Complete documentation

### 🎯 Current Mode

**Static Metrics** (default) - Using hardcoded values from config

---

## 🚀 Enable Live Metrics (3 Steps)

### 1. Set Update Interval

Edit `frontend/src/config/landingPageMetrics.ts`:

```typescript
// Line 35: Change from 0 to 60000 (1 minute)
export const METRICS_UPDATE_INTERVAL = 60000;
```

### 2. Set API Endpoint

Edit `frontend/.env`:

```bash
# Add this line with your API URL
REACT_APP_METRICS_API_URL=https://api.yourdomain.com
```

### 3. Rebuild

```bash
cd frontend
npm run build
```

Done! Metrics will now update every minute.

---

## 📊 API Response Format

Your API endpoint should return:

```json
{
  "success": true,
  "data": {
    "uptime": 99.8,
    "responseTime": 28,
    "dataIntegrity": 100,
    "lastUpdated": "2025-01-08T12:00:00Z"
  },
  "timestamp": "2025-01-08T12:00:00Z"
}
```

---

## 🎨 What Users Will See

When live metrics are enabled:

- ✅ Real-time updates every minute
- ✅ "Last updated" timestamp
- ✅ Manual refresh button
- ✅ Loading indicator during updates
- ✅ Automatic fallback if API fails

---

## 🔧 Configuration Options

### Update Frequencies

```typescript
30000   // 30 seconds (frequent)
60000   // 1 minute (recommended)
300000  // 5 minutes (conservative)
0       // Disabled (static only)
```

### Data Sources

```typescript
// In your component
useLiveMetrics({
  source: 'api'         // REST API (default)
  source: 'cloudwatch'  // AWS CloudWatch
  source: 'monitoring'  // Datadog/New Relic/etc
});
```

---

## 📝 Example Backend (Node.js)

```javascript
app.get('/metrics', async (req, res) => {
  res.json({
    success: true,
    data: {
      uptime: 99.8,
      responseTime: 28,
      dataIntegrity: 100,
      lastUpdated: new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  });
});
```

---

## 🧪 Testing

### Test Without API

The system automatically provides mock data for development. Just enable updates:

```typescript
export const METRICS_UPDATE_INTERVAL = 60000;
// Leave REACT_APP_METRICS_API_URL empty
```

You'll see slightly varying metrics to simulate live data.

### Test With API

```bash
# Test your endpoint
curl https://api.yourdomain.com/metrics
```

---

## 🆘 Troubleshooting

**Metrics not updating?**
```typescript
// Check this is > 0
export const METRICS_UPDATE_INTERVAL = 60000;
```

**API errors?**
- Check browser console (F12)
- Verify CORS headers on your API
- Test endpoint with curl

**Still using static values?**
- Rebuild after config changes
- Check .env file exists
- Verify API URL is set

---

## 📚 Full Documentation

See `LIVE_METRICS_SETUP.md` for:
- Complete API implementation examples
- AWS CloudWatch integration
- Monitoring service integration
- Best practices
- Advanced configuration

---

## 🎯 Summary

| Step | File | Change |
|------|------|--------|
| 1 | `config/landingPageMetrics.ts` | Set `METRICS_UPDATE_INTERVAL = 60000` |
| 2 | `.env` | Add `REACT_APP_METRICS_API_URL=...` |
| 3 | Terminal | Run `npm run build` |

That's it! Your metrics are now live. 🎉
