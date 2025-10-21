# Design Token Implementation Guide

## Quick Start

### 1. Import Design Tokens
Include the design token CSS file in your project:

```html
<link rel="stylesheet" href="design-tokens.css">
```

Or import in your CSS:

```css
@import url('design-tokens.css');
```

### 2. Use CSS Custom Properties
Access design tokens using CSS custom properties:

```css
.my-component {
  color: var(--surface-light);
  background-color: var(--brand-primary);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}
```

### 3. Apply Utility Classes
Use pre-built utility classes for common patterns:

```html
<div class="underwater-card bg-brand-primary text-surface-light">
  <h2 class="text-2xl font-semibold tracking-tight">Water Quality Status</h2>
  <p class="text-base leading-normal">Current readings are within safe parameters</p>
</div>
```

## Color Implementation

### Status Indicators
```css
/* Water quality status indicators */
.status-safe {
  background-color: var(--feedback-success-bg);
  border: 1px solid var(--feedback-success-border);
  color: var(--feedback-success-text);
}

.status-warning {
  background-color: var(--feedback-warning-bg);
  border: 1px solid var(--feedback-warning-border);
  color: var(--feedback-warning-text);
}

.status-critical {
  background-color: var(--feedback-error-bg);
  border: 1px solid var(--feedback-error-border);
  color: var(--feedback-error-text);
}
```

### Brand Colors
```css
/* Primary brand button */
.btn-primary {
  background-color: var(--brand-primary);
  color: var(--surface-light);
  border: 1px solid var(--brand-secondary);
}

.btn-primary:hover {
  background-color: var(--brand-secondary);
  box-shadow: var(--shadow-aqua-md);
}

/* Secondary brand button */
.btn-secondary {
  background-color: transparent;
  color: var(--brand-secondary);
  border: 1px solid var(--brand-secondary);
}

.btn-secondary:hover {
  background-color: var(--brand-secondary);
  color: var(--deep-black);
}
```

### Underwater Theme Colors
```css
/* Underwater card with depth effect */
.underwater-panel {
  background: linear-gradient(135deg, 
    var(--deep-dark) 0%, 
    var(--deep-main) 50%, 
    var(--mid-dark) 100%
  );
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-aqua-lg);
}

/* Bioluminescent accent */
.glow-accent {
  color: var(--glow-cyan);
  text-shadow: 0 0 10px var(--glow-cyan);
}
```

## Typography Implementation

### Responsive Headings
```css
/* Hero heading that scales across devices */
.hero-title {
  font-family: var(--font-secondary);
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
  color: var(--surface-light);
}

/* Section heading */
.section-title {
  font-family: var(--font-secondary);
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  letter-spacing: var(--tracking-tight);
  color: var(--surface-accent);
  margin-bottom: var(--space-6);
}

/* Body text */
.body-text {
  font-family: var(--font-primary);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--neutral-200);
}
```

### Data Display Typography
```css
/* Large data values */
.data-value {
  font-family: var(--font-primary);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-none);
  color: var(--surface-accent);
}

/* Data labels */
.data-label {
  font-family: var(--font-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--neutral-400);
}

/* Code/technical data */
.code-text {
  font-family: var(--font-monospace);
  font-size: var(--text-sm);
  background-color: var(--neutral-800);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  color: var(--glow-cyan);
}
```

## Spacing Implementation

### Layout Spacing
```css
/* Page container */
.page-container {
  padding: var(--container-padding-mobile);
  max-width: 1200px;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .page-container {
    padding: var(--container-padding-tablet);
  }
}

@media (min-width: 1024px) {
  .page-container {
    padding: var(--container-padding-desktop);
  }
}

/* Section spacing */
.section {
  margin-bottom: var(--space-16);
}

.section--large {
  margin-bottom: var(--space-24);
}

/* Grid layouts */
.grid {
  display: grid;
  gap: var(--space-6);
}

.grid--tight {
  gap: var(--space-4);
}

.grid--loose {
  gap: var(--space-8);
}
```

### Component Spacing
```css
/* Card component */
.card {
  padding: var(--space-6);
  margin-bottom: var(--space-4);
  border-radius: var(--radius-lg);
}

.card--compact {
  padding: var(--space-4);
}

.card--spacious {
  padding: var(--space-8);
}

/* Form elements */
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  margin-bottom: var(--space-2);
  display: block;
}

.form-input {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
}

/* Button spacing */
.btn {
  padding: var(--space-3) var(--space-6);
  margin-right: var(--space-2);
}

.btn--small {
  padding: var(--space-2) var(--space-4);
}

.btn--large {
  padding: var(--space-4) var(--space-8);
}
```

## Animation Implementation

### Hover Interactions
```css
/* Standard hover transition */
.interactive {
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-aqua-md);
}

/* Button press animation */
.btn {
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.btn:active {
  transform: translateY(0);
  transition-duration: var(--interaction-press-duration);
  transition-timing-function: var(--interaction-press-easing);
}
```

