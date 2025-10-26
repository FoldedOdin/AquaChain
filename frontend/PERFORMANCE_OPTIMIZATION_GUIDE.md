# AquaChain Frontend Performance Optimization Guide

Quick reference for implementing performance best practices in the AquaChain frontend.

---

## 1. Component Optimization

### Use React.memo for Pure Components

```typescript
// ❌ Bad: Component re-renders on every parent update
const MyComponent: React.FC<Props> = ({ data }) => {
  return <div>{data.value}</div>;
};

// ✅ Good: Component only re-renders when props change
const MyComponent = memo<Props>(({ data }) => {
  return <div>{data.value}</div>;
});

MyComponent.displayName = 'MyComponent';
```

### Use useMemo for Expensive Computations

```typescript
// ❌ Bad: Calculation runs on every render
const MyComponent = ({ readings }) => {
  const average = readings.reduce((sum, r) => sum + r.value, 0) / readings.length;
  return <div>{average}</div>;
};

// ✅ Good: Calculation only runs when readings change
const MyComponent = ({ readings }) => {
  const average = useMemo(() => {
    return readings.reduce((sum, r) => sum + r.value, 0) / readings.length;
  }, [readings]);
  
  return <div>{average}</div>;
};
```

### Use useCallback for Event Handlers

```typescript
// ❌ Bad: New function created on every render
const MyComponent = ({ onSave }) => {
  const handleClick = () => {
    onSave();
  };
  
  return <button onClick={handleClick}>Save</button>;
};

// ✅ Good: Function reference stays stable
const MyComponent = ({ onSave }) => {
  const handleClick = useCallback(() => {
    onSave();
  }, [onSave]);
  
  return <button onClick={handleClick}>Save</button>;
};
```

---

## 2. Data Fetching with React Query

### Basic Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../lib/react-query';

function useWaterQualityData(timeRange: string) {
  return useQuery({
    queryKey: queryKeys.waterQuality.list(timeRange),
    queryFn: () => dataService.getWaterQualityData(timeRange),
    staleTime: 30000,        // Data fresh for 30 seconds
    refetchInterval: 60000,  // Refetch every minute
  });
}

// Usage in component
const MyComponent = () => {
  const { data, isLoading, error } = useWaterQualityData('24h');
  
  if (isLoading) return <Loading />;
  if (error) return <Error message={error.message} />;
  
  return <div>{data.map(/* ... */)}</div>;
};
```

### Mutation with Optimistic Updates

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useUpdateDevice() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (device) => api.updateDevice(device),
    onMutate: async (newDevice) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['devices'] });
      
      // Snapshot previous value
      const previous = queryClient.getQueryData(['devices']);
      
      // Optimistically update
      queryClient.setQueryData(['devices'], (old) => 
        old.map(d => d.id === newDevice.id ? newDevice : d)
      );
      
      return { previous };
    },
    onError: (err, newDevice, context) => {
      // Rollback on error
      queryClient.setQueryData(['devices'], context.previous);
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });
}
```

### Prefetching Data

```typescript
import { useQueryClient } from '@tanstack/react-query';

const MyComponent = () => {
  const queryClient = useQueryClient();
  
  const handleMouseEnter = () => {
    // Prefetch data before user clicks
    queryClient.prefetchQuery({
      queryKey: ['device', deviceId],
      queryFn: () => api.getDevice(deviceId),
    });
  };
  
  return <button onMouseEnter={handleMouseEnter}>View Device</button>;
};
```

---

## 3. Code Splitting & Lazy Loading

### Lazy Load Routes

```typescript
import { lazy, Suspense } from 'react';

// ✅ Lazy load dashboard components
const ConsumerDashboard = lazy(() => import('./components/Dashboard/ConsumerDashboard'));
const AdminDashboard = lazy(() => import('./components/Dashboard/AdminDashboard'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard/consumer" element={<ConsumerDashboard />} />
        <Route path="/dashboard/admin" element={<AdminDashboard />} />
      </Routes>
    </Suspense>
  );
}
```

### Lazy Load Heavy Components

```typescript
// ✅ Lazy load chart library
const WaterQualityChart = lazy(() => import('./components/Charts/WaterQualityChart'));

const Dashboard = () => {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <WaterQualityChart data={data} />
        </Suspense>
      )}
    </div>
  );
};
```

