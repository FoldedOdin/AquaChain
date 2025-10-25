# React Performance Optimizations - Quick Reference

## Overview
This guide provides quick reference for the performance optimizations implemented in the AquaChain frontend.

---

## 🚀 Memoization

### When to Use useMemo
Use `useMemo` for expensive computations that depend on specific values:

```typescript
// ✅ Good: Expensive filtering operation
const filteredDevices = useMemo(
  () => devices.filter(d => d.status === 'online'),
  [devices]
);

// ❌ Bad: Simple value access
const userName = useMemo(() => user.name, [user]); // Overkill
```

### When to Use useCallback
Use `useCallback` for functions passed as props to memoized components:

```typescript
// ✅ Good: Callback passed to child component
const handleClick = useCallback((id: string) => {
  navigate(`/device/${id}`);
}, [navigate]);

// ❌ Bad: Function not passed to children
const handleClick = useCallback(() => {
  console.log('clicked');
}, []); // Unnecessary
```

### When to Use React.memo
Use `React.memo` for components that render frequently with the same props:

```typescript
// ✅ Good: Frequently rendered with same props
export const DataCard = React.memo(DataCardComponent, (prev, next) => {
  return prev.value === next.value && prev.title === next.title;
});

// ❌ Bad: Component rarely re-renders
export const Header = React.memo(HeaderComponent); // Probably unnecessary
```

---

## 📦 Code Splitting

### Lazy Loading Routes
```typescript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Dashboard />
    </Suspense>
  );
}
```

### Lazy Loading Components
```typescript
// Heavy components that aren't immediately needed
const ChartComponent = lazy(() => import('./components/Chart'));
const MapComponent = lazy(() => import('./components/Map'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));
```

### Loading Fallbacks
```typescript
const LoadingFallback = () => (
  <div className="flex items-center justify-center p-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
    <p className="ml-3 text-gray-600">Loading...</p>
  </div>
);
```

---

## 🖼️ Image Optimization

### Using Optimized Images
```typescript
import { OptimizedPicture } from '../utils/imageOptimization';

// Automatically generates WebP, AVIF, and JPEG sources
<OptimizedPicture
  basePath="/images"
  filename="device-photo.jpg"
  alt="Water quality device"
  loading="lazy"
  priority={false}
/>
```

### Lazy Background Images
```typescript
import { useLazyBackgroundImage } from '../utils/imageOptimization';

function HeroSection() {
  const { elementRef, backgroundImage, isLoaded } = useLazyBackgroundImage(
    '/images/hero-bg.jpg',
    '/images/hero-placeholder.jpg'
  );

  return (
    <div
      ref={elementRef}
      style={{ backgroundImage }}
      className={isLoaded ? 'loaded' : 'loading'}
    />
  );
}
```

### Client-Side Compression
```typescript
import { compressImage } from '../utils/imageOptimization';

async function handleImageUpload(file: File) {
  const compressed = await compressImage(file, 1920, 1080, 0.8);
  // Upload compressed blob
}
```

---

## 📊 Performance Monitoring

### Component Performance Tracking
```typescript
import { usePerformanceMonitor } from '../hooks/usePerformanceMonitor';

function Dashboard() {
  const { measureOperation, logMetrics } = usePerformanceMonitor({
    componentName: 'Dashboard',
    trackRenderTime: true,
    trackMountTime: true,
    renderTimeThreshold: 16 // 60fps
  });

  const handleDataFetch = async () => {
    await measureOperation('data-fetch', async () => {
      const data = await fetchDashboardData();
      setData(data);
    });
  };

  return <div>...</div>;
}
```

### Data Fetch Performance
```typescript
import { useDataFetchPerformance } from '../hooks/usePerformanceMonitor';

function useDeviceData(deviceId: string) {
  const { startTracking, endTracking } = useDataFetchPerformance('fetch-device-data');

  useEffect(() => {
    startTracking();
    fetchDeviceData(deviceId).then(data => {
      endTracking();
      setData(data);
    });
  }, [deviceId]);
}
```

### Manual Performance Marks
```typescript
import performanceMonitor from '../services/performanceMonitor';

// Mark start of operation
performanceMonitor.mark('data-processing-start');

// ... do work ...

// Mark end and measure
performanceMonitor.mark('data-processing-end');
const duration = performanceMonitor.measure(
  'data-processing',
  'data-processing-start',
  'data-processing-end'
);
```