### Underwater Animations
```css
/* Ripple effect on click */
@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

.ripple-effect {
  position: relative;
  overflow: hidden;
}

.ripple-effect::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: var(--glow-cyan);
  transform: scale(0);
  animation: ripple var(--underwater-ripple-duration) var(--underwater-ripple-easing);
  pointer-events: none;
}

/* Wave background animation */
@keyframes wave {
  0%, 100% {
    transform: translateX(-50%) translateY(0);
  }
  50% {
    transform: translateX(-50%) translateY(-10px);
  }
}

.wave-background {
  position: relative;
}

.wave-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  width: 120%;
  height: 100%;
  background: linear-gradient(90deg, transparent, var(--glow-cyan), transparent);
  opacity: 0.1;
  animation: wave var(--underwater-wave-duration) var(--underwater-wave-easing) infinite;
}

/* Bubble floating animation */
@keyframes bubble {
  0% {
    transform: translateY(100px) scale(0);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) scale(1);
    opacity: 0;
  }
}

.bubble-effect {
  position: relative;
}

.bubble-effect::after {
  content: '';
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--glow-teal);
  border-radius: 50%;
  animation: bubble var(--underwater-bubble-duration) var(--underwater-bubble-easing) infinite;
}

/* Glow pulse animation */
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 5px var(--glow-cyan);
  }
  50% {
    box-shadow: 0 0 20px var(--glow-cyan), 0 0 30px var(--glow-cyan);
  }
}

.glow-pulse {
  animation: glow var(--underwater-glow-duration) var(--underwater-glow-easing) infinite;
}
```

### Loading Animations
```css
/* Spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--neutral-600);
  border-top: 2px solid var(--brand-secondary);
  border-radius: 50%;
  animation: spin var(--loading-spinner-duration) var(--loading-spinner-easing) infinite;
}

/* Pulse loading */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.loading-pulse {
  animation: pulse var(--loading-pulse-duration) var(--loading-pulse-easing) infinite;
}

/* Skeleton loading */
@keyframes skeleton {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, var(--neutral-800) 25%, var(--neutral-700) 50%, var(--neutral-800) 75%);
  background-size: 200px 100%;
  animation: skeleton var(--loading-skeleton-duration) var(--loading-skeleton-easing) infinite;
}
```

## Component Examples

### Water Quality Dashboard Card
```css
.quality-card {
  background: var(--bg-underwater-card);
  backdrop-filter: var(--backdrop-blur-md);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-aqua-sm);
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.quality-card:hover {
  border-color: var(--border-secondary);
  box-shadow: var(--shadow-aqua-md);
  transform: translateY(-2px);
}

.quality-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.quality-card__title {
  font-family: var(--font-secondary);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--surface-light);
}

.quality-card__status {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.quality-card__value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--surface-accent);
  line-height: var(--leading-none);
  margin-bottom: var(--space-2);
}

.quality-card__unit {
  font-size: var(--text-sm);
  color: var(--neutral-400);
  margin-left: var(--space-1);
}

.quality-card__trend {
  display: flex;
  align-items: center;
  font-size: var(--text-sm);
  color: var(--neutral-300);
}
```

### Navigation Component
```css
.nav {
  background: var(--bg-underwater-nav);
  backdrop-filter: var(--backdrop-blur-md);
  border-bottom: 1px solid var(--border-primary);
  padding: var(--space-4) 0;
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.nav__container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--container-padding-mobile);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav__logo {
  font-family: var(--font-secondary);
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--surface-accent);
  text-decoration: none;
}

.nav__menu {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: var(--space-6);
}

.nav__link {
  color: var(--neutral-300);
  text-decoration: none;
  font-weight: var(--font-medium);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  transition: all var(--interaction-hover-duration) var(--interaction-hover-easing);
}

.nav__link:hover {
  color: var(--surface-accent);
  background-color: var(--bg-hover);
}

.nav__link--active {
  color: var(--surface-accent);
  background-color: var(--bg-active);
}

@media (min-width: 768px) {
  .nav__container {
    padding: 0 var(--container-padding-tablet);
  }
}

@media (min-width: 1024px) {
  .nav__container {
    padding: 0 var(--container-padding-desktop);
  }
}
```

### Form Components
```css
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--surface-light);
  margin-bottom: var(--space-2);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-underwater-card);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  color: var(--surface-light);
  font-size: var(--text-base);
  transition: all var(--interaction-focus-duration) var(--interaction-focus-easing);
}

.form-input:focus {
  outline: none;
  border-color: var(--brand-secondary);
  box-shadow: var(--focus-ring-shadow);
  background: var(--bg-focus);
}

.form-input::placeholder {
  color: var(--neutral-400);
}

.form-error {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--feedback-error-text);
}

.form-help {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--neutral-400);
}
```

## Best Practices

### 1. Consistent Token Usage
- Always use design tokens instead of hardcoded values
- Use semantic tokens (e.g., `--brand-primary`) over literal tokens (e.g., `--mid-main`)
- Maintain consistency across similar components

### 2. Responsive Design
- Leverage responsive typography scaling
- Use appropriate spacing for different screen sizes
- Ensure touch targets meet minimum size requirements

### 3. Accessibility
- Maintain proper color contrast ratios
- Respect user motion preferences
- Provide focus indicators for interactive elements

### 4. Performance
- Use CSS custom properties for dynamic theming
- Minimize animation complexity on lower-end devices
- Optimize backdrop filters and shadows for performance

### 5. Maintenance
- Document custom token usage
- Test changes across all breakpoints
- Validate accessibility after modifications

This implementation guide provides practical examples and patterns for using the AquaChain design token system effectively in your components and layouts.