---

## 4. List Rendering Optimization

### Use Keys Properly

```typescript
// ❌ Bad: Using index as key
{items.map((item, index) => (
  <Item key={index} data={item} />
))}

// ✅ Good: Using stable unique ID
{items.map((item) => (
  <Item key={item.id} data={item} />
))}
```

### Virtualize Long Lists

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualList = ({ items }) => {
  const parentRef = useRef();
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });
  
  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 5. Image Optimization

### Use WebP Format

```typescript
// ✅ Provide WebP with fallback
<picture>
  <source srcSet="/images/logo.webp" type="image/webp" />
  <img src="/images/logo.png" alt="Logo" />
</picture>
```

### Lazy Load Images

```typescript
// ✅ Native lazy loading
<img 
  src="/images/chart.png" 
  alt="Chart" 
  loading="lazy"
  decoding="async"
/>
```

---

## 6. Bundle Size Optimization

### Dynamic Imports

```typescript
// ❌ Bad: Import entire library
import { format, parse, addDays } from 'date-fns';

// ✅ Good: Import only what you need
import format from 'date-fns/format';
import addDays from 'date-fns/addDays';
```

### Lazy Load AWS SDK

```typescript
// ✅ Load AWS SDK only when needed
const loadAmplifyAuth = async () => {
  const { signIn, signOut } = await import('aws-amplify/auth');
  return { signIn, signOut };
};

// Usage
const handleLogin = async () => {
  const auth = await loadAmplifyAuth();
  await auth.signIn(credentials);
};
```

---

## 7. Error Handling

### Use Error Boundaries

```typescript
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  );
}
```

### Handle Query Errors

```typescript
const { data, error, isError } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
});

if (isError) {
  return <ErrorMessage error={error} />;
}
```

---

## 8. Performance Monitoring

### Track Component Renders

```typescript
import { useEffect, useRef } from 'react';

function useRenderCount(componentName: string) {
  const renderCount = useRef(0);
  
  useEffect(() => {
    renderCount.current += 1;
    console.log(`${componentName} rendered ${renderCount.current} times`);
  });
}

// Usage
const MyComponent = () => {
  useRenderCount('MyComponent');
  // ...
};
```

### Measure Performance

```typescript
import { useEffect } from 'react';

const MyComponent = () => {
  useEffect(() => {
    const start = performance.now();
    
    // Expensive operation
    processData();
    
    const end = performance.now();
    console.log(`Processing took ${end - start}ms`);
  }, []);
};
```

---

## 9. Common Pitfalls to Avoid

### ❌ Don't Create Objects/Arrays in Render

```typescript
// ❌ Bad: New object created on every render
<MyComponent config={{ theme: 'dark', size: 'large' }} />

// ✅ Good: Stable reference
const config = useMemo(() => ({ theme: 'dark', size: 'large' }), []);
<MyComponent config={config} />
```

### ❌ Don't Use Inline Functions in Props

```typescript
// ❌ Bad: New function on every render
<button onClick={() => handleClick(id)}>Click</button>

// ✅ Good: Stable function reference
const handleButtonClick = useCallback(() => handleClick(id), [id]);
<button onClick={handleButtonClick}>Click</button>
```

### ❌ Don't Fetch Data in Render

```typescript
// ❌ Bad: Fetching in render
const MyComponent = () => {
  const data = fetchData(); // This runs on every render!
  return <div>{data}</div>;
};

// ✅ Good: Use React Query
const MyComponent = () => {
  const { data } = useQuery({
    queryKey: ['data'],
    queryFn: fetchData,
  });
  return <div>{data}</div>;
};
```

---

## 10. Performance Checklist

Before deploying, verify:

- [ ] All dashboard components use `React.memo()`
- [ ] Expensive computations use `useMemo()`
- [ ] Event handlers use `useCallback()`
- [ ] Data fetching uses React Query
- [ ] Routes are lazy loaded
- [ ] Images are optimized (WebP, lazy loading)
- [ ] Bundle size is < 500KB (scripts)
- [ ] Error boundaries are in place
- [ ] No console.log in production
- [ ] React DevTools Profiler shows no unnecessary renders

---

## Resources

- [React Query Docs](https://tanstack.com/query/latest)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)

---

**Last Updated:** October 26, 2025  
**Maintained By:** Frontend Team