---

## 🔧 Build Commands

### Development
```bash
npm start                    # Start dev server
npm run start:full          # Start with backend
```

### Production Build
```bash
npm run build               # Standard production build
npm run build:analyze       # Build with bundle analysis
npm run build:check         # Build and check bundle size
```

### Performance Testing
```bash
npm run lighthouse          # Run Lighthouse audit
npm run lighthouse:ci       # Run Lighthouse in CI mode
npm run performance:budget  # Check performance budgets
```

---

## 📏 Performance Budgets

### Bundle Size Limits
- **Main Bundle**: 500 KB
- **Vendor Bundle**: 800 KB
- **Total Bundle**: 1000 KB
- **Images**: 200 KB
- **Stylesheets**: 100 KB

### Timing Budgets
- **First Contentful Paint**: < 2000ms
- **Largest Contentful Paint**: < 3000ms
- **Time to Interactive**: < 5000ms
- **Cumulative Layout Shift**: < 0.1
- **Total Blocking Time**: < 300ms

---

## ⚠️ Common Pitfalls

### 1. Over-Memoization
```typescript
// ❌ Bad: Memoizing everything
const value = useMemo(() => props.value, [props.value]); // Unnecessary

// ✅ Good: Only memoize expensive operations
const processedData = useMemo(() => 
  expensiveProcessing(rawData), 
  [rawData]
);
```

### 2. Incorrect Dependencies
```typescript
// ❌ Bad: Missing dependencies
const handleClick = useCallback(() => {
  console.log(userId); // userId not in deps
}, []);

// ✅ Good: All dependencies included
const handleClick = useCallback(() => {
  console.log(userId);
}, [userId]);
```

### 3. Lazy Loading Critical Content
```typescript
// ❌ Bad: Lazy loading above-the-fold content
const Hero = lazy(() => import('./Hero')); // User sees loading spinner

// ✅ Good: Only lazy load below-the-fold or heavy components
const AdminPanel = lazy(() => import('./AdminPanel'));
```

### 4. Not Using Loading States
```typescript
// ❌ Bad: No loading indicator
<Suspense fallback={null}>
  <HeavyComponent />
</Suspense>

// ✅ Good: Clear loading indicator
<Suspense fallback={<LoadingSpinner />}>
  <HeavyComponent />
</Suspense>
```

---

## 🎯 Best Practices

### 1. Measure Before Optimizing
- Use React DevTools Profiler
- Check bundle size regularly
- Monitor Core Web Vitals
- Profile in production mode

### 2. Optimize Strategically
- Focus on user-facing performance
- Optimize critical rendering path
- Lazy load non-critical resources
- Compress and optimize images

### 3. Monitor Continuously
- Track performance metrics
- Set up alerts for regressions
- Review bundle size in CI/CD
- Use Lighthouse CI

### 4. Test on Real Devices
- Test on slow networks
- Test on low-end devices
- Test with real user data
- Monitor production metrics

---

## 📚 Additional Resources

### Documentation
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Web Vitals](https://web.dev/vitals/)
- [Webpack Code Splitting](https://webpack.js.org/guides/code-splitting/)

### Tools
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [webpack-bundle-analyzer](https://github.com/webpack-contrib/webpack-bundle-analyzer)

### Internal Docs
- `PERFORMANCE_OPTIMIZATIONS_COMPLETE.md` - Full implementation details
- `TASK_10_PERFORMANCE_OPTIMIZATIONS_SUMMARY.md` - Task completion summary

---

## 🆘 Troubleshooting

### Bundle Size Too Large
1. Run `npm run build:analyze` to identify large dependencies
2. Check for duplicate dependencies
3. Consider lazy loading more components
4. Review and remove unused dependencies

### Slow Page Load
1. Check Core Web Vitals in browser DevTools
2. Use Lighthouse to identify bottlenecks
3. Review network waterfall
4. Check for render-blocking resources

### Performance Regression
1. Compare bundle sizes before/after changes
2. Run performance tests in CI/CD
3. Check for new heavy dependencies
4. Review recent code changes

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**Maintained By**: AquaChain Development Team
