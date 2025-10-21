# AquaChain UI Style Guide Implementation Guide

## Overview

This implementation guide provides developers with practical instructions for implementing the AquaChain UI Style Guide in their projects. It covers setup, usage patterns, best practices, and migration strategies.

## Quick Start

### 1. Include Design Tokens

Add the design tokens CSS file to your project:

```html
<!-- In your HTML head -->
<link rel="stylesheet" href="path/to/design-tokens.css">
```

Or import in your CSS:

```css
@import url('path/to/design-tokens.css');
```

### 2. Set Base Styles

Apply base styles to your application:

```css
/* Base application styles */
body {
  font-family: var(--font-primary);
  background: var(--gradient-bg-primary);
  color: var(--neutral-100);
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

/* Ensure box-sizing is consistent */
*, *::before, *::after {
  box-sizing: border-box;
}
```

### 3. Use Component Classes

Start using the predefined component classes:

```html
<!-- Primary button -->
<button class="btn btn-primary">Get Started</button>

<!-- Card component -->
<div class="card">
  <h3 class="card-title">Water Quality Status</h3>
  <div class="card-content">
    <p>Current water quality is within safe parameters.</p>
  </div>
</div>
```

## Component Implementation

### Buttons

#### Basic Button Structure
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-primary);
  font-weight: var(--font-semibold);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  text-decoration: none;
  position: relative;
  overflow: hidden;
}
```

#### Button Variants
```css
/* Primary button */
.btn-primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow-aqua-sm);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-aqua-md);
}

/* Secondary button */
.btn-secondary {
  background: transparent;
  color: var(--surface-accent);
  border: 2px solid var(--surface-accent);
}

.btn-secondary:hover {
  background: var(--bg-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-aqua-sm);
}

/* Disabled state */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}
```

#### Button Sizes
```css
.btn-sm {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
}

.btn-lg {
  padding: var(--space-4) var(--space-8);
  font-size: var(--text-lg);
}
```

#### Usage Examples
```html
<!-- Different button types -->
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
<button class="btn btn-primary" disabled>Disabled</button>

<!-- Different sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Medium</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- With icons -->
<button class="btn btn-primary">
  <svg width="16" height="16"><!-- icon --></svg>
  Save Changes
</button>
```

### Form Elements

#### Input Fields
```css
.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: rgba(15, 23, 42, 0.6);
  border: 2px solid var(--border-primary);
  border-radius: var(--radius-lg);
  color: var(--neutral-100);
  font-size: var(--text-base);
  font-family: var(--font-primary);
  transition: all var(--duration-normal) var(--ease-out);
}

.form-input::placeholder {
  color: var(--neutral-500);
}

.form-input:focus {
  outline: none;
  border-color: var(--surface-accent);
  background: rgba(15, 23, 42, 0.8);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
}

.form-input:invalid {
  border-color: var(--status-critical);
}
```

#### Form Groups
```css
.form-group {
  margin-bottom: var(--space-6);
}

.form-label {
  display: block;
  margin-bottom: var(--space-2);
  color: var(--neutral-300);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
}

.form-help {
  margin-top: var(--space-1);
  color: var(--neutral-500);
  font-size: var(--text-xs);
}

.form-error {
  margin-top: var(--space-1);
  color: var(--status-critical);
  font-size: var(--text-xs);
}
```

#### Usage Examples
```html
<div class="form-group">
  <label class="form-label" for="email">Email Address</label>
  <input type="email" id="email" class="form-input" placeholder="Enter your email">
  <div class="form-help">We'll never share your email with anyone else.</div>
</div>

<div class="form-group">
  <label class="form-label" for="password">Password</label>
  <input type="password" id="password" class="form-input" placeholder="Enter your password">
  <div class="form-error">Password must be at least 8 characters long.</div>
</div>
```

### Cards

#### Basic Card Structure
```css
.card {
  background: var(--bg-underwater-card);
  backdrop-filter: var(--backdrop-blur-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-2xl);
  padding: var(--card-padding);
  transition: all var(--duration-normal) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-aqua-lg);
  border-color: var(--border-secondary);
}
```

#### Card Components
```css
.card-header {
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-primary);
}

.card-title {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--neutral-100);
}

.card-subtitle {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--neutral-400);
}

.card-content {
  color: var(--neutral-300);
  line-height: var(--leading-relaxed);
}

.card-footer {
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

#### Usage Examples
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Water Quality Monitor</h3>
    <p class="card-subtitle">Sensor ID: WQ-001</p>
  </div>
  <div class="card-content">
    <p>Current water quality parameters are within normal ranges.</p>
  </div>
  <div class="card-footer">
    <span class="status-badge status-safe">Operational</span>
    <button class="btn btn-secondary btn-sm">View Details</button>
  </div>
</div>
```

### Navigation

#### Top Navigation
```css
.top-navigation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-sticky);
  height: var(--nav-height);
  background: var(--bg-underwater-nav);
  backdrop-filter: var(--backdrop-blur-md);
  border-bottom: 1px solid var(--border-primary);
  padding: 0 var(--space-4);
}

