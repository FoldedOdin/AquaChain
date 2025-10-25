# Performance Optimizations

This document describes the performance optimizations implemented in the AquaChain frontend application.

## Overview

The following optimizations have been implemented to ensure fast page loads, smooth interactions, and efficient resource usage:

1. **Memoization** - Prevent unnecessary re-renders
2. **Code Splitting** - Lazy load components on demand
3. **Asset Optimization** - Compress and optimize images and bundles
4. **Performance Monitoring** - Track Core Web Vitals and page load metrics

## 1. Memoization

### React.memo for Components

Frequently rendered components are wrapped with `React.memo` to prevent unnecessary re-renders:

- `DataCard` - Dashboard metric cards
- `AlertPanel` - Alert notification panel

### useMemo for Expensive Computations

Expensive computations are memoized using `useMemo`:

```typescript
// Memoize filtered data
const activeDevices = useMemo(
  () => devices.filter(d => d.status === 'online'),
  [devices]
);

// Memoize computed statistics
const taskCounts = useMemo(() => ({
  assigned: tasks.filter(t => t.status === 'assigned').length,
  accepted: tasks.filter(t => t.status === 'accepted').length,
  // ...
}), [tasks]);
```

### useCallback for Event Handlers

Event handlers are memoized using `useCallback` to maintain referential equality:

```typescript
const handleExport = useCallback(async () => {
  await exportData(data, options);
}, [exportData, data, options]);
```

## 2. Code Splitting & Lazy Loading

### Route-Level Code Splitting

Dashboard routes are lazy loaded to reduce initial bundle size:

```typescript
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const TechnicianDashboard = lazy(() => import('./pages/TechnicianDashboard'));
const ConsumerDashboard = lazy(() => import('./components/Dashboard/ConsumerDashboard'));
```

### Component-Level Code Splitting

Heavy admin components are lazy loaded within the AdminDashboard:

- UserManagement
- DeviceManagement
- TechnicianManagement
- ComplianceReporting
- AuditTrailViewer
- SystemConfiguration

### Suspense Boundaries

All lazy-loaded components are wrapped with Suspense boundaries showing loading indicators:

```typescript
<Suspense fallback={<LoadingFallback />}>
  <LazyComponent />
</Suspense>
```

## 3. Asset Optimization

### Webpack Configuration (via CRACO)

Custom webpack configuration optimizes bundle splitting and asset loading:

#### Bundle Splitting Strategy

- **React Vendor Bundle** - React, React DOM, React Router
- **AWS Vendor Bundle** - AWS SDK, Amplify libraries
- **Charts Vendor Bundle** - Recharts, D3
- **Common Bundle** - Shared code between chunks
- **Runtime Bundle** - Webpack runtime code

#### Image Optimization

Images are automatically optimized during build:

- **JPEG** - Compressed with mozjpeg (quality: 75%)
- **PNG** - Compressed with pngquant (quality: 65-90%)
- **SVG** - Optimized with svgo
- **WebP** - Generated WebP versions for modern browsers

Small images (<8KB) are inlined as data URLs.

### Performance Budget

Bundle size limits are enforced:

- **Main Bundle**: 500 KB
- **Vendor Bundle**: 800 KB
- **Total Bundle**: 1000 KB

Check bundle size:
```bash
npm run build:check
```

Analyze bundle composition:
```bash
npm run build:analyze
```

## 4. Performance Monitoring

### Core Web Vitals Tracking

The application tracks all Core Web Vitals metrics:

- **LCP** (Largest Contentful Paint) - Target: < 2.5s
- **FID** (First Input Delay) - Target: < 100ms
- **CLS** (Cumulative Layout Shift) - Target: < 0.1
- **FCP** (First Contentful Paint) - Target: < 1.8s
- **TTFB** (Time to First Byte) - Target: < 800ms

### Performance Monitor Service

The `performanceMonitor` service automatically tracks:

- Page load time (warns if > 3 seconds)
- Core Web Vitals
- Long tasks (> 50ms)
- Custom performance marks and measures

### Performance Monitoring Hook

Components can use the `usePerformanceMonitor` hook:

```typescript
const { getMetrics, measureOperation, logMetrics } = usePerformanceMonitor({
  componentName: 'AdminDashboard',
  trackRenderTime: true,
  trackMountTime: true,
  renderTimeThreshold: 16 // 60fps
});

// Measure an operation
measureOperation('data-fetch', async () => {
  await fetchData();
});

// Log metrics
logMetrics();
```

### Data Fetch Performance

Track data fetching performance:

```typescript
const { startTracking, endTracking } = useDataFetchPerformance('fetch-devices');

startTracking();
const data = await fetchDevices();
const duration = endTracking(); // Warns if > 500ms
```

## Performance Targets

### Page Load Performance

- **Initial Page Load**: < 3 seconds
- **Dashboard Load**: < 2 seconds
- **Component Render**: < 16ms (60fps)

### Bundle Size

- **Initial Bundle**: < 500 KB
- **Total Assets**: < 1 MB
- **Lazy Chunks**: < 200 KB each

### Core Web Vitals

- **LCP**: < 2.5 seconds (Good)
- **FID**: < 100ms (Good)
- **CLS**: < 0.1 (Good)

## Best Practices

### When to Use Memoization

✅ **Use memoization when:**
- Computing expensive derived data
- Filtering/sorting large arrays
- Creating callback functions passed to child components
- Rendering components with expensive render logic

❌ **Avoid memoization when:**
- The computation is trivial
- Props change frequently
- The component rarely re-renders

### When to Use Code Splitting

✅ **Use code splitting for:**
- Route-level components
- Heavy third-party libraries
- Admin/management features
- Rarely used components

❌ **Avoid code splitting for:**
- Small components
- Frequently used components
- Critical path components

### Performance Monitoring

- Monitor performance in production
- Set up alerts for poor metrics
- Review performance reports regularly
- Test on various devices and networks

## Testing Performance

### Local Testing

```bash
# Build and check bundle size
npm run build:check

# Analyze bundle composition
npm run build:analyze

# Run Lighthouse audit
npm run lighthouse
```

### Production Monitoring

Performance metrics are automatically sent to:
- Google Analytics (if configured)
- AWS Pinpoint (if configured)
- Browser console (development mode)

## Troubleshooting

### Large Bundle Size

1. Run bundle analyzer: `npm run build:analyze`
2. Identify large dependencies
3. Consider alternatives or lazy loading
4. Remove unused code

### Slow Page Load

1. Check Network tab in DevTools
2. Identify slow resources
3. Optimize or lazy load heavy resources
4. Enable caching

### Poor Core Web Vitals

1. Check performance monitor logs
2. Identify problematic components
3. Add memoization or code splitting
4. Optimize images and assets

## Future Optimizations

Potential future improvements:

- [ ] Service Worker for offline support
- [ ] HTTP/2 Server Push
- [ ] Preload critical resources
- [ ] Resource hints (prefetch, preconnect)
- [ ] Progressive image loading
- [ ] Virtual scrolling for long lists
- [ ] Web Workers for heavy computations

## Resources

- [Web Vitals](https://web.dev/vitals/)
- [React Performance](https://react.dev/learn/render-and-commit)
- [Webpack Code Splitting](https://webpack.js.org/guides/code-splitting/)
- [Image Optimization](https://web.dev/fast/#optimize-your-images)
