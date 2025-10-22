# AquaChain Dashboard Style Guide

## Overview

This style guide defines the visual design system, components, and patterns for the AquaChain Dashboard interface. It ensures consistency across all dashboard views and provides guidelines for developers and designers.

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Layout & Grid](#layout--grid)
5. [Components](#components)
6. [Icons & Imagery](#icons--imagery)
7. [Animation & Motion](#animation--motion)
8. [Accessibility](#accessibility)
9. [Code Examples](#code-examples)

---

## Design Principles

### 1. **Clarity First**

- Information hierarchy is clear and logical
- Critical water quality data is immediately visible
- Status indicators use universally understood colors and symbols

### 2. **Real-time Focus**

- Live data updates are smooth and non-disruptive
- Timestamps are always visible
- Loading states provide clear feedback

### 3. **Trust & Reliability**

- Consistent visual language builds confidence
- Error states are clear and actionable
- Data integrity indicators are prominent

### 4. **Responsive Design**

- Mobile-first approach for field technicians
- Adaptive layouts for different screen sizes
- Touch-friendly interface elements

---

## Color System

### Primary Palette

```css
/* Aqua (Primary Brand) */
--color-aqua-50: #f0fdfa; /* Lightest backgrounds */
--color-aqua-100: #ccfbf1; /* Light backgrounds */
--color-aqua-200: #99f6e4; /* Subtle accents */
--color-aqua-300: #5eead4; /* Hover states */
--color-aqua-400: #2dd4bf; /* Interactive elements */
--color-aqua-500: #06b6d4; /* Primary actions */
--color-aqua-600: #0891b2; /* Active states */
--color-aqua-700: #0e7490; /* Dark accents */
--color-aqua-800: #155e75; /* Headers */
--color-aqua-900: #164e63; /* Text on light */
```

### Status Colors

```css
/* Water Quality Status */
--color-excellent: #10b981; /* WQI 90-100 */
--color-good: #06b6d4; /* WQI 70-89 */
--color-fair: #f59e0b; /* WQI 50-69 */
--color-poor: #ef4444; /* WQI 25-49 */
--color-critical: #dc2626; /* WQI 0-24 */
```

### Usage Guidelines

- **Primary Actions**: Use `aqua-500` for main CTAs
- **Status Indicators**: Use semantic colors for water quality status
- **Backgrounds**: Use `aqua-50` for subtle backgrounds, white for cards
- **Text**: Use `gray-900` for primary text, `gray-600` for secondary

---

## Typography

### Font Stack

```css
font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif;
```

### Type Scale

```css
/* Headings */
.text-3xl {
  font-size: 1.875rem;
  line-height: 2.25rem;
} /* Page titles */
.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
} /* Section headers */
.text-xl {
  font-size: 1.25rem;
  line-height: 1.75rem;
} /* Card titles */
.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
} /* Subheadings */

/* Body Text */
.text-base {
  font-size: 1rem;
  line-height: 1.5rem;
} /* Default body */
.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
} /* Small text */
.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
} /* Captions */
```

### Font Weights

- **Bold (700)**: Page titles, important metrics
- **Semibold (600)**: Section headers, card titles
- **Medium (500)**: Interactive elements, labels
- **Regular (400)**: Body text, descriptions

---

## Layout & Grid

### Container Widths

```css
.container-sm {
  max-width: 640px;
} /* Mobile dashboards */
.container-md {
  max-width: 768px;
} /* Tablet dashboards */
.container-lg {
  max-width: 1024px;
} /* Desktop dashboards */
.container-xl {
  max-width: 1280px;
} /* Large screens */
```

### Grid System

```css
/* Main dashboard layout */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 2fr 1fr; /* 2/3 main content, 1/3 sidebar */
  }
}
```

### Spacing Scale

```css
/* Consistent spacing using Tailwind scale */
.space-1 {
  margin: 0.25rem;
} /* 4px */
.space-2 {
  margin: 0.5rem;
} /* 8px */
.space-3 {
  margin: 0.75rem;
} /* 12px */
.space-4 {
  margin: 1rem;
} /* 16px */
.space-6 {
  margin: 1.5rem;
} /* 24px */
.space-8 {
  margin: 2rem;
} /* 32px */
```

---

## Components

### 1. Cards

```css
.dashboard-card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  padding: 1.5rem;
}

.dashboard-card-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}
```

### 2. Status Indicators

```css
.status-excellent {
  background: #10b981;
  color: white;
}
.status-good {
  background: #06b6d4;
  color: white;
}
.status-fair {
  background: #f59e0b;
  color: white;
}
.status-poor {
  background: #ef4444;
  color: white;
}
```

### 3. Metrics Display

```css
.metric-large {
  font-size: 2.25rem;
  font-weight: 700;
  line-height: 1;
}

.metric-medium {
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.2;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### 4. Buttons

```css
/* Primary button */
.btn-primary {
  background: #06b6d4;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #0891b2;
  transform: translateY(-1px);
}

/* Secondary button */
.btn-secondary {
  background: white;
  color: #06b6d4;
  border: 1px solid #06b6d4;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
}
```

### 5. Data Tables

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f9fafb;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
}
```

---

## Icons & Imagery

### Icon System

- **Library**: Heroicons (outline and solid variants)
- **Size Scale**: 16px, 20px, 24px, 32px
- **Color**: Match text color or use brand colors for emphasis

### Common Icons

```jsx
// Status icons
<CheckCircleIcon className="w-5 h-5 text-green-500" />
<ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
<XCircleIcon className="w-5 h-5 text-red-500" />

// Navigation icons
<ChartBarIcon className="w-5 h-5" />
<Cog6ToothIcon className="w-5 h-5" />
<BellIcon className="w-5 h-5" />
```

### Data Visualization

- **Charts**: Use aqua color palette with good contrast
- **Gauges**: Circular progress with status colors
- **Trends**: Line charts with smooth curves

---

## Animation & Motion

### Transition Timing

```css
/* Standard transitions */
.transition-fast {
  transition-duration: 150ms;
}
.transition-normal {
  transition-duration: 300ms;
}
.transition-slow {
  transition-duration: 500ms;
}

/* Easing functions */
.ease-out {
  transition-timing-function: cubic-bezier(0, 0, 0.2, 1);
}
.ease-bounce {
  transition-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

### Loading States

```css
.loading-skeleton {
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

### Hover Effects

```css
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.hover-glow:hover {
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
}
```

---

## Accessibility

### Color Contrast

- **Text on white**: Minimum 4.5:1 ratio
- **Interactive elements**: Minimum 3:1 ratio
- **Status indicators**: Use icons + color, not color alone

### Focus States

```css
.focus-visible:focus {
  outline: 2px solid #06b6d4;
  outline-offset: 2px;
}
```

### Screen Reader Support

```jsx
// Always include aria-labels for data
<div aria-label="Water Quality Index: 85, Good">
  <span className="sr-only">Water Quality Index</span>
  85
</div>

// Use semantic HTML
<main role="main">
  <section aria-labelledby="dashboard-title">
    <h1 id="dashboard-title">Water Quality Dashboard</h1>
  </section>
</main>
```

---

## Code Examples

### Dashboard Card Component

```jsx
const DashboardCard = ({ title, children, className = "" }) => (
  <div
    className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
  >
    {title && (
      <div className="mb-4 pb-3 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
    )}
    {children}
  </div>
);
```

### Status Badge Component

```jsx
const StatusBadge = ({ status, children }) => {
  const statusClasses = {
    excellent: "bg-green-100 text-green-800",
    good: "bg-blue-100 text-blue-800",
    fair: "bg-yellow-100 text-yellow-800",
    poor: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClasses[status]}`}
    >
      {children}
    </span>
  );
};
```

### Metric Display Component

```jsx
const MetricDisplay = ({ value, label, unit, trend }) => (
  <div className="text-center">
    <div className="text-2xl font-bold text-gray-900">
      {value}
      {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
    </div>
    <div className="text-sm text-gray-600 mt-1">{label}</div>
    {trend && (
      <div
        className={`text-xs mt-1 ${
          trend > 0 ? "text-green-600" : "text-red-600"
        }`}
      >
        {trend > 0 ? "↗" : "↘"} {Math.abs(trend)}%
      </div>
    )}
  </div>
);
```

---

## Responsive Breakpoints

```css
/* Mobile First Approach */
.dashboard-responsive {
  /* Mobile: 320px+ */
  padding: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  /* Small tablets: 640px+ */
  .dashboard-responsive {
    padding: 1.5rem;
  }
}

@media (min-width: 768px) {
  /* Tablets: 768px+ */
  .dashboard-responsive {
    padding: 2rem;
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  /* Desktop: 1024px+ */
  .dashboard-responsive {
    grid-template-columns: 2fr 1fr;
  }
}

@media (min-width: 1280px) {
  /* Large screens: 1280px+ */
  .dashboard-responsive {
    max-width: 1280px;
    margin: 0 auto;
  }
}
```

---

## Best Practices

### 1. **Data Presentation**

- Always show units with numerical values
- Use consistent decimal places (e.g., pH: 7.2, not 7.23)
- Include timestamps for all readings
- Show data source/sensor ID when relevant

### 2. **Error Handling**

- Graceful degradation for missing data
- Clear error messages with suggested actions
- Retry mechanisms for failed requests
- Offline state indicators

### 3. **Performance**

- Lazy load non-critical components
- Optimize images and icons
- Use skeleton loading for better perceived performance
- Implement proper caching strategies

### 4. **User Experience**

- Consistent navigation patterns
- Predictable interaction behaviors
- Clear visual hierarchy
- Contextual help and tooltips

---

This style guide should be treated as a living document and updated as the dashboard evolves. All team members should reference this guide when building new features or modifying existing components.