.nav-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
}
```

#### Navigation Links
```css
.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: var(--neutral-300);
  font-weight: var(--font-medium);
  transition: all var(--duration-normal) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.nav-link:hover {
  color: var(--surface-accent);
  background: var(--bg-hover);
  transform: translateY(-1px);
}

.nav-link.active {
  color: var(--surface-accent);
  background: var(--bg-active);
  box-shadow: 0 0 10px rgba(8, 131, 149, 0.3);
}
```

### Loading States

#### Aqua Spinner
```css
.aqua-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-ripple {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(8, 131, 149, 0.6);
  border-radius: 50%;
  animation: ripple-animation 2s infinite ease-out;
}

.spinner-ripple:nth-child(2) { animation-delay: 0.5s; }
.spinner-ripple:nth-child(3) { animation-delay: 1s; }

.spinner-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 25%;
  height: 25%;
  background: var(--gradient-primary);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: pulse-animation 2s infinite ease-in-out;
  box-shadow: 0 0 10px rgba(8, 131, 149, 0.5);
}
```

#### Usage Examples
```html
<!-- Loading spinner -->
<div class="aqua-spinner">
  <div class="spinner-ripple"></div>
  <div class="spinner-ripple"></div>
  <div class="spinner-ripple"></div>
  <div class="spinner-center"></div>
</div>

<!-- Loading state for buttons -->
<button class="btn btn-primary" disabled>
  <div class="aqua-spinner" style="width: 16px; height: 16px;">
    <div class="spinner-center"></div>
  </div>
  Loading...
</button>
```

## Responsive Implementation

### Mobile-First Approach

Always start with mobile styles and enhance for larger screens:

```css
/* Mobile first (default) */
.component {
  padding: var(--space-4);
  font-size: var(--text-base);
}

/* Tablet and up */
@media (min-width: 768px) {
  .component {
    padding: var(--space-6);
    font-size: var(--text-lg);
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .component {
    padding: var(--space-8);
  }
}
```

### Touch-Friendly Interactions

Ensure interactive elements meet minimum touch target sizes:

```css
.touch-target {
  min-height: var(--touch-target-min);
  min-width: var(--touch-target-min);
}

@media (max-width: 768px) {
  .touch-target {
    min-height: var(--touch-target-mobile);
    min-width: var(--touch-target-mobile);
  }
}
```

### Responsive Grid System

Use CSS Grid for responsive layouts:

```css
.grid {
  display: grid;
  gap: var(--grid-gap-md);
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--grid-gap-lg);
  }
}
```

## Accessibility Implementation

### Focus Management

Implement proper focus states for all interactive elements:

```css
.focusable:focus {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  box-shadow: var(--focus-ring-shadow);
}

/* Remove default focus styles */
.focusable:focus {
  outline: none;
}

/* Custom focus ring */
.focusable:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  box-shadow: var(--focus-ring-shadow);
}
```

### Screen Reader Support

Include screen reader only text where needed:

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

### ARIA Implementation

Use proper ARIA attributes:

```html
<!-- Button with loading state -->
<button class="btn btn-primary" aria-describedby="loading-text">
  <span class="sr-only" id="loading-text">Loading, please wait</span>
  <div class="aqua-spinner" aria-hidden="true"></div>
  Save
</button>

<!-- Status indicators -->
<div class="status-badge status-safe" role="status" aria-live="polite">
  <span class="sr-only">Status:</span>
  Safe
</div>
```

## Animation Implementation

### Underwater Effects

#### Ripple Effect
```css
.ripple-container {
  position: relative;
  overflow: hidden;
}

.ripple-effect {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(6, 182, 212, 0.8);
  border-radius: 50%;
  pointer-events: none;
  animation: ripple-expand var(--duration-slower) var(--ease-out) forwards;
  transform: translate(-50%, -50%);
}

@keyframes ripple-expand {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(8);
    opacity: 0;
  }
}
```

#### Wave Animation
```css
.wave-element {
  animation: wave-flow 3s var(--ease-in-out) infinite;
}

@keyframes wave-flow {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}
```

### Performance Considerations

Use `transform` and `opacity` for animations:

```css
/* Good - GPU accelerated */
.animated-element {
  transform: translateY(0);
  opacity: 1;
  transition: transform var(--duration-normal), opacity var(--duration-normal);
}

.animated-element:hover {
  transform: translateY(-2px);
}

/* Avoid - CPU intensive */
.animated-element:hover {
  top: -2px; /* Don't do this */
}
```

Use `will-change` for elements that will be animated:

```css
.will-animate {
  will-change: transform, opacity;
}

