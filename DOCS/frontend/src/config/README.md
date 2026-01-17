# Landing Page Configuration

This directory contains configuration files for the landing page that can be updated without modifying component code.

## Metrics Configuration

### File: `landingPageMetrics.ts`

This file controls the metrics displayed on the landing page in the "Proven Reliability" section and footer.

### How to Update Metrics

1. Open `frontend/src/config/landingPageMetrics.ts`
2. Modify the values in the `trustMetrics` array:

```typescript
export const trustMetrics: MetricConfig[] = [
  {
    id: 'uptime',
    value: '99.8%',           // ← Change this value
    label: 'System Uptime',
    description: 'Average uptime over the last 12 months'
  },
  // ... more metrics
];
```

3. Save the file
4. Rebuild the application: `npm run build`

### Available Metrics

- **System Uptime**: Shows overall system availability
- **Alert Response**: Average time to deliver critical alerts
- **Data Integrity**: Blockchain-verified data accuracy

### Adding New Metrics

To add a new metric:

1. Add it to the `trustMetrics` array in `landingPageMetrics.ts`
2. Add the corresponding icon mapping in `FeaturesShowcase.tsx`:

```typescript
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  'uptime': TrendingUpIcon,
  'response-time': ClockIcon,
  'data-integrity': ShieldCheckIcon,
  'your-new-metric': YourNewIcon  // ← Add your icon here
};
```

3. Add the color mapping:

```typescript
const colorMap: Record<string, string> = {
  'uptime': 'aqua',
  'response-time': 'teal',
  'data-integrity': 'emerald',
  'your-new-metric': 'blue'  // ← Add your color here
};
```

### Connecting to Live Data (Optional)

To fetch metrics from an API instead of using static values:

1. Set the API endpoint in `landingPageMetrics.ts`:

```typescript
export const METRICS_API_ENDPOINT = 'https://api.yoursite.com/metrics';
```

2. Set the update interval (in milliseconds):

```typescript
export const METRICS_UPDATE_INTERVAL = 60000; // Update every minute
```

3. Implement the API fetching logic in `FeaturesShowcase.tsx` using the provided constants.

### Footer Metrics

Update footer metrics separately:

```typescript
export const footerMetrics = {
  uptime: '99.8%',        // ← Change uptime percentage
  status: 'Operational'   // ← Change status text
};
```

## Benefits of This Approach

✅ **Easy Updates**: Change metrics without touching component code  
✅ **Type Safety**: TypeScript ensures correct data structure  
✅ **Centralized**: All metrics in one place  
✅ **Flexible**: Can switch between static and dynamic data  
✅ **Maintainable**: Clear separation of data and presentation  

## Example: Updating All Metrics

```typescript
// landingPageMetrics.ts
export const trustMetrics: MetricConfig[] = [
  {
    id: 'uptime',
    value: '99.9%',  // Improved!
    label: 'System Uptime',
    description: 'Average uptime over the last 12 months'
  },
  {
    id: 'response-time',
    value: '<15s',  // Faster!
    label: 'Alert Response',
    description: 'Average time to deliver critical alerts'
  },
  {
    id: 'data-integrity',
    value: '100%',
    label: 'Data Integrity',
    description: 'Blockchain-verified data accuracy'
  }
];
```

Save, rebuild, and your landing page will show the new values!