/* Remove after animation */
.animation-complete {
  will-change: auto;
}
```

## JavaScript Integration

### Ripple Effect Implementation

```javascript
function createRipple(event) {
  const button = event.currentTarget;
  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;
  
  const ripple = document.createElement('div');
  ripple.className = 'ripple-effect';
  ripple.style.width = ripple.style.height = size + 'px';
  ripple.style.left = x + 'px';
  ripple.style.top = y + 'px';
  
  button.appendChild(ripple);
  
  // Remove ripple after animation
  setTimeout(() => {
    ripple.remove();
  }, 800);
}

// Add to buttons
document.querySelectorAll('.btn').forEach(button => {
  button.addEventListener('click', createRipple);
});
```

### Loading State Management

```javascript
function setLoadingState(button, isLoading) {
  if (isLoading) {
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    
    const spinner = document.createElement('div');
    spinner.className = 'aqua-spinner';
    spinner.style.width = '16px';
    spinner.style.height = '16px';
    spinner.innerHTML = '<div class="spinner-center"></div>';
    
    button.insertBefore(spinner, button.firstChild);
  } else {
    button.disabled = false;
    button.removeAttribute('aria-busy');
    
    const spinner = button.querySelector('.aqua-spinner');
    if (spinner) {
      spinner.remove();
    }
  }
}
```

### Theme Switching

```javascript
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('aquachain-theme', theme);
}

function getTheme() {
  return localStorage.getItem('aquachain-theme') || 'default';
}

// Initialize theme
document.documentElement.setAttribute('data-theme', getTheme());
```

## Testing Guidelines

### Visual Regression Testing

Test components across different states:

```javascript
// Example with Playwright
test('button states', async ({ page }) => {
  await page.goto('/style-guide');
  
  // Test default state
  await expect(page.locator('.btn-primary')).toHaveScreenshot('button-default.png');
  
  // Test hover state
  await page.locator('.btn-primary').hover();
  await expect(page.locator('.btn-primary')).toHaveScreenshot('button-hover.png');
  
  // Test focus state
  await page.locator('.btn-primary').focus();
  await expect(page.locator('.btn-primary')).toHaveScreenshot('button-focus.png');
});
```

### Accessibility Testing

```javascript
// Example with axe-core
import { injectAxe, checkA11y } from 'axe-playwright';

test('accessibility compliance', async ({ page }) => {
  await page.goto('/style-guide');
  await injectAxe(page);
  await checkA11y(page);
});
```

### Responsive Testing

```javascript
test('responsive behavior', async ({ page }) => {
  // Mobile
  await page.setViewportSize({ width: 375, height: 667 });
  await expect(page.locator('.nav-mobile')).toBeVisible();
  
  // Desktop
  await page.setViewportSize({ width: 1024, height: 768 });
  await expect(page.locator('.nav-desktop')).toBeVisible();
});
```

## Migration Guide

### From Existing Styles

1. **Audit Current Styles**: Identify existing components and their styles
2. **Map to Design Tokens**: Replace hardcoded values with design tokens
3. **Update Component Structure**: Align with new component patterns
4. **Test Thoroughly**: Ensure visual and functional consistency

### Example Migration

Before:
```css
.old-button {
  background: #0891b2;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
}
```

After:
```css
.btn-primary {
  background: var(--gradient-primary);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  box-shadow: var(--shadow-aqua-sm);
  transition: all var(--duration-normal) var(--ease-out);
}
```

## Performance Optimization

### CSS Optimization

1. **Use CSS Custom Properties**: Leverage design tokens for consistency
2. **Minimize Repaints**: Use `transform` and `opacity` for animations
3. **Optimize Selectors**: Keep specificity low and selectors simple
4. **Bundle Efficiently**: Only include used components

### Animation Performance

```css
/* Optimize animations */
.optimized-animation {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force hardware acceleration */
  backface-visibility: hidden;
}

/* Clean up after animation */
.animation-complete {
  will-change: auto;
}
```

## Troubleshooting

### Common Issues

1. **Colors Not Applying**: Ensure design tokens CSS is loaded first
2. **Animations Not Working**: Check for `prefers-reduced-motion` settings
3. **Focus States Missing**: Verify focus-visible support and fallbacks
4. **Mobile Touch Issues**: Ensure minimum touch target sizes

### Debug Tools

```css
/* Debug layout issues */
.debug * {
  outline: 1px solid red;
}

/* Debug focus issues */
.debug *:focus {
  outline: 3px solid yellow !important;
}
```

## Support and Resources

### Documentation
- [Complete Style Guide](./ui-style-guide.md)
- [Design Tokens Reference](./design-tokens.json)
- [Component Examples](./component-examples.html)

### Tools
- [Design Tokens CSS](./design-tokens.css)
- Browser DevTools for debugging
- Accessibility testing tools (axe, WAVE)

### Community
- Report issues and suggestions
- Contribute improvements
- Share implementation examples

This implementation guide provides the foundation for successfully implementing the AquaChain UI Style Guide in your projects while maintaining consistency, accessibility, and performance